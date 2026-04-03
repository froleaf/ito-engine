# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

ITO Engine (Input-Think-Output) is a **file-system-driven personal knowledge management Agent**. It has no code to build/test/lint — the entire system is structured files (Markdown skills, JSON-LD graphs, JSONL logs, JSON templates) that an LLM reads and writes at runtime. The working language is **Simplified Chinese (zh-CN)**.

## Architecture: Unified Knowledge Graph

The core data model is a single JSON-LD graph database (`ontology/ontology.jsonld`) containing:
- Domain knowledge: DomainRoot, Branch, BranchScaffold, KnowledgeNode, Material, MisconceptionPattern
- Personal cognitive data: depth, nodeRole, userInsight, misconceptions — annotated **directly on knowledge nodes**
- Cross-domain structures: CrossDomainLink
- Output entities: KnowledgeDeposit, ThinkingDeposit
- Compiled cognition: ThinkingScript (with scenario routing via `ontology/_meta/thinking_scenarios.md`)

**Critical rule: JSON-LD file is a graph database.** Query by `@id` grep. **NEVER** brute-force read the entire file.

**Navigation vs Knowledge layer:** DomainRoot and Branch/BranchScaffold form the **navigation layer** (directory structure). They CAN carry personal metadata (depth etc.), but this only indicates general familiarity, NOT mastery of everything underneath. Actual knowledge is represented by nodes BELOW this layer (KnowledgeNode, Material, Deposit, etc.).

Supporting files:
- `agent_profile.json` — Agent identity, behavior rules, knowledge architecture config
- `ontology/_meta/domains.md` — Simple list of registered domain names (the only registry)
- `templates/` — Record structure templates for all JSONL and graph entities

## Graph Query Patterns

```
grep "@id.*node_id" ontology/ontology.jsonld       # By @id
grep "@type.*DomainRoot" ontology/ontology.jsonld   # By @type
grep -i "keyword" ontology/ontology.jsonld          # By keyword
grep "depth" ontology/ontology.jsonld               # Personal data on nodes
grep "@type.*CrossDomainLink" ontology/ontology.jsonld  # Cross-domain links
grep "@type.*Deposit" ontology/ontology.jsonld      # Deposits
grep "outputPotential" ontology/ontology.jsonld     # Output candidates
grep "appliedIn" ontology/ontology.jsonld           # Mental model usage logs
grep "mental_model" ontology/ontology.jsonld        # Thinking tools
grep "readingStatus.*in_progress" ontology/ontology.jsonld  # Active reading materials
```

## Skill System

Skills live in `.claude/skills/*/SKILL.md`. Skills with `user-invocable: false` are internal (called by other skills, not by user).

Call chains:
```
/cold-start → ontology-init → knowledge-extract → knowledge-process (NO session_memory) + (user decides when to /bootstrap or /plan)
/cold-start-obsidian → import_obsidian.py (zero-token) → AI reads vault_analysis.json → ontology-init → lightweight registration → selective /bootstrap (hub notes only) → knowledge-extract → knowledge-process (NO session_memory)
/chat | /pass-note | /write-note → knowledge-extract → knowledge-process → Deposit creation
/bootstrap → knowledge-extract → knowledge-process → Deposit creation (NO session_memory, NO plan trigger)
/weekly-review → /plan + dormant-check
/content-review → READ-ONLY (no graph/memory writes, optional save to output/content-reviews/)
/compile-thinking → READ-ONLY (analyzes mental_model appliedIn logs, CrossDomainLink patterns, ThinkingDeposits → generates thinking scripts in output/thinking_scripts/)
/brain → READ-ONLY (cognitive proxy mode, no graph/memory writes, output to docs/brain/, dialectic loop: "审视"→content-review→"继续"→brain)
```

The `/ito` skill is the main entry point (auto-activated). It routes to sub-skills based on user intent. **Standby mode** (default) handles tool requests without session recording; **session mode** (triggered by "聊天"/"传笔记"/"写笔记") records to session_memory.

## Output System: Deposits

Deposit entities (KnowledgeDeposit / ThinkingDeposit) live in the graph. Content files in `output/deposits/` contain **only metadata header + AI 导读** (no raw text). Raw text lives in `inbox/conversations/` or `inbox/processed/`, linked via `sourceRef` in the graph entity and `原文来源` in the deposit file header.

**Three-tier access rule:**
| Request | Agent action | Token cost |
|---------|-------------|------------|
| Agent needs context | Read deposit file (导读 only) | Low |
| User asks "这份讲了什么" | Answer from 导读 | Low |
| User says "给我原文" | Follow sourceRef → Bash pipe raw file, Agent does NOT read | None |
| User says "帮我分析原文" | Follow sourceRef → Agent reads raw file | High |

No separate seeds file — use `outputPotential` markers on graph nodes to track candidates.

## Memory Layer Conventions

All `.jsonl` files are **append-only** (never modify existing lines). Every record must have an ISO 8601 `ts` field. Use templates in `templates/` for record structure.

`session_memory` is stored per-week: `memory/session_memory/{YYYY}-W{WW}.jsonl`. Before writing, calculate the current ISO week number and create the file if needed.

`memory/todo.json` is the exception along with `ontology/ontology.jsonld` — it uses **read-modify-write** (it's a structured list, not a log). Each todo item follows `templates/todo_record.json` format, with types: `topic_to_explore` (待聊话题), `reading` (未完成阅读), `deep_thinking` (待深化思考), `action_item` (行动待办). Todos are created by `/chat` (conversation follow-ups), `/knowledge-process` (deposit-linked deep thinking), and manually via standby mode. Reviewed during `/weekly-review`.

`ontology/ontology.jsonld` is the exception — it uses **read-modify-write** (it's a graph, not a log).

## Entity ID Naming Convention

| Entity type | ID prefix | Example |
|-------------|-----------|---------|
| DomainRoot | `domain_` | `domain_cognitive_science` |
| Branch/BranchScaffold | `branch_{2-letter-prefix}_` | `branch_cs_consciousness` |
| KnowledgeNode | `{prefix}_` | `cs_self_reference` |
| Material | `mat_` | `mat_geb` |
| MisconceptionPattern | `mp_` | `mp_embodied_vs_behaviorism` |
| ThinkingDeposit | `td_` | `td_education_as_temporal_transfer` |
| KnowledgeDeposit | `kd_` | `kd_systems_thinking_notes` |
| CrossDomainLink | `link_` | `link_music_emotion_healing` |
| ThinkingScript | `ts_` | `ts_occam_decision` |

## Visualization

`visualization.html` is auto-generated — **do not edit it directly**. It's built from:
- `templates/visualization_template.html` — D3.js force-directed graph template (edit this for visual changes)
- `scripts/build_visualization.py` — reads `ontology/ontology.jsonld`, injects data into template

**Mandatory rebuild rule:** Every write to `ontology/ontology.jsonld` MUST be followed by `python3 scripts/build_visualization.py` before responding to the user. No exceptions — whether the write happens in a skill (knowledge-process, bootstrap, ontology-init) or in standby mode (adding Materials, updating readingStatus, creating Deposits, etc.). This is a global post-write hook, not something individual skills need to remember.

## Cognitive Trajectory

`memory/trajectory.json` is auto-generated by `scripts/build_trajectory.py`. It analyzes recent `session_memory` to identify active cognitive threads and nearby unexplored graph nodes. The `/ito` skill runs this on startup.

## Session Memory Schema

All `session_memory` records **must** follow `templates/session_record.json` exactly — no custom field names. Key fields: `ts`, `interaction_type`, `topic` (required, ≤30 chars), `domains_touched`, `input_summary`, `knowledge_extracted`, `thinking_notes`, `cross_domain_links`, `deposits_created`, `deposits_updated`, `duration_min`, `ito_classification`. Migration script: `scripts/migrate_session_memory.py`.

## Conventions When Editing Skills

- All knowledge operations go through `ontology/ontology.jsonld` (single unified file)
- Domain discovery: read `ontology/_meta/domains.md` first, then grep the unified graph
- Personal cognitive data (depth, nodeRole, userInsight, misconceptions) is annotated directly on knowledge nodes — no separate personal ontology
- `/ito` standby vs session mode distinction matters: tool requests don't create session records; only explicit "聊天"/"传笔记"/"写笔记" triggers session recording
- `_init/` mirrors data directories in their empty/initial state — used by `/cold-start` (first-time init) and `/reset`. **When adding new data directories or files, sync `_init/` to match**
- Deposit files: Agent reads only 导读 (above `---`), never reads 原文 unless user explicitly instructs
- **Implicit cognition detection** (in knowledge-extract): when the user is clearly USING a mental model to make a decision (not just talking about it), the Agent must report the finding to the user for confirmation before writing to the graph. High threshold — if unsure, don't flag it
