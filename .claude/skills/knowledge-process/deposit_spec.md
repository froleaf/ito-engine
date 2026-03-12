# 沉淀产出（Deposit）规范

## 判断标准

当识别到用户的内容构成一份**有结构的知识整理**或**有实质的原创思考**时，创建沉淀产出实体。

- **KnowledgeDeposit**：用户将学到的知识进行了结构化整理输出（不是"学了什么"，而是"整理出了什么"）。例如：结构化的读书笔记、知识体系梳理文、概念对比分析
- **ThinkingDeposit**：用户产出了原创思考、模型、框架。例如：独立见解的论述、自创的分析框架、跨域洞察

## 三种状态

- `planned`：用户表达了输出意向但尚未动笔（"我想写…"、"打算分享…"）。此时创建图谱实体但不创建内容文件，作为后续内容汇聚的锚点
- `deposited`：内容已沉淀完成
- `published`：已对外输出（文章、分享等）

## 创建流程

1. **查重合并优先**：在图谱中 grep 同领域/同分支下已有的 Deposit 实体，检查是否是对同一主题的延续或深化
   - 如已有 `planned` 状态的同主题 Deposit → 将内容填入该 Deposit，状态升级为 `deposited`，创建内容文件
   - 如已有 `deposited` 状态的同主题 Deposit → 合并内容到已有文件，更新实体的 `updatedAt` 和 `mergeHistory`
   - 如无匹配 → 创建新实体

2. **创建实体**（追加到 ontology.jsonld @graph）：
```json
{
  "@type": "ThinkingDeposit",
  "@id": "td_{short_id}",
  "name": "产出标题",
  "description": "内容摘要（2-3句话）",
  "depositType": "thinking",
  "outputStatus": "deposited",
  "contentPath": "output/deposits/td_{short_id}.md",
  "aboutNodes": ["相关知识节点@id列表"],
  "aboutDomains": ["相关领域@id列表"],
  "derivedFrom": ["启发来源节点"],
  "coCreatedWith": "AI名称（如有）",
  "sourceRef": "原始素材路径或来源标识",
  "updatedAt": "ISO 8601"
}
```

3. **写入内容文件**：将内容整理为 Markdown 文件存入 `output/deposits/`，格式如下：

```markdown
# {产出标题}

> **类型**：知识沉淀 / 思考沉淀
> **状态**：沉淀 / 已发布（{渠道}）
> **协作**：与 {AI名称} 共同产出（如适用，否则省略此行）
> **涉及领域**：{领域列表}
> **关联节点**：{关键知识节点}
> **更新时间**：{最近更新日期}

## 导读

{AI 生成的内容摘要，比图谱 description 更详细，约 200-500 字，
帮助用户快速回忆这份内容的核心要点、论证结构和独特之处}

---

## 原文

{用户的完整原始内容，保留原始表达}
```

4. **在相关知识节点上标记**：`outputStatus: "deposited"` 或 `"published"`，以及 `relatedDeposits` 指向 deposit @id

5. **已发布产出额外记录**：`outputTitle`、`outputDate`、`publishedTo`（发布渠道）、`publishedUrl`（外部链接）。即使有外部链接，也在 deposits/ 保留一份本地副本，防止链接失效

## 协作归因（coCreatedWith）

当内容的主体产出来自用户与 AI 的协作时，必须标注 `coCreatedWith` 字段（值为 AI 名称，如 "Gemini"、"ChatGPT"、"Claude" 等）。判断标准：
- 用户提供方向/种子 + AI 展开主体内容 → 标注
- 用户口述完整思考、AI 仅做结构化整理 → 不标注
- 用户与 AI 对话中双方都有实质性贡献 → 标注

同时在对应知识节点上，区分用户的原创见解（记入 `userInsight`）和 AI 的展开（记入 `description`），避免虚高 `depth` 和 `nodeRole`。

## 原始来源追溯（sourceRef）

每个 Deposit 必须记录原始素材的来源路径，确保从 todo → deposit → sourceRef → 原文的完整可追溯链：
- 来自笔记文件 → `"inbox/processed/文件名.md"`（归档后的路径）
- 来自对话 → `"inbox/conversations/对话存档文件名.md"`
- 来自 URL → 原始 URL
- 来自用户口述（无独立文件）→ `"chat_YYYY-MM-DD"`（指向对话存档）

## 查阅规则（三层访问）

| 场景 | 操作 | token 消耗 |
|------|------|-----------|
| Agent 需要了解内容 | 只 Read 导读部分（到 `---` 为止） | 低 |
| 用户问"这份讲了什么" | 基于导读回答 | 低 |
| 用户说"把原文给我" | 用 `cat` 或 `sed` 提取 `## 原文` 之后的部分，直接打印输出给用户。**Agent 不读取这段内容**，只负责把文件内容投递出去 | 无（AI 不处理） |
| 用户说"帮我分析一下原文" / 明确指示 AI 读原文 | Read 整个文件，AI 消耗 token 阅读并分析 | 高 |

**关键区分**：
- "给我原文" = 管道投递，Agent 作为文件搬运工，不读不理解
- "读一下原文" / "分析原文" = Agent 消耗 token 阅读理解

## 合并机制

- 同一主题的思考反复出现时，内容合并到同一份 deposit 文件中（追加新段落并标注时间）
- 图谱实体的 `mergeHistory` 记录每次合并
- 防止相关的思考散落在不同节点上

## Todo 联动

- 创建 Deposit 时，如果导读中包含明确的"待深入方向"或"未展开的追问"，同时在 `memory/todo.json` 中创建 `deep_thinking` 类型的 todo（按 `templates/todo_record.json` 格式），关联该 Deposit 节点
- 不是每个 Deposit 都需要生成 todo——只在确实有值得继续追问的方向时才创建

## outputPotential 联动

- 当任何节点（KnowledgeNode、CrossDomainLink、Deposit 等）被标记 `outputPotential: "high"` 时，同时在 `memory/todo.json` 中创建 `deep_thinking` 类型的 todo，标题描述该节点的输出潜力方向，`relatedNodes` 指向被标记的节点
- 这确保了高潜力方向不会只静默标记在图谱中，而是进入用户的待办视野

## 用户原创理论/洞见

当用户表达了原创理论或跨域洞见，直接按 Deposit 流程处理（创建图谱实体 + 写入内容文件到 `output/deposits/`），不再使用 UserTheory 实体类型。

## CrossDomainLink 创建

```json
{
  "@id": "link_{short_id}",
  "@type": "CrossDomainLink",
  "name": "领域A×领域B→主题",
  "crossDomainLink": ["branch_a_xxx", "branch_b_yyy"],
  "link_type": "analogy|structural_isomorphism|causal|complementary|application",
  "userInsight": "用户对这个交叉点的理解",
  "confidence": "certain|likely|uncertain",
  "outputPotential": "potential"
}
```
