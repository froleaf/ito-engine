#!/usr/bin/env python3
"""
从 ontology/ontology.jsonld 提取时间线事件，
输出轻量 JSON 供 visualization.html 的时间轴 slider 使用。

可独立运行：python scripts/build_timeline.py  → 输出到 stdout
也可被 build_visualization.py 作为模块导入。
"""

import json
import os
import re
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTOLOGY_PATH = os.path.join(BASE_DIR, "ontology", "ontology.jsonld")


def normalize_date(raw: str) -> str | None:
    """
    将各种日期格式统一为 'YYYY-MM-DD'。
    支持: ISO 8601 datetime, YYYY-MM-DD, YYYY-MM, 含前缀的字符串(如 mergeHistory)。
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()

    # ISO 8601 full datetime: 2026-03-07T00:00:00+08:00
    m = re.match(r"(\d{4}-\d{2}-\d{2})T", raw)
    if m:
        return m.group(1)

    # YYYY-MM-DD
    m = re.match(r"^(\d{4}-\d{2}-\d{2})$", raw)
    if m:
        return m.group(1)

    # YYYY-MM (only year-month, like firstContact: "2025-06")
    m = re.match(r"^(\d{4}-\d{2})$", raw)
    if m:
        return m.group(1) + "-01"  # 补 day=01

    return None


def extract_merge_dates(merge_history: list) -> list[str]:
    """
    从 mergeHistory 数组提取日期。
    格式如: "2026-03-12: 与阿德勒×创投讨论交叉..."
    """
    dates = []
    for entry in merge_history:
        if not isinstance(entry, str):
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", entry)
        if m:
            dates.append(m.group(1))
    return dates


def extract_timeline_events(graph_entries: list) -> list[dict]:
    """
    从 @graph 条目中提取所有可观测的时间事件。

    事件类型:
    - node_created:       节点被创建 (createdAt)
    - first_contact:      首次接触知识节点 (firstContact)
    - last_contact:       最近一次接触 (lastContact)
    - deposit_updated:    沉淀产出更新 (updatedAt)
    - material_started:   开始阅读材料 (startedAt)
    - material_progress:  材料进度更新 (lastProgressUpdate)
    - script_compiled:    思维脚本编译 (compiledAt)
    - deposit_merged:     沉淀合并记录 (mergeHistory)
    """
    events = []

    for entry in graph_entries:
        nid = entry.get("@id")
        ntype = entry.get("@type")
        if not nid or not ntype:
            continue

        name = entry.get("name", "")
        domain = entry.get("belongsTo") or entry.get("parentBranch") or ""
        depth = entry.get("depth", "")

        # 1. node_created (createdAt; ThinkingScript 用 compiledAt 作为诞生时间)
        created_raw = entry.get("createdAt", "") or entry.get("compiledAt", "")
        date = normalize_date(created_raw)
        if date:
            ev = {
                "date": date,
                "event": "node_created",
                "id": nid,
                "type": ntype,
                "name": name,
            }
            if depth:
                ev["depth"] = depth
            events.append(ev)

        # 2. first_contact (KnowledgeNode)
        date = normalize_date(entry.get("firstContact", ""))
        if date:
            events.append({
                "date": date,
                "event": "first_contact",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 3. last_contact (KnowledgeNode) — 只在与 firstContact 不同时记录
        lc_date = normalize_date(entry.get("lastContact", ""))
        fc_date = normalize_date(entry.get("firstContact", ""))
        if lc_date and lc_date != fc_date:
            events.append({
                "date": lc_date,
                "event": "last_contact",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 4. deposit_updated (updatedAt ≠ createdAt 时有意义)
        upd_date = normalize_date(entry.get("updatedAt", ""))
        crt_date = normalize_date(entry.get("createdAt", ""))
        if upd_date and upd_date != crt_date:
            events.append({
                "date": upd_date,
                "event": "deposit_updated",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 5. material_started (startedAt)
        date = normalize_date(entry.get("startedAt", ""))
        if date:
            events.append({
                "date": date,
                "event": "material_started",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 6. material_progress (lastProgressUpdate)
        date = normalize_date(entry.get("lastProgressUpdate", ""))
        if date:
            events.append({
                "date": date,
                "event": "material_progress",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 7. script_compiled (compiledAt)
        date = normalize_date(entry.get("compiledAt", ""))
        if date:
            events.append({
                "date": date,
                "event": "script_compiled",
                "id": nid,
                "type": ntype,
                "name": name,
            })

        # 8. deposit_merged (mergeHistory)
        mh = entry.get("mergeHistory", [])
        if isinstance(mh, list):
            for merge_date in extract_merge_dates(mh):
                events.append({
                    "date": merge_date,
                    "event": "deposit_merged",
                    "id": nid,
                    "type": ntype,
                    "name": name,
                })

    # 按日期排序
    events.sort(key=lambda e: e["date"])
    return events


def load_and_extract() -> list[dict]:
    """加载图谱并提取时间线事件 — 供 build_visualization.py 导入调用。"""
    with open(ONTOLOGY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    graph = data.get("@graph", [])
    return extract_timeline_events(graph)


def main():
    if not os.path.exists(ONTOLOGY_PATH):
        print(f"Error: {ONTOLOGY_PATH} not found", file=sys.stderr)
        sys.exit(1)

    events = load_and_extract()

    # 输出 JSON
    print(json.dumps(events, ensure_ascii=False, indent=2))

    # 统计摘要到 stderr
    from collections import Counter
    counts = Counter(e["event"] for e in events)
    total = len(events)
    date_range = f"{events[0]['date']} ~ {events[-1]['date']}" if events else "N/A"
    print(f"\n--- Timeline: {total} events, {date_range} ---", file=sys.stderr)
    for event_type, count in counts.most_common():
        print(f"  {event_type}: {count}", file=sys.stderr)

    # 提醒不可追踪的事件
    print("\n⚠ depth_upgrade 事件无法追踪（需要 mutation log）", file=sys.stderr)


if __name__ == "__main__":
    main()
