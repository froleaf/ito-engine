#!/usr/bin/env python3
"""
从 session_memory 中提取认知轨迹，识别活跃线索，
查询图谱找到线索附近但未触及的节点。
输出 memory/trajectory.json。
"""

import json
import os
import glob
from datetime import datetime, timedelta, timezone
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "memory", "session_memory")
ONTOLOGY_PATH = os.path.join(BASE_DIR, "ontology", "ontology.jsonld")
OUTPUT_PATH = os.path.join(BASE_DIR, "memory", "trajectory.json")

CST = timezone(timedelta(hours=8))
LOOKBACK_DAYS = 14

# 图谱中产生边的属性
EDGE_PROPS = {
    "subBranch", "parentBranch", "belongsTo", "isA",
    "prerequisite", "relatedTo", "contradicts", "appliesTo",
    "exemplifiedBy", "hasMisconception", "confusedWith",
    "hasResource", "coversTopics", "derivedFrom", "inspiredBy",
    "crossDomainLink", "aboutNodes", "aboutDomains", "relatedDeposits",
}


# ── 数据加载 ──────────────────────────────────────────────

def load_sessions(lookback_days=LOOKBACK_DAYS):
    """加载回看窗口内的所有 session 记录。"""
    cutoff = datetime.now(CST) - timedelta(days=lookback_days)
    sessions = []

    for fpath in sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl"))):
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts_str = rec.get("ts", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=CST)
                except (ValueError, TypeError):
                    continue

                if ts >= cutoff:
                    rec["_ts"] = ts
                    sessions.append(rec)

    sessions.sort(key=lambda r: r["_ts"])
    return sessions


def load_graph():
    """加载图谱，返回邻接表和节点元数据。"""
    with open(ONTOLOGY_PATH, "r", encoding="utf-8") as f:
        graph = json.load(f)

    adjacency = defaultdict(set)
    node_meta = {}

    for entity in graph.get("@graph", []):
        eid = entity.get("@id", "")
        if not eid:
            continue

        node_meta[eid] = {
            "name": entity.get("name", eid),
            "type": entity.get("@type", ""),
            "depth": entity.get("depth", ""),
        }

        for prop in EDGE_PROPS:
            val = entity.get(prop)
            if not val:
                continue
            refs = [val] if isinstance(val, str) else val
            for v in refs:
                if isinstance(v, str):
                    adjacency[eid].add(v)
                    adjacency[v].add(eid)

    return adjacency, node_meta


# ── 概念提取 ──────────────────────────────────────────────

def extract_concepts(session):
    """从一条 session 记录中提取涉及的概念 ID。"""
    concepts = set()

    # 领域（兼容两种字段名）
    for key in ("domains_touched", "domains"):
        for d in _as_list(session.get(key)):
            if isinstance(d, str):
                concepts.add(d)

    # Deposit（兼容多种字段名和格式）
    for key in ("deposits_created", "newDeposits", "deepenedDeposits",
                "deposits_updated", "depositsUpdated"):
        for item in _as_list(session.get(key)):
            if isinstance(item, str):
                concepts.add(item.split("(")[0].strip())
            elif isinstance(item, dict) and item.get("node"):
                concepts.add(item["node"])

    # 跨域链接
    for key in ("cross_domain_links", "newCrossDomainLinks"):
        for item in _as_list(session.get(key)):
            if isinstance(item, str):
                # "label: description" 或 纯 id
                concepts.add(item.split(":")[0].strip())

    # 显式触及的节点
    for n in _as_list(session.get("nodes_touched")):
        if isinstance(n, str):
            concepts.add(n)

    # knowledge_extracted 中的结构化节点
    for item in _as_list(session.get("knowledge_extracted")):
        if isinstance(item, dict) and item.get("node"):
            concepts.add(item["node"])

    return concepts


def _as_list(val):
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


# ── 线索识别 ──────────────────────────────────────────────

def get_session_label(session):
    """提取 session 的可读标签。"""
    topic = session.get("topic", "")
    if topic:
        return topic
    summary = session.get("input_summary", session.get("summary", ""))
    if summary:
        # 取第一个句号或逗号前的内容，截断到 40 字
        for sep in ("。", "，", "；", ".", ","):
            if sep in summary[:60]:
                return summary[:summary.index(sep, 0, 60)]
        return summary[:40]
    return ""


def identify_threads(sessions, min_occurrences=3):
    """
    识别活跃认知线索。
    线索 = 在 min_occurrences 个以上 session 中出现的概念簇。
    过于宽泛的领域（出现在 >70% session 中）会被降权。
    """
    concept_sessions = defaultdict(list)
    for i, session in enumerate(sessions):
        for c in extract_concepts(session):
            concept_sessions[c].append(i)

    # 过滤过于宽泛的概念（出现在 >70% session 中的 domain）
    n = len(sessions)
    too_broad = set()
    for c, idx in concept_sessions.items():
        if c.startswith("domain_") and len(idx) > n * 0.7:
            too_broad.add(c)

    # 只保留出现 >= min_occurrences 次且不过于宽泛的概念
    recurring = {c: idx for c, idx in concept_sessions.items()
                 if len(idx) >= min_occurrences and c not in too_broad}

    # 聚类：共享 2+ session 的概念归为同一线索
    threads = []
    used = set()
    sorted_concepts = sorted(recurring.items(), key=lambda x: -len(x[1]))

    for concept, indices in sorted_concepts:
        if concept in used:
            continue

        cluster = {concept}
        for other, other_idx in sorted_concepts:
            if other in used or other == concept:
                continue
            if len(set(indices) & set(other_idx)) >= 2:
                cluster.add(other)

        all_indices = sorted({i for c in cluster for i in recurring.get(c, [])})
        for c in cluster:
            used.add(c)

        first_ts = sessions[all_indices[0]]["_ts"]
        last_ts = sessions[all_indices[-1]]["_ts"]

        # 收集 session 标签
        topics = []
        for idx in all_indices:
            label = get_session_label(sessions[idx])
            if label:
                topics.append(label)

        threads.append({
            "concepts": sorted(cluster),
            "session_count": len(all_indices),
            "date_range": [first_ts.isoformat(), last_ts.isoformat()],
            "span_days": (last_ts - first_ts).days,
            "session_topics": topics,
        })

    # 按最近活跃时间排序
    threads.sort(key=lambda t: t["date_range"][1], reverse=True)
    return threads, too_broad


# ── 邻居探索 ──────────────────────────────────────────────

def find_unexplored(thread_concepts, touched, adjacency, node_meta):
    """找到线索概念的 1-hop 邻居中，最近未触及的节点。"""
    candidates = set()
    for concept in thread_concepts:
        for neighbor in adjacency.get(concept, set()):
            if neighbor not in touched and neighbor in node_meta:
                ntype = node_meta[neighbor].get("type", "")
                if ntype in ("DomainRoot", "BranchScaffold"):
                    continue
                candidates.add(neighbor)

    scored = []
    for c in candidates:
        links = sum(1 for tc in thread_concepts if c in adjacency.get(tc, set()))
        scored.append({
            "node_id": c,
            "name": node_meta[c]["name"],
            "type": node_meta[c]["type"],
            "depth": node_meta[c].get("depth", ""),
            "thread_links": links,
        })

    scored.sort(key=lambda x: -x["thread_links"])
    return scored[:10]


# ── 主流程 ────────────────────────────────────────────────

def build_trajectory():
    sessions = load_sessions()

    if not sessions:
        print("回看窗口内无 session 记录。")
        result = {
            "generated_at": datetime.now(CST).isoformat(),
            "lookback_days": LOOKBACK_DAYS,
            "session_count": 0,
            "threads": [],
        }
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return

    print(f"加载 {len(sessions)} 条 session（最近 {LOOKBACK_DAYS} 天）")

    # 收集最近所有触及过的概念
    all_touched = set()
    for s in sessions:
        all_touched.update(extract_concepts(s))

    threads, pervasive_domains = identify_threads(sessions)
    print(f"识别出 {len(threads)} 条线索")
    if pervasive_domains:
        print(f"贯穿性领域（>70% session）: {', '.join(sorted(pervasive_domains))}")

    adjacency, node_meta = load_graph()

    # 为每条线索查找未探索的邻居
    output_threads = []
    for thread in threads[:5]:
        unexplored = find_unexplored(
            thread["concepts"], all_touched, adjacency, node_meta
        )

        domains = [c for c in thread["concepts"] if c.startswith("domain_")]
        deposits = [c for c in thread["concepts"]
                    if c.startswith("td_") or c.startswith("kd_")]
        nodes = [c for c in thread["concepts"]
                 if not c.startswith("domain_") and not c.startswith("td_")
                 and not c.startswith("kd_")]

        output_threads.append({
            "domains": domains,
            "key_deposits": deposits[:5],
            "key_nodes": nodes[:5],
            "session_count": thread["session_count"],
            "span_days": thread["span_days"],
            "date_range": thread["date_range"],
            "recent_topics": thread["session_topics"][-5:],
            "unexplored_nearby": unexplored[:5],
        })

    result = {
        "generated_at": datetime.now(CST).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "session_count": len(sessions),
        "date_range": [sessions[0]["_ts"].isoformat(), sessions[-1]["_ts"].isoformat()],
        "pervasive_domains": sorted(pervasive_domains),
        "threads": output_threads,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n轨迹已写入 {OUTPUT_PATH}")

    for i, t in enumerate(output_threads):
        domains_str = ", ".join(d.replace("domain_", "") for d in t["domains"][:3])
        print(f"\n线索 {i+1}: [{domains_str}] "
              f"({t['session_count']} sessions, 跨 {t['span_days']} 天)")
        for topic in t["recent_topics"][-3:]:
            print(f"  最近: {topic}")
        if t["unexplored_nearby"]:
            print(f"  附近未触及:")
            for n in t["unexplored_nearby"][:3]:
                depth = n["depth"] or "未标注"
                print(f"    - {n['name']} ({n['type']}, depth: {depth})")


if __name__ == "__main__":
    build_trajectory()
