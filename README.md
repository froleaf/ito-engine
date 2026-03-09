# ITO Engine — 输入·思考·输出 个人知识管理 Agent

一个纯文件系统驱动的个人知识管理 Agent 架构。帮助你在多个关注领域中系统地**摄入知识、沉淀思考、孵化输出**。

只要将本仓库接入任意大语言模型（Claude、GPT 等），即可启动完整的 ITO 闭环。所有状态以 JSON / JSON-LD / JSONL / Markdown 存储，零外部依赖。

---

## 快速开始

### 0. 启动 Agent

> **每次打开项目后，输入 `/ito` 启动 Agent。**
>
> Agent 会检查系统状态：首次使用自动引导冷启动，已初始化则进入待命模式。
> 不输入 `/ito` 时，Agent 只是普通的 AI 助手，不会执行 ITO 引擎的任何逻辑。

### 1. 接入

| 方式 | 说明 |
|------|------|
| **Claude Code / Cursor**（推荐） | 将本仓库作为工作目录打开，AI 直接读写文件。技能已注册为 `.claude/skills/` 下的 slash command |
| **自定义后端** | 读取 `.claude/skills/*/SKILL.md` 作为 system prompt，调用 LLM API，结果写入 `memory/` |

### 2. 冷启动

启动后首次使用时，Agent 会自动引导**冷启动**流程：

1. 通过轻松对话了解你的 2-4 条**主线目标**（你最想推进的方向）
2. 从主线出发梳理涉及的关注领域（建议 3-7 个）
3. 为每个领域创建骨架知识本体
4. 在统一图谱中初始化你的认知数据

冷启动对话完成后，如果你有历史笔记要导入，使用 `/bootstrap` 将过去的思考灌入系统（支持文件批量、对话输入和链接）。灌入完成后用 `/plan` 生成首次计划，系统正式启用。

`/bootstrap` 不仅限于冷启动阶段——日后翻出旧笔记时同样可以用它补录，图谱正常更新但不影响当前的 PDCA 监测回路。

### 3. 日常使用

冷启动后，Agent 默认处于**待命模式**。你可以直接做工具性操作，不会产生 session 记录：

- **`/plan`** — 查看/调整周度计划
- **查看图谱** — 在浏览器中打开交互式知识图谱可视化
- **查看沉淀产出** — 浏览你的 Deposit 和输出候选
- **`/review`** — 评价一篇文章或你自己的作品（不影响知识系统）
- **`/bootstrap`** — 灌入历史笔记、旧文章、聊天记录
- **`/weekly-review`** — 发起周度复盘
- **`/reset`** / **`/reload`** — 系统重置或从存档重建

当你需要深度交流时，显式说出以下关键词进入**会话模式**（会触发知识提取和 session 记录）：

- **"传笔记"**：将 `.md` 文件放入 `inbox/notes/`，Agent 读取并提取知识
- **"写笔记"**：直接口述或打字，Agent 帮你整理成结构化笔记
- **"聊天"**：自由聊天，Agent 作为苏格拉底式思考伙伴，追问、挑战、帮助深化

你也可以在会话中直接**分享链接**，Agent 会自动读取内容并纳入知识处理流程。

---

## 核心概念

### I-T-O 三维度

| 维度 | 含义 | 典型行为 |
|------|------|----------|
| **Input** | 知识摄入 | 读书笔记、文章摘要、课程记录 |
| **Think** | 思考沉淀 | 对话中的分析、追问、跨域类比 |
| **Output** | 输出孵化 | 写文章、做分享、产出作品 |

Agent 会追踪每次交互的 I/T/O 比例，帮助你保持"知识饮食均衡"。

### 统一知识图谱

```
统一知识图谱（骨架→渐进生长，节点直接携带个人认知数据）
     学科知识谱系 + 用户认知状态 + 跨域连接 + 原创理论
          ↑
    你的输入触发构建，个人元数据直接标注在节点上
```

- **统一图谱** (`ontology/ontology.jsonld`)：所有关注领域的知识图谱 + 个人认知数据（JSON-LD 图数据库）。不是预建的完整知识树，而是从你的交互中渐进生长。节点直接携带深度标签（浅读→理解→有独立见解→可教授他人）、独特见解、认知歧义等个人元数据。AI 通过 `@id` grep 查询定位节点

### Skill 体系

Skill 分三类——**主线入口**（用户直接触发）、**被调用**（由其他 skill 调用）、**系统**（管理操作）：

```
/cold-start ──→ ontology-init（构建领域骨架）
            ──→ 引导用户 /bootstrap 或 /plan

/bootstrap ──→ knowledge-extract + knowledge-process（图谱生长 + Deposit 创建）
           ╳   不写 session_memory，不触发 plan

/chat、/pass-note、/write-note
            ──→ [对话中] knowledge-extract（提取结构化知识）
            ──→ [结束时] knowledge-process（图谱更新+歧义检测+session记录）
                            └──→ Deposit 创建（如有成型产出）

/weekly-review ──→ 在读材料跟进（grep in_progress Material）
               ──→ /plan（更新下周计划）
               ──→ dormant-check（沉寂领域检查）

/review ──→ 只读评价（事实核查 + 逻辑核查 + 内容质量 + 个人相关性）
        ╳   不写图谱、不写记忆，可选存档到 output/reviews/

/compile-thinking ──→ 扫描 mental_model appliedIn 日志 + CrossDomainLink + ThinkingDeposit
                  ──→ 编译个人思维脚本 → output/thinking_scripts/
```

### 输出体系：Deposit

产出分两类：

- **KnowledgeDeposit**（知识沉淀）：用户将学到的知识结构化整理后的产物（如读书笔记、知识体系梳理）
- **ThinkingDeposit**（思考沉淀）：用户的原创思考、模型、框架

每份 Deposit 在图谱中有实体节点（带关系边指向相关知识节点），实际内容存为文件（`output/deposits/`），节点里存路径可导航到原文。状态分 `deposited`（仅沉淀）和 `published`（已对外输出）。

同一主题的内容反复出现时，合并到已有 Deposit 实体，不重复创建。

尚未成型的想法不单独追踪——通过图谱节点上的 `outputPotential` 标记即可动态汇总候选。

### 学习材料追踪

当你提到正在读的书或在学的课程时，Agent 会创建 Material 实体并标记阅读状态：

| 状态 | 含义 | 触发 |
|------|------|------|
| `in_progress` | 正在阅读/学习 | "我在读…"、"最近在看…" |
| `completed` | 已读完 | "读完了"、"看完了" |
| `paused` | 暂停 | "暂时放下了" |
| `abandoned` | 不再继续 | "不打算读了" |

周度复盘时，Agent 会主动询问在读材料的进展，帮你追踪阅读节奏。

### 知识图谱可视化

输入"查看图谱"，Agent 会在浏览器中打开交互式力导向图，展示你的领域、分支、知识节点、材料、沉淀产出和跨域连接。图谱数据每次变更后自动同步。

### 内容评价（`/review`）

对任意内容进行多维度评价——事实核查、逻辑核查、内容质量、与你的知识体系的相关性。可以评价外部文章，也可以评价你自己的作品。**对知识系统严格只读**，不会影响你的图谱和记忆。

### 思维编译（`/compile-thinking`）

随着图谱积累，Agent 会追踪你在思考和决策中**实际使用**了哪些思维工具（通过隐性认知检测 + 用户确认）。`/compile-thinking` 从这些调用日志中提炼出你的个人思维脚本——不是教科书上的通用方法，而是**你自己的思考方式的显性化**。

编译来源：
- 你内化的 mental_model 和 methodology 的实际调用记录（`appliedIn`）
- 你习惯的跨域连接路径（CrossDomainLink 模式）
- 你的原创框架（ThinkingDeposit）

编译产物是三层结构：
- **图谱实体**（`ThinkingScript` 节点）— 存元数据和场景标签
- **内容文件**（`scripts/thinking/*.md`）— 存实际的思维步骤
- **场景索引**（`ontology/_meta/thinking_scenarios.md`）— 轻量路由表

`/review` 评价内容时会自动匹配场景索引，将适用的思维脚本作为分析视角注入评价。`/chat` 聊天中遇到匹配场景也会温和建议。

---

## 目录结构

```
ito-engine/
│
├── agent_profile.json              # Agent 全局配置（人格、行为规则）
│
├── ontology/                       # ═══ 统一知识图谱（领域知识 + 个人认知）═══
│   ├── ontology.jsonld             #   统一图谱（JSON-LD 图数据库）
│   └── _meta/
│       └── domains.md              #   领域名称索引
│
├── memory/                         # ═══ 分层记忆 ═══
│   ├── goal_memory.jsonl           #   主线目标（2-4条，关联多领域）
│   ├── session_memory/             #   每次交互记录（按周分文件）
│   │   └── {YYYY}-W{WW}.jsonl     #     如 2026-W10.jsonl
│   ├── plan_memory.jsonl           #   周度计划（精力分配+I/T/O比例）
│   ├── milestone_memory.jsonl      #   周度总结
│   ├── rlhf_memory.jsonl           #   Agent 建议效果追踪
│   └── preference_memory.jsonl     #   用户偏好
│
├── inbox/                          # ═══ 输入收件箱 ═══
│   ├── notes/                      #   放入待处理笔记（.md）
│   ├── bootstrap/                  #   放入历史内容（/bootstrap 灌入用）
│   ├── processed/                  #   已处理的笔记归档
│   └── conversations/              #   对话原文存档（含冷启动对话）
│
├── output/                         # ═══ 输出体系 ═══
│   ├── deposits/                   #   沉淀产出文件（知识沉淀 + 思考沉淀）
│   ├── reviews/                    #   内容评价存档（/review 可选保存）
│   └── drafts/                     #   草稿文件
│
├── visualization.html              # 知识图谱可视化（自动生成，勿手动编辑）
│
├── _init/                          # ═══ 初始状态快照（用于重置）═══
│
├── .claude/skills/                  # ═══ 技能层（Claude Code slash command）═══
│   ├── ito/SKILL.md                #   主入口：待命模式 + 路由
│   ├── cold-start/SKILL.md         #   冷启动：认知版图初始化
│   ├── chat/SKILL.md               #   聊天模式
│   ├── pass-note/SKILL.md          #   传笔记模式
│   ├── write-note/SKILL.md         #   写笔记模式
│   ├── plan/SKILL.md               #   计划查看/调整
│   ├── weekly-review/SKILL.md      #   周度复盘
│   ├── bootstrap/SKILL.md          #   历史内容灌入
│   ├── review/SKILL.md             #   内容评价（只读，不影响知识系统）
│   ├── compile-thinking/SKILL.md   #   思维编译（从图谱编译个人思维脚本）
│   ├── reload/SKILL.md             #   从存档重新加载
│   ├── reset/SKILL.md              #   项目重置
│   ├── knowledge-extract/SKILL.md  #   [内部] 知识提取
│   ├── knowledge-process/SKILL.md  #   [内部] 知识处理
│   ├── ontology-init/SKILL.md      #   [内部] 领域骨架初始化
│   └── dormant-check/SKILL.md      #   [内部] 沉寂领域检查
│
├── scripts/                        # ═══ 脚本 ═══
│   ├── build_visualization.py      #   从图谱生成 visualization.html
│   └── thinking/                   #   个人思维脚本（/compile-thinking 生成）
│
└── templates/                      # ═══ 数据模板 ═══
    ├── session_record.json
    ├── plan_record.json
    ├── milestone_record.json
    ├── rlhf_record.json
    ├── diet_report.md
    ├── domain_scaffold.jsonld
    └── visualization_template.html  #   D3.js 可视化模板
```

---

## 链接输入

在任何交互模式中，你都可以直接给 Agent 发送 URL 链接。Agent 会自动读取内容，根据你的表述判断如何处理：

| 你的表述 | Agent 理解为 | 处理方式 |
|----------|------------|----------|
| "我读了这个…"、"推荐这篇" | 外部阅读材料 | 提取知识，创建 Material 实体挂载到本体 |
| "这是我的日记"、"我和 AI 的讨论记录" | 你自己的产出 | 提取知识点和见解，不创建 Material |
| "帮我把这个挂载到本体上" | 指定挂载 | 判断挂载位置，创建 Material |

如果链接无法读取，Agent 会明确告知，请你口述要点——绝不会用幻觉替代。

---

## 重置与重新加载

### 重置（`/reset`）

| 模式 | 适用场景 | 保留什么 | 清除什么 |
|------|----------|----------|----------|
| **保留内容重置** | 自己用，想用新逻辑重新处理 | 笔记（processed 移回 notes）、对话存档（含冷启动） | 图谱、记忆、输出 |
| **完全重置** | 交付给新用户 | 无 | 全部数据 |

### 重新加载（`/reload`）

保留内容重置后，从存档重建整个系统：
1. 识别并重放冷启动对话 → 恢复领域骨架和认知数据
2. 重放 `inbox/bootstrap/` 中的历史内容（走 bootstrap 逻辑）
3. 按时间顺序重放其他对话存档
4. 按时间顺序处理笔记
5. 生成计划、同步可视化、汇总报告

---

## 设计原则

| 原则 | 说明 |
|------|------|
| **纯文件即数据库** | 所有状态以 JSON/JSONL/JSON-LD/Markdown 存储，零外部依赖 |
| **Skills 即 Prompt** | 每个技能是独立的提示词文件，包含输入输出契约，LLM 按需调用 |
| **本体渐进生长** | 不预建完整知识树，从用户交互中按需构建 |
| **统一图谱** | 领域知识、个人认知、跨域连接、用户理论全在一个图中 |
| **记忆只追加** | JSONL append-only，保证数据安全与可审计。session_memory 按 ISO 周分文件存储，避免单文件膨胀 |
| **多域并行** | 支持同时管理多个关注领域，统一图存储 |
| **输出导向** | 不仅记录输入和思考，更主动追踪和孵化可输出的内容 |
