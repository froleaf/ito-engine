#!/usr/bin/env python3
"""
读取 ontology/ontology.jsonld，解析图谱数据，
注入 templates/visualization_template.html 模板，
输出 visualization.html。
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTOLOGY_PATH = os.path.join(BASE_DIR, "ontology", "ontology.jsonld")
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "visualization_template.html")
OUTPUT_PATH = os.path.join(BASE_DIR, "visualization.html")

# Edge properties that point to other nodes (value is @id or list of @id)
EDGE_PROPERTIES = {
    "subBranch", "parentBranch", "belongsTo", "isA",
    "prerequisite", "relatedTo", "contradicts", "appliesTo", "exemplifiedBy",
    "hasMisconception", "confusedWith",
    "hasResource", "coversTopics",
    "derivedFrom", "inspiredBy",
    "crossDomainLink",
    "aboutNodes", "aboutDomains",
    "relatedDeposits",
}

# Node properties to extract for visualization
NODE_DISPLAY_PROPS = {
    "name", "description", "priority", "depth", "nodeRole",
    "userInsight", "outputStatus", "outputPotential",
    "depositType", "materialType", "author",
    "readingStatus", "progress",
    "scenarioTags", "appliedInCount",
}


def load_graph():
    with open(ONTOLOGY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("@graph", [])


def find_domain(node_id, graph_entries, parent_cache):
    """Recursively find the DomainRoot ancestor of a node."""
    if node_id in parent_cache:
        return parent_cache[node_id]

    for entry in graph_entries:
        if entry.get("@id") == node_id:
            if entry.get("@type") == "DomainRoot":
                parent_cache[node_id] = node_id
                return node_id
            # Check parentBranch or belongsTo
            parent = entry.get("parentBranch") or entry.get("belongsTo")
            if parent:
                result = find_domain(parent, graph_entries, parent_cache)
                parent_cache[node_id] = result
                return result
    return None


def build_graph_data(graph_entries):
    """Extract nodes and links from @graph entries."""
    nodes = []
    links = []
    node_ids = {e["@id"] for e in graph_entries if "@id" in e}
    parent_cache = {}

    # First pass: identify all DomainRoot nodes
    for entry in graph_entries:
        if entry.get("@type") == "DomainRoot":
            parent_cache[entry["@id"]] = entry["@id"]

    # Second pass: build parent cache for branches
    for entry in graph_entries:
        eid = entry.get("@id")
        if not eid:
            continue
        parent = entry.get("parentBranch") or entry.get("belongsTo")
        if parent:
            find_domain(eid, graph_entries, parent_cache)

    # Third pass: build nodes and links
    for entry in graph_entries:
        eid = entry.get("@id")
        etype = entry.get("@type")
        if not eid or not etype:
            continue

        # Build node
        node = {"id": eid, "type": etype}
        for prop in NODE_DISPLAY_PROPS:
            if prop in entry:
                node[prop] = entry[prop]

        # Determine domain affiliation
        node["domain"] = find_domain(eid, graph_entries, parent_cache)

        nodes.append(node)

        # Extract edges
        for prop in EDGE_PROPERTIES:
            if prop not in entry:
                continue
            targets = entry[prop]
            if isinstance(targets, str):
                targets = [targets]
            if not isinstance(targets, list):
                continue
            for target in targets:
                if isinstance(target, str) and target in node_ids:
                    links.append({
                        "source": eid,
                        "target": target,
                        "type": prop,
                    })

    return nodes, links


def generate_js(nodes, links):
    """Generate the JS data assignment string."""
    nodes_json = json.dumps(nodes, ensure_ascii=False, indent=2)
    links_json = json.dumps(links, ensure_ascii=False, indent=2)
    return f"const graphNodes = {nodes_json};\n\nconst graphLinks = {links_json};\n"


def main():
    if not os.path.exists(ONTOLOGY_PATH):
        print(f"Error: {ONTOLOGY_PATH} not found", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: {TEMPLATE_PATH} not found", file=sys.stderr)
        sys.exit(1)

    graph_entries = load_graph()
    nodes, links = build_graph_data(graph_entries)

    js_data = generate_js(nodes, links)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    output = template.replace("/* __GRAPH_DATA__ */", js_data)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)

    node_types = {}
    for n in nodes:
        node_types[n["type"]] = node_types.get(n["type"], 0) + 1
    type_summary = ", ".join(f"{t}: {c}" for t, c in sorted(node_types.items()))
    print(f"visualization.html generated: {len(nodes)} nodes ({type_summary}), {len(links)} links")

    # Detect orphan nodes (no edges at all)
    connected = set()
    for link in links:
        connected.add(link["source"])
        connected.add(link["target"])
    orphans = [n for n in nodes if n["id"] not in connected and n["type"] != "DomainRoot"]
    if orphans:
        print(f"\n⚠ WARNING: {len(orphans)} orphan node(s) with NO edges:")
        for o in orphans:
            print(f"  - [{o['type']}] {o['id']} ({o.get('name', '?')})")


if __name__ == "__main__":
    main()
