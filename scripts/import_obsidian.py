#!/usr/bin/env python3
"""
Obsidian Vault 预处理脚本（零 token）。

扫描 Obsidian vault 目录，提取元数据、构建链接图、分类笔记、聚类领域候选，
输出 vault_analysis.json 供 /cold-start-obsidian skill 使用。

用法：
    python3 scripts/import_obsidian.py /path/to/obsidian/vault
    python3 scripts/import_obsidian.py /path/to/vault --output custom_output.json
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "inbox" / "obsidian_analysis" / "vault_analysis.json"

# 扫描时跳过的目录
SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules", ".stversions"}

# 笔记分类关键词
MOC_KEYWORDS = {"moc", "index", "目录", "总览", "概览", "map of content", "homepage"}
LITERATURE_TAGS = {"book", "reading", "文献", "读书", "书", "阅读", "论文", "paper", "article"}
LITERATURE_FOLDERS = {"reading", "书", "读书", "书籍", "文献", "books", "literature"}

# 枢纽笔记阈值
HUB_MIN_IN_DEGREE = 3
HUB_MAX_COUNT = 30


# ── 轻量 Frontmatter 解析 ──────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """
    解析 YAML frontmatter（--- 分隔）。
    仅处理简单 key: value 和 key: [list] 格式，不引入 pyyaml。
    """
    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    yaml_block = content[3:end].strip()
    result = {}

    for line in yaml_block.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # key: value
        m = re.match(r'^(\w[\w\s-]*?):\s*(.*)$', line)
        if not m:
            continue

        key = m.group(1).strip()
        val = m.group(2).strip()

        # 内联列表: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            result[key] = items
        # 布尔/数字
        elif val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
        # 带引号的字符串
        elif (val.startswith('"') and val.endswith('"')) or \
             (val.startswith("'") and val.endswith("'")):
            result[key] = val[1:-1]
        # 普通字符串
        elif val:
            result[key] = val
        else:
            # 可能是多行列表的开头，简化处理：跳过
            result[key] = None

    # 处理 YAML 列表格式 (- item)
    current_key = None
    list_items = []
    for line in yaml_block.split("\n"):
        stripped = line.strip()
        m = re.match(r'^(\w[\w\s-]*?):\s*$', stripped)
        if m:
            # 保存前一个列表
            if current_key and list_items:
                result[current_key] = list_items
            current_key = m.group(1).strip()
            list_items = []
            continue

        if current_key and stripped.startswith("- "):
            item = stripped[2:].strip().strip("'\"")
            list_items.append(item)

    # 保存最后一个列表
    if current_key and list_items:
        result[current_key] = list_items

    return result


# ── 内容解析 ──────────────────────────────────────────

def extract_wikilinks(content: str) -> list[str]:
    """提取所有 [[target]] 和 [[target|alias]] 中的 target。"""
    # 排除 frontmatter 区域
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            body = content[end + 4:]

    links = re.findall(r'\[\[([^\]|]+?)(?:\|[^\]]*?)?\]\]', body)
    # 去重保序
    seen = set()
    unique = []
    for link in links:
        link = link.strip()
        if link and link not in seen:
            seen.add(link)
            unique.append(link)
    return unique


def extract_inline_tags(content: str) -> list[str]:
    """提取行内 #tag（排除标题 # 和代码块）。"""
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            body = content[end + 4:]

    # 移除代码块
    body = re.sub(r'```[\s\S]*?```', '', body)
    body = re.sub(r'`[^`]+`', '', body)

    tags = re.findall(r'(?:^|\s)#([a-zA-Z\u4e00-\u9fff][\w/\u4e00-\u9fff-]*)', body)
    return list(set(tags))


def extract_headings(content: str) -> list[dict]:
    """提取 H1-H3 标题。"""
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            body = content[end + 4:]

    headings = []
    for m in re.finditer(r'^(#{1,3})\s+(.+)$', body, re.MULTILINE):
        headings.append({
            "level": len(m.group(1)),
            "text": m.group(2).strip()
        })
    return headings


def count_words(content: str) -> int:
    """
    统计字数：中文按字符计，英文按空格分词计。
    去除 frontmatter 和 markdown 语法。
    """
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            body = content[end + 4:]

    # 去除代码块、链接语法、图片等
    body = re.sub(r'```[\s\S]*?```', '', body)
    body = re.sub(r'!\[\[.*?\]\]', '', body)
    body = re.sub(r'\[\[([^\]|]*?)(?:\|([^\]]*?))?\]\]', r'\2' if r'\2' else r'\1', body)
    body = re.sub(r'[#*_`~>|=-]', '', body)

    # 中文字符数
    chinese = len(re.findall(r'[\u4e00-\u9fff]', body))
    # 英文词数
    english_text = re.sub(r'[\u4e00-\u9fff]', ' ', body)
    english = len([w for w in english_text.split() if w.strip()])

    return chinese + english


# ── 笔记分类 ──────────────────────────────────────────

def classify_note(note: dict, avg_word_count: float) -> str:
    """
    根据启发式规则分类笔记。
    返回: moc / evergreen / literature / fleeting / regular
    """
    filename_lower = note["filename"].lower()
    tags_lower = {t.lower() for t in note["tags"]}
    folder_lower = note["folder"].lower() if note["folder"] else ""

    # MOC: 文件名含关键词，或出链多
    if any(kw in filename_lower for kw in MOC_KEYWORDS):
        return "moc"
    if note["out_degree"] > 10 and note["word_count"] < avg_word_count * 2:
        return "moc"

    # Literature: 标签或文件夹匹配
    if tags_lower & LITERATURE_TAGS:
        return "literature"
    first_folder = folder_lower.split("/")[0] if folder_lower else ""
    if first_folder in LITERATURE_FOLDERS:
        return "literature"

    # Fleeting: 短且无链接
    if note["word_count"] < 100 and note["in_degree"] == 0 and note["out_degree"] == 0:
        return "fleeting"
    if note["word_count"] < 50:
        return "fleeting"

    # Evergreen: 有 frontmatter、字数够、有入链
    if note["has_frontmatter"] and note["word_count"] > 200 and note["in_degree"] >= 2:
        return "evergreen"

    # 有一定质量但不满足 evergreen 的严格条件
    if note["word_count"] > 300 and note["in_degree"] >= 1:
        return "evergreen"

    return "regular"


# ── 领域聚类 ──────────────────────────────────────────

def cluster_domains(notes: list[dict]) -> list[dict]:
    """
    从标签和文件夹聚类领域候选。
    """
    # 统计标签频次
    tag_counter = Counter()
    tag_notes = defaultdict(list)
    for note in notes:
        for tag in note["tags"]:
            tag_lower = tag.lower()
            tag_counter[tag_lower] += 1
            tag_notes[tag_lower].append(note["filename"])

    # 统计一级文件夹
    folder_counter = Counter()
    folder_notes = defaultdict(list)
    for note in notes:
        if note["folder"]:
            first_folder = note["folder"].split("/")[0]
            if first_folder:
                folder_counter[first_folder] += 1
                folder_notes[first_folder].append(note["filename"])

    # 合并候选：取出现 >= 3 次的标签和 >= 3 个文件的文件夹
    candidates = []
    seen_names = set()

    # 优先用文件夹（用户主动组织的结构）
    for folder, count in folder_counter.most_common():
        if count < 3:
            continue
        name = folder.strip()
        if name.lower() in seen_names or name.lower() in SKIP_DIRS:
            continue
        seen_names.add(name.lower())

        # 找该文件夹下笔记的常见标签
        folder_note_set = set(folder_notes[folder])
        common_tags = []
        for tag, _ in tag_counter.most_common():
            overlap = len(set(tag_notes[tag]) & folder_note_set)
            if overlap >= 2:
                common_tags.append(tag)
            if len(common_tags) >= 5:
                break

        # 取入链最高的代表笔记
        relevant = [n for n in notes if n["folder"] and n["folder"].split("/")[0] == folder]
        relevant.sort(key=lambda n: n["in_degree"], reverse=True)
        reps = [n["filename"] for n in relevant[:5]]

        candidates.append({
            "name": name,
            "source": f"folder:{folder}",
            "note_count": count,
            "common_tags": common_tags,
            "representative_notes": reps,
            "confidence": "high" if count >= 10 else "medium"
        })

    # 补充：高频标签中未被文件夹覆盖的
    for tag, count in tag_counter.most_common():
        if count < 5:
            continue
        if tag.lower() in seen_names:
            continue
        # 检查是否与已有候选高度重叠
        tag_note_set = set(tag_notes[tag])
        overlaps = False
        for c in candidates:
            c_notes = set(c["representative_notes"])
            if len(tag_note_set & c_notes) > len(tag_note_set) * 0.5:
                overlaps = True
                break
        if overlaps:
            continue

        seen_names.add(tag.lower())
        relevant = [n for n in notes if tag in [t.lower() for t in n["tags"]]]
        relevant.sort(key=lambda n: n["in_degree"], reverse=True)
        reps = [n["filename"] for n in relevant[:5]]

        candidates.append({
            "name": tag,
            "source": f"tag:{tag}",
            "note_count": count,
            "common_tags": [tag],
            "representative_notes": reps,
            "confidence": "medium" if count >= 10 else "low"
        })

    # 按笔记数排序
    candidates.sort(key=lambda c: c["note_count"], reverse=True)

    # 加 id
    for i, c in enumerate(candidates):
        c["candidate_id"] = f"dc_{i+1:03d}"

    return candidates


# ── 主流程 ──────────────────────────────────────────

def scan_vault(vault_path: Path) -> dict:
    """扫描 vault，返回完整分析结果。"""

    # 1. 遍历所有 .md 文件
    md_files = []
    for root, dirs, files in os.walk(vault_path):
        # 跳过特殊目录
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                full_path = Path(root) / f
                rel_path = full_path.relative_to(vault_path)
                md_files.append((full_path, str(rel_path)))

    print(f"Found {len(md_files)} markdown files", file=sys.stderr)

    # 2. 提取每个文件的元数据
    raw_notes = []
    filename_to_idx = {}  # filename -> index（用于链接图）

    for full_path, rel_path in md_files:
        try:
            content = full_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        filename = full_path.stem  # 不含扩展名
        folder = str(Path(rel_path).parent)
        if folder == ".":
            folder = ""

        frontmatter = parse_frontmatter(content)
        fm_tags = frontmatter.get("tags", [])
        if isinstance(fm_tags, str):
            fm_tags = [fm_tags]
        if not isinstance(fm_tags, list):
            fm_tags = []

        inline_tags = extract_inline_tags(content)
        all_tags = list(set(fm_tags + inline_tags))

        wikilinks = extract_wikilinks(content)
        word_count = count_words(content)
        headings = extract_headings(content)

        # 时间信息
        stat = full_path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

        created_time = None
        for key in ("date", "created", "created_at", "createdAt"):
            if key in frontmatter and frontmatter[key]:
                val = str(frontmatter[key])
                m = re.match(r'(\d{4}-\d{2}-\d{2})', val)
                if m:
                    created_time = m.group(1)
                    break
        if not created_time:
            created_time = datetime.fromtimestamp(stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime).strftime("%Y-%m-%d")

        idx = len(raw_notes)
        filename_to_idx[filename] = idx

        raw_notes.append({
            "filename": filename,
            "path": rel_path,
            "folder": folder,
            "tags": all_tags,
            "wikilinks": wikilinks,
            "word_count": word_count,
            "has_frontmatter": bool(frontmatter),
            "headings": headings,
            "created_time": created_time,
            "modified_time": modified_time,
            "in_degree": 0,
            "out_degree": len(wikilinks),
        })

    # 3. 构建链接图，计算入链数
    edges = []
    for note in raw_notes:
        for target in note["wikilinks"]:
            if target in filename_to_idx:
                edges.append({"source": note["filename"], "target": target})
                raw_notes[filename_to_idx[target]]["in_degree"] += 1

    print(f"Link graph: {len(edges)} edges", file=sys.stderr)

    # 4. 分类笔记
    avg_wc = sum(n["word_count"] for n in raw_notes) / max(len(raw_notes), 1)
    for note in raw_notes:
        note["category"] = classify_note(note, avg_wc)

    category_counts = Counter(n["category"] for n in raw_notes)
    for cat, cnt in category_counts.most_common():
        print(f"  {cat}: {cnt}", file=sys.stderr)

    # 5. 识别枢纽笔记
    hub_candidates = [n for n in raw_notes if n["in_degree"] >= HUB_MIN_IN_DEGREE]
    hub_candidates.sort(key=lambda n: n["in_degree"], reverse=True)
    hub_notes = [n["filename"] for n in hub_candidates[:HUB_MAX_COUNT]]

    for note in raw_notes:
        note["is_hub"] = note["filename"] in hub_notes

    moc_notes = [n["filename"] for n in raw_notes if n["category"] == "moc"]

    print(f"Hub notes: {len(hub_notes)}, MOC notes: {len(moc_notes)}", file=sys.stderr)

    # 6. 聚类领域
    domain_candidates = cluster_domains(raw_notes)
    print(f"Domain candidates: {len(domain_candidates)}", file=sys.stderr)

    # 7. 清理输出（去掉 headings 减小体积，保留在需要时可加回）
    output_notes = []
    for note in raw_notes:
        output_notes.append({
            "filename": note["filename"],
            "path": note["path"],
            "folder": note["folder"],
            "tags": note["tags"],
            "wikilinks": note["wikilinks"],
            "word_count": note["word_count"],
            "has_frontmatter": note["has_frontmatter"],
            "created_time": note["created_time"],
            "modified_time": note["modified_time"],
            "in_degree": note["in_degree"],
            "out_degree": note["out_degree"],
            "category": note["category"],
            "is_hub": note["is_hub"],
        })

    # 按入链数降序排列
    output_notes.sort(key=lambda n: n["in_degree"], reverse=True)

    # 8. 统计
    stats = {
        "total_files": len(raw_notes),
        "total_wikilinks": len(edges),
        "total_tags": len(set(t for n in raw_notes for t in n["tags"])),
        "avg_word_count": round(avg_wc),
        "files_with_frontmatter": sum(1 for n in raw_notes if n["has_frontmatter"]),
        "categories": dict(category_counts.most_common()),
    }

    # 9. 组装输出
    result = {
        "vault_path": str(vault_path.resolve()),
        "scan_time": datetime.now().isoformat(),
        "stats": stats,
        "domain_candidates": domain_candidates,
        "hub_notes": hub_notes,
        "moc_notes": moc_notes,
        "notes": output_notes,
        "link_graph": {
            "edge_count": len(edges),
            "edges": edges,
        },
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/import_obsidian.py /path/to/vault [--output path]",
              file=sys.stderr)
        sys.exit(1)

    vault_path = Path(sys.argv[1]).resolve()

    # 解析 --output 参数
    output_path = DEFAULT_OUTPUT
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])

    # 验证 vault 路径
    if not vault_path.is_dir():
        print(f"Error: {vault_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    obsidian_dir = vault_path / ".obsidian"
    if not obsidian_dir.is_dir():
        print(f"Warning: {vault_path} does not contain .obsidian/ — "
              "proceeding anyway (may not be an Obsidian vault)", file=sys.stderr)

    # 扫描
    print(f"\nScanning vault: {vault_path}", file=sys.stderr)
    result = scan_vault(vault_path)

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Analysis saved to: {output_path}", file=sys.stderr)
    print(f"  {result['stats']['total_files']} files, "
          f"{result['stats']['total_wikilinks']} links, "
          f"{len(result['domain_candidates'])} domain candidates, "
          f"{len(result['hub_notes'])} hub notes", file=sys.stderr)


if __name__ == "__main__":
    main()
