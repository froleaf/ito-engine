---
name: knowledge-process
description: 根据知识提取结果更新统一图谱（领域知识扩展、个人元数据标注、歧义检测、跨域发现），生成 session 记录。由 chat/pass-note/write-note 在交互结束时调用。
user-invocable: false
---

## 角色

知识图谱工程师和认知分析师。根据知识提取结果更新统一图谱（领域知识扩展 + 个人元数据标注 + 歧义检测 + 跨域发现），生成 session 记录，检测输出种子。

## 输入

- `/knowledge-extract` 的结构化提取结果
- `ontology/ontology.jsonld`：统一知识图谱（通过 grep 按需查询）
- `templates/session_record.json`：session_memory 条目模板

## 图谱 Schema 约束

写入 `ontology.jsonld` 时，**只允许使用以下实体类型和边属性**。不得自创字段——自创字段不会生成可视化边，导致节点孤立。

### 合法实体类型

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

### 合法边属性（能产生可视化边的字段）

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

## 处理逻辑

### 第一步：图谱扩展（领域知识构建）

对知识提取结果中标记为 `create` 的新知识点，执行**翻译-构建-挂载三步法**：

1. **翻译用户输入**：将口语/俗称映射到标准学术术语，保留原始表述作为 `aliases`
2. **grep 检查是否已存在**：`grep "学术术语" ontology/ontology.jsonld`
3. **构建知识谱系**：
   - 基于权威学术定义构建节点，追加到 @graph
   - **所有新节点必须标注 `createdAt`**（当前时间 ISO 8601）
   - 建立边关系（belongsTo、isA、prerequisite、relatedTo 等）
   - 同时创建 3-5 个同级/子级节点
4. **创建 Material 实体（如有）**：调用 `add-material` skill 的流程（查重→信息补全→边关系→写入→todo 联动→rebuild）。详见 `.claude/skills/add-material/SKILL.md`
5. **BranchScaffold 升级**：如新节点属于某 BranchScaffold → 升级为 Branch

对标记为 `deepen` 的知识点：补充 description 细节、添加新边、挂载新材料。

**质量要求**：
- 节点学术定义来自 AI 知识储备/权威信息，**不照搬用户原始表述**
- 用户原始表述保存在 `aliases` 中
- 每个新节点至少建立 2 条边
- 只沿用户探索路径扩展，不凭空编造

### 第二步：个人元数据更新（直接在节点上标注）

**新接触的节点**：
- 标注 `depth: "浅读"`（或根据用户表达的深度直接标注更高级别）
- 标注 `nodeRole`（根据用户表述判断：knowledge/mental_model/methodology/skill）
- 标注 `firstContact`、`lastContact`、`contactCount: 1`
- 如用户表达了独立见解 → 记录 `userInsight`

**再次接触的节点**（grep 确认已有 depth 等字段）：
- 更新 `lastContact`、递增 `contactCount`
- 按深度升级规则评估是否升级 `depth`
- 更新 `userInsight`（如有新见解）

**深度标签升级规则**（只升不降）：

| 当前深度 | 升级条件 | 升级到 |
|----------|----------|--------|
| 浅读 | 用户能准确复述核心内容 | 理解 |
| 理解 | 用户表达了原创观点或独特类比 | 有独立见解 |
| 有独立见解 | 用户在输出（文章/分享）中系统阐述 | 可教授他人 |

**nodeRole 判断规则**：
- 用户说"我用 X 来思考/分析问题" → `mental_model`
- 用户说"我的工作方法是 X" → `methodology`
- 用户说"我会 X"/"我擅长 X" → `skill`
- 用户说"我读过/学过/知道 X" → `knowledge`（默认）

**隐性认知确认后的 appliedIn 写入**：

当 knowledge-extract 检测到隐性认知调用，且用户确认（或未否认）后，在被调用的 mental_model/methodology 节点上追加一条 `appliedIn` 记录：

```json
{
  "ts": "2026-03-06T14:30:00+08:00",
  "context": "在讨论ITO引擎的实体类型设计时",
  "decision": "用奥卡姆剃刀原则决定删除冗余的 UserTheory 实体",
  "confirmedBy": "user"
}
```

字段说明：
- `ts`：调用发生的时间
- `context`：在什么场景/话题下调用的（1 句话）
- `decision`：用这个思维工具做了什么判断（1 句话）
- `confirmedBy`：`"user"`（用户明确确认）或 `"implicit"`（用户未否认）

这些记录是 `/compile-thinking` 的核心数据源——通过分析一个 mental_model 的 appliedIn 日志，可以还原出用户何时、在什么类型的问题上、如何使用这个思维工具。

### Material 信息检索规范

创建 Material 实体时，Agent 必须基于 AI 知识储备**主动补全**以下信息，不能只记录用户提到的片段：

**书籍（book）**：
- `author`：完整作者列表（数组），查证准确的姓名拼写
- `translator`：如用户提到的是翻译版本，查证译者
- `publicationYear`：首版出版年份
- `publisher`：出版社（如可知）
- `isbn`：ISBN（如可知）
- `language`：原著语言

**在线课程/视频（video_course/online_course）**：
- `author`：讲师/机构
- `url`：课程链接（Coursera/edX/YouTube/Bilibili 等公开平台）
- `platform`：所在平台

**文章/论文（article/paper）**：
- `author`：作者列表
- `url`：公开链接（如有）
- `publicationYear`：发表年份

**原则**：
- 信息来自 AI 知识储备，**确信时直接填写，不确定时留空**，不用幻觉填充
- 用户说"侯世达的 GEB" → 你应该填 `author: ["Douglas Hofstadter"]`, `name: "Gödel, Escher, Bach: An Eternal Golden Braid"`, 中文别名放 `aliases`
- 同一本书的不同版本/译本可以共用一个 Material 节点，用 `aliases` 记录不同译名

### Material 阅读状态管理

当知识提取结果中的 material 包含 `readingStatus` 时：

**新创建的 Material**：
```json
{
  "@type": "Material",
  "@id": "mat_{short_id}",
  "name": "材料名称",
  "materialType": "book",
  "readingStatus": "in_progress",
  "progress": "读到第3章",
  "startedAt": "2026-03-06",
  "lastProgressUpdate": "2026-03-06",
  "coversTopics": ["相关知识节点@id"]
}
```

**已有的 Material**（grep 确认已存在）：
- 更新 `readingStatus`（如状态变化）
- 更新 `progress`（如有新进度）
- 更新 `lastProgressUpdate`

**合法状态值**：`wishlist` | `in_progress` | `paused` | `completed` | `abandoned`

**状态转换规则**：
- `wishlist` → `in_progress`：用户开始阅读
- `in_progress` → `completed`：用户明确说读完/看完了
- `in_progress` → `paused`：用户说暂时放下了
- `paused` → `in_progress`：用户说又开始读了
- 任何状态 → `abandoned`：用户明确说不读了
- `completed` 后如用户说"我在重读"→ 保持 `completed`，更新 `progress` 为"重读中"

**Todo 联动**：
- 创建 `readingStatus: "in_progress"` 或 `"wishlist"` 的 Material 时，同时在 `memory/todo.json` 中创建 `reading` 类型的 todo，`relatedNodes` 指向该 Material 的 @id
- Material 状态变为 `completed` 或 `abandoned` 时，将对应 todo 标记为 `completed` 或 `dropped`
- Material 状态变为 `paused` 时，todo 保持 `open`（下次 weekly-review 会提醒）

### 沉淀产出处理（Deposit）

当识别到用户的内容构成一份**有结构的知识整理**或**有实质的原创思考**时，创建沉淀产出实体。

**判断标准：**
- **KnowledgeDeposit**：用户将学到的知识进行了结构化整理输出（不是"学了什么"，而是"整理出了什么"）。例如：结构化的读书笔记、知识体系梳理文、概念对比分析
- **ThinkingDeposit**：用户产出了原创思考、模型、框架。例如：独立见解的论述、自创的分析框架、跨域洞察

**三种状态：**
- `planned`：用户表达了输出意向但尚未动笔（"我想写…"、"打算分享…"）。此时创建图谱实体但不创建内容文件，作为后续内容汇聚的锚点
- `deposited`：内容已沉淀完成
- `published`：已对外输出（文章、分享等）

**创建流程：**

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

**协作归因（coCreatedWith）**：当内容的主体产出来自用户与 AI 的协作时，必须标注 `coCreatedWith` 字段（值为 AI 名称，如 "Gemini"、"ChatGPT"、"Claude" 等）。判断标准：
- 用户提供方向/种子 + AI 展开主体内容 → 标注
- 用户口述完整思考、AI 仅做结构化整理 → 不标注
- 用户与 AI 对话中双方都有实质性贡献 → 标注
同时在对应知识节点上，区分用户的原创见解（记入 `userInsight`）和 AI 的展开（记入 `description`），避免虚高 `depth` 和 `nodeRole`。

**原始来源追溯（sourceRef）**：每个 Deposit 必须记录原始素材的来源路径，确保从 todo → deposit → sourceRef → 原文的完整可追溯链：
- 来自笔记文件 → `"inbox/processed/文件名.md"`（归档后的路径）
- 来自对话 → `"inbox/conversations/对话存档文件名.md"`
- 来自 URL → 原始 URL
- 来自用户口述（无独立文件）→ `"chat_YYYY-MM-DD"`（指向对话存档）

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

**查阅规则（三层访问）**：

| 场景 | 操作 | token 消耗 |
|------|------|-----------|
| Agent 需要了解内容 | 只 Read 导读部分（到 `---` 为止） | 低 |
| 用户问"这份讲了什么" | 基于导读回答 | 低 |
| 用户说"把原文给我" | 用 `cat` 或 `sed` 提取 `## 原文` 之后的部分，直接打印输出给用户。**Agent 不读取这段内容**，只负责把文件内容投递出去 | 无（AI 不处理） |
| 用户说"帮我分析一下原文" / 明确指示 AI 读原文 | Read 整个文件，AI 消耗 token 阅读并分析 | 高 |

**关键区分**：
- "给我原文" = 管道投递，Agent 作为文件搬运工，不读不理解
- "读一下原文" / "分析原文" = Agent 消耗 token 阅读理解

**合并机制**：
- 同一主题的思考反复出现时，内容合并到同一份 deposit 文件中（追加新段落并标注时间）
- 图谱实体的 `mergeHistory` 记录每次合并
- 防止相关的思考散落在不同节点上

**Todo 联动**：
- 创建 Deposit 时，如果导读中包含明确的"待深入方向"或"未展开的追问"，同时在 `memory/todo.json` 中创建 `deep_thinking` 类型的 todo（按 `templates/todo_record.json` 格式），关联该 Deposit 节点
- 不是每个 Deposit 都需要生成 todo——只在确实有值得继续追问的方向时才创建

**outputPotential 联动**：
- 当任何节点（KnowledgeNode、CrossDomainLink、Deposit 等）被标记 `outputPotential: "high"` 时，同时在 `memory/todo.json` 中创建 `deep_thinking` 类型的 todo，标题描述该节点的输出潜力方向，`relatedNodes` 指向被标记的节点
- 这确保了高潜力方向不会只静默标记在图谱中，而是进入用户的待办视野

**用户原创理论/洞见 → 创建 ThinkingDeposit**：
当用户表达了原创理论或跨域洞见，直接按 Deposit 流程处理（创建图谱实体 + 写入内容文件到 `output/deposits/`），不再使用 UserTheory 实体类型。

**创建 CrossDomainLink**（跨域关联发现）：
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

### 第三步：歧义检测

将用户的表述与节点的标准定义进行语义比对：

| 类型 | 说明 |
|------|------|
| `concept_confusion` | 两个相近概念混为一谈 |
| `causal_inversion` | 因果关系颠倒 |
| `overgeneralization` | 过度泛化 |
| `detail_omission` | 关键细节遗漏导致理解偏差 |
| `outdated_info` | 引用了过时的信息 |

**处理原则**：
- 宽容为先——表述不精确但本质理解正确时，不标记
- 将歧义记录到节点的 `misconceptions` 数组
- **不在此步骤直接纠正用户**——在交互结束的反馈环节温和指出
- 如之前记录的歧义已被用户自行修正，更新 `corrected_at`

### 第四步：生成 session_memory 条目

按 `templates/session_record.json` 格式组装：
```json
{
  "ts": "ISO 8601",
  "interaction_type": "pass_note|write_note|chat",
  "domains_touched": ["领域ID列表"],
  "input_summary": "1-2句话摘要",
  "knowledge_extracted": [{"domain": "ID", "node": "名称", "action": "create|deepen"}],
  "thinking_notes": "思考要点和独立见解摘要",
  "cross_domain_links": [],
  "deposits_created": [],
  "duration_min": 25,
  "ito_classification": {"input": 0.3, "think": 0.6, "output": 0.1}
}
```

**写入规则**：session_memory 按周分文件存储在 `memory/session_memory/` 目录下，文件名格式为 `{YYYY}-W{WW}.jsonl`（如 `2026-W10.jsonl`）。写入前：
1. 根据当前日期计算 ISO 周数
2. 检查对应周文件是否存在，不存在则创建
3. 追加写入对应周文件（单行 JSON，append-only）

### 可视化同步

图谱变更完成后，执行 `python3 scripts/build_visualization.py` 重新生成 `visualization.html`。

### 第五步：反馈

向用户给出即时反馈：
- 确认本次交互的价值："这次你深入了{知识点}，图谱中新增了{N}个节点。"
- 如发现跨域关联，立即提示
- 对 severity ≥ moderate 的歧义温和指出
- 如创建了 Deposit，告知用户

## 输出

- 图谱变更日志（新增/更新的节点和边）
- session_memory 条目
- Deposit 文件（如有）
- 反馈文字
