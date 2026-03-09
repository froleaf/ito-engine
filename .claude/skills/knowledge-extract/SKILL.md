---
name: knowledge-extract
description: 从自由文本中提取结构化知识信息，为图谱更新提供数据。由 chat/pass-note/write-note 在交互过程中或结束时调用。
user-invocable: false
---

## 角色

从自由文本（笔记、对话摘要）中提取结构化知识信息，为后续的图谱更新提供数据。

## 输入

- 自由文本内容（笔记正文或对话摘要）
- `ontology/_meta/domains.md`：已注册领域列表
- `ontology/ontology.jsonld`：统一知识图谱（通过 grep 按需查询匹配，不全览）

## 处理逻辑

### 第一步：领域归属判断

1. 读取 `ontology/_meta/domains.md` 获取已注册领域列表
2. 分析文本内容，确定涉及哪些已注册领域
3. 如涉及未注册领域，标记为 `new_domain_candidate`
4. 一段文本可能同时涉及多个领域

### 第二步：知识点提取

从文本中识别以下类型的知识元素：

| 类型 | 说明 | 示例 |
|------|------|------|
| `concept` | 概念/理论/框架 | "具身认知理论" |
| `fact` | 客观事实/数据 | "GPT-4 有 1.8 万亿参数" |
| `person` | 相关人物 | "侯世达" |
| `material` | 具体学习材料（注意识别阅读状态，见下方） | "《哥德尔、艾舍尔、巴赫》" |
| `method` | 方法/技术/工具 | "费曼学习法" |
| `opinion` | 用户的独立见解 | "我认为...本质上是同一件事" |
| `original_thinking` | 用户的原创理论/框架（将作为 ThinkingDeposit 处理） | "教育本质上是知识基于时间的传播" |

**材料阅读状态识别**：

当提取到 `material` 类型时，同时判断用户的阅读/学习状态：

| 用户表述 | readingStatus | 示例 |
|----------|--------------|------|
| "我在读…"、"最近在看…"、"刚开始学…" | `in_progress` | "我在读《系统之美》" |
| "我读完了…"、"看完了…"、"学完了…" | `completed` | "这本看完了" |
| "我之前读过…"、"以前看过…" | `completed` | "我之前读过这本" |
| "暂时放下了"、"没继续看" | `paused` | "《GEB》太难了暂时放下" |
| 只是提到材料名，未说明状态 | 不标记状态 | "《GEB》里提到过这个" |

同时提取进度信息（如有）：`progress` 字段，如"读到第3章"、"看了一半"。

### 第三步：术语翻译

对每个 `concept` / `method` 类型知识点：
1. 将用户的口语描述映射为**标准学术术语**
2. 保留用户原始表述作为 `user_expression`

### 第四步：与统一图谱匹配

对每个提取到的知识点：
1. 用学术术语 grep `ontology/ontology.jsonld`（搜索 name、description、aliases 字段）
2. 如已存在 → 标记为 `deepen`（深化），记录已有节点 @id
3. 如不存在 → 标记为 `create`（新建）
4. 如与已有节点矛盾 → 标记为 `conflict`（冲突）

### 第五步：跨域关联检测

1. 如果文本同时涉及多个领域的知识点
2. 检查是否存在逻辑上的关联（类比、同构、因果、互补）
3. 如发现关联，生成 `cross_domain_link` 候选

### 第六步：隐性认知检测

除了用户**显性谈论**的话题，还要识别用户在思考过程中**隐性调用**的知识工具。

**区分：**
- 显性话题："我们讨论一下奥卡姆剃刀这个原理" → 用户在**谈论**奥卡姆剃刀
- 隐性调用："删繁就简，奥卡姆剃刀" → 用户在**使用**奥卡姆剃刀做决策，讨论话题其实是架构设计

**检测什么：**
- 用户用某个概念/模型/方法论来**支撑决策或分析**，而不是在讨论这个概念本身
- 用户的推理方式明显体现了某个学科的思维范式（如系统思维、数据思维、辩证法）
- 用户无意中运用了某个领域的专业方法而没有点名

**记录方式：**
- 标记为 `implicit_method_use` 类型
- 记录：被调用的知识工具名称 + 它所属的领域 + 用户用它做了什么
- 这构成了该知识点 depth 升级的证据（"能应用"比"能复述"更深）

**高门槛原则：**
- **只记录明确、显著的隐性调用**——用户明显在用某个模型/方法做判断
- **不记录模糊的影子**——不要因为用户说了"系统"就认为在用系统论
- 如果不确定，就不记录。宁可漏掉，不可乱标

**必须反馈给用户：**
- 检测到隐性认知后，**一定要在交互反馈中明确告知用户**："我注意到你刚才在用{X}来做{Y}的判断，这说明{X}对你来说已经是一个内化的思维工具了。"
- 让用户确认或纠正——即使判断错了，用户也能及时说"不是，我没有用那个"
- 只有用户确认后（或未否认）才写入图谱

### 第七步：I/T/O 分类

判断本次交互的 I/T/O 权重：
- **Input**：用户引用外部来源（书、文章、课程）的内容占比
- **Think**：用户的思考、分析、评论、类比占比
- **Output**：用户在组织可分享的完整论述占比

## 图谱查询方式

- 按 `@id` 查节点：`grep "@id.*node_id" ontology/ontology.jsonld`
- 按 `@type` 筛选：`grep "@type.*DomainRoot" ontology/ontology.jsonld`
- 按关键词搜索：`grep -i "关键词" ontology/ontology.jsonld`
- 按边查关联：`grep "parentBranch.*domain_id" ontology/ontology.jsonld`
- **禁止**一次性读取整个 `ontology.jsonld`

## 输出

```json
{
  "domains_touched": ["domain_id_1", "domain_id_2"],
  "new_domain_candidates": [],
  "knowledge_points": [
    {
      "type": "concept",
      "domain": "domain_id",
      "academic_term": "标准学术术语",
      "user_expression": "用户原始表述",
      "action": "create|deepen|conflict",
      "existing_node_ref": "如有匹配的已有节点@id"
    }
  ],
  "materials": [
    {
      "name": "材料名称",
      "materialType": "book|video_course|article|...",
      "readingStatus": "in_progress|completed|paused|null",
      "progress": "进度描述（如有）",
      "domain": "domain_id",
      "action": "create|deepen"
    }
  ],
  "user_insights": [],
  "original_thinkings": [],
  "cross_domain_links": [],
  "ito_classification": { "input": 0.3, "think": 0.6, "output": 0.1 }
}
```
