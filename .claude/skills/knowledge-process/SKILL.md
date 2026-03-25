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

## 规范参考

写入图谱前，必须参照以下规范文件（同目录下）：
- [schema.md](schema.md)：合法实体类型和边属性（**不得自创字段**，否则不生成可视化边）
- [material_spec.md](material_spec.md)：Material 信息补全和阅读状态管理
- [deposit_spec.md](deposit_spec.md)：沉淀产出判断标准、创建流程、查阅规则

## 处理逻辑

### 第一步：图谱扩展（领域知识构建）

对知识提取结果中标记为 `create` 的新知识点，执行**翻译-构建-挂载三步法**：

1. **翻译用户输入**：将口语/俗称映射到标准学术术语，保留原始表述作为 `aliases`。
   **命名质量是图谱激活 AI 深层知识的关键**——术语越精准，AI 在后续对话中被唤醒的知识区域越准确。翻译时执行以下检查：
   - **学科归属验证**：该术语是否属于用户所谈论的学科？避免跨学科术语错位（如把认知科学概念命名为哲学术语）
   - **粒度匹配**：用户谈论的是一个大领域（如"系统论"）还是一个具体机制（如"负反馈回路"）？节点命名要匹配实际讨论粒度
   - **消歧**：如果一个术语在多个学科中有不同含义（如"本体"在哲学 vs 计算机科学），节点名或 description 中必须明确是哪个语境
2. **grep 检查是否已存在**：`grep "学术术语" ontology/ontology.jsonld`
3. **构建知识谱系**：
   - 基于权威学术定义构建节点，追加到 @graph
   - **所有新节点必须标注 `createdAt`**（当前时间 ISO 8601）
   - 建立边关系（belongsTo、isA、prerequisite、relatedTo 等）——合法边属性见 [schema.md](schema.md)
   - 同时创建 3-5 个同级/子级节点
4. **创建 Material 实体（如有）**：调用 `add-material` skill 的流程（查重→信息补全→边关系→写入→todo 联动→rebuild）。详见 `.claude/skills/add-material/SKILL.md`，信息补全规范见 [material_spec.md](material_spec.md)
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

### 第三步：沉淀产出处理

按 [deposit_spec.md](deposit_spec.md) 执行 Deposit 判断、创建、查阅和联动。

### 第四步：歧义检测

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

### 第五步：生成 session_memory 条目

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

### 第六步：反馈

向用户给出即时反馈，遵循金字塔结构：

1. **结论先行**：一句话概括本次交互的核心认知变化（不是"新增了 N 个节点"，而是"你对{主题}的理解从{A}推进到了{B}"）
2. **归类展开**：按类型分组列出变更——
   - 知识扩展：新增/深化了哪些节点
   - 认知成长：depth 升级、新 userInsight
   - 跨域发现：新建的 CrossDomainLink
   - 沉淀产出：新建的 Deposit
3. 如发现歧义（severity ≥ moderate），在反馈末尾温和指出

## 输出

- 图谱变更日志（新增/更新的节点和边）
- session_memory 条目
- Deposit 文件（如有）
- 反馈文字
