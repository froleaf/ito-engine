---
name: ontology-init
description: 为用户声明的关注领域构建骨架本体，追加到统一知识图谱。由 /cold-start 调用。
user-invocable: false
---

## 角色

知识工程师。为用户声明的关注领域构建骨架本体。本体中的知识节点必须基于**权威学术定义**，而非用户的口语描述。

## 核心原则

### 学术权威性原则

> 用户说"我最近在看侯世达的怪圈"——你不应该创建一个叫"怪圈"的节点。
> 你应该识别出这指向"自指 (Self-reference)"和"递归 (Recursion)"等学术概念，
> 然后基于学术定义构建这些节点的知识谱系，并将《哥德尔、艾舍尔、巴赫》作为 Material 实体挂载。

### 图查询前置

所有操作前，先用 grep 查询 `ontology/ontology.jsonld` 确认节点是否已存在。

## 输入

- 领域信息（来自 /cold-start 的领域探索对话）
- `templates/domain_scaffold.jsonld`：骨架本体模板（@context 参考）

## 处理逻辑

### 对每个领域执行：

1. **生成领域 ID**：将领域名称转为 snake_case 英文标识（如"认知科学" → `cognitive_science`）

2. **确定分支前缀**：取 2 个字母的缩写（如 `cs` → cognitive_science），用于分支 @id

3. **研究顶层分支**：
   - 基于权威学术信息确定该领域的 5-10 个主要方向/分支
   - 每个分支写一段简要描述（1-2 句话）
   - 结合用户提到的具体话题，确保这些话题能被归入某个分支
   - 分支名称使用该学科的通用术语

4. **追加到统一图谱**：
   将 DomainRoot + BranchScaffold 节点追加到 `ontology/ontology.jsonld` 的 `@graph` 数组中：
   ```json
   {
     "@type": "DomainRoot",
     "@id": "domain_{id}",
     "name": "领域名称",
     "description": "领域整体描述",
     "priority": "primary|foundation|supplementary",
     "subBranch": ["branch_{prefix}_xxx", "branch_{prefix}_yyy"]
   },
   {
     "@type": "BranchScaffold",
     "@id": "branch_{prefix}_xxx",
     "name": "分支名称",
     "description": "分支简要描述",
     "parentBranch": "domain_{id}"
   }
   ```

5. **更新领域索引**：在 `ontology/_meta/domains.md` 中追加新领域名称。

### 导航层 vs 知识层

DomainRoot 和 Branch/BranchScaffold 构成**导航层**——它们是学科领域的目录结构，用于组织和定位知识。导航层节点**可以**携带个人元数据（depth、userInsight 等），表示用户在该领域/分支的整体了解程度。但 Agent 必须理解：**导航层的 depth 标记不意味着用户精通该层下的所有内容**，只代表用户对这个方向有某种程度的了解。

真正代表用户具体掌握了什么的，是导航层之下的知识节点（KnowledgeNode、Material、Deposit 等）。

### 骨架质量标准

- 分支数量 5-10 个，覆盖领域的主要方向
- 所有分支标记为 `@type: "BranchScaffold"`，表示待扩展
- 不展开子节点——这些将在后续交互中由 `/knowledge-process` 渐进构建

### 命名规则

| 实体类型 | ID 前缀 | 示例 |
|----------|---------|------|
| DomainRoot | `domain_` | `domain_cognitive_science` |
| BranchScaffold | `branch_{prefix}_` | `branch_cs_consciousness` |
| Branch | `branch_{prefix}_` | `branch_cs_consciousness`（升级后） |
| KnowledgeNode | `{prefix}_` | `cs_self_reference` |
| Material | `mat_` | `mat_geb` |
| MisconceptionPattern | `mp_` | `mp_embodied_vs_behaviorism` |
| ThinkingDeposit | `td_` | `td_education_as_temporal_transfer` |
| CrossDomainLink | `link_` | `link_music_emotion_healing` |
| ThinkingScript | `ts_` | `ts_occam_decision` |

## 输出

- 更新后的 `ontology/ontology.jsonld`（追加了新领域节点）
- 更新后的 `ontology/_meta/domains.md`
- 执行 `python3 scripts/build_visualization.py` 同步可视化
