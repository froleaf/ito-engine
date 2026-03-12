# 图谱 Schema 约束

写入 `ontology.jsonld` 时，**只允许使用以下实体类型和边属性**。不得自创字段——自创字段不会生成可视化边，导致节点孤立。

## 合法实体类型

| @type | 用途 | ID 前缀 |
|-------|------|---------|
| DomainRoot | 领域根节点 | `domain_` |
| Branch | 已激活的分支 | `branch_{2字母}_` |
| BranchScaffold | 骨架分支（待激活） | `branch_{2字母}_` |
| KnowledgeNode | 知识节点 | `{前缀}_` |
| Material | 学习材料 | `mat_` |
| MisconceptionPattern | 认知歧义模式 | `mp_` |
| KnowledgeDeposit | 知识沉淀产出 | `kd_` |
| ThinkingDeposit | 思考沉淀产出 | `td_` |
| CrossDomainLink | 跨域关联 | `link_` |
| ThinkingScript | 编译后的思维脚本 | `ts_` |

## 合法边属性（能产生可视化边的字段）

| 属性 | 语义 | 典型使用者 |
|------|------|-----------|
| `belongsTo` | 归属于上级分支 | KnowledgeNode → Branch |
| `parentBranch` | 分支的父分支 | Branch → Branch/DomainRoot |
| `subBranch` | 包含的子分支 | DomainRoot/Branch → Branch |
| `isA` | 是某类的子类 | KnowledgeNode → KnowledgeNode |
| `prerequisite` | 前置知识 | KnowledgeNode → KnowledgeNode |
| `relatedTo` | 相关知识 | KnowledgeNode → KnowledgeNode |
| `contradicts` | 矛盾/对立 | KnowledgeNode → KnowledgeNode |
| `appliesTo` | 应用于 | KnowledgeNode → KnowledgeNode |
| `exemplifiedBy` | 以…为例 | KnowledgeNode → KnowledgeNode/Material |
| `hasMisconception` | 有歧义模式 | KnowledgeNode → MisconceptionPattern |
| `confusedWith` | 易混淆 | MisconceptionPattern → KnowledgeNode |
| `hasResource` | 有学习资源 | KnowledgeNode/Branch → Material |
| `coversTopics` | 覆盖主题 | Material → KnowledgeNode/Branch/Deposit |
| `derivedFrom` | 派生自 | Deposit/CrossDomainLink → KnowledgeNode |
| `inspiredBy` | 启发自 | Deposit → Material/KnowledgeNode |
| `crossDomainLink` | 跨域连接的节点 | CrossDomainLink → Branch |
| `aboutNodes` | 关联知识节点 | Deposit → KnowledgeNode/Branch |
| `aboutDomains` | 关联领域 | Deposit → DomainRoot |
| `relatedDeposits` | 关联产出 | KnowledgeNode → Deposit |

**禁止使用的常见错误字段**：`domains`（不生成边，用 `aboutDomains`）、`relatedNodes`（不生成边，Material 用 `coversTopics`，Deposit 用 `aboutNodes`）。
