---
name: compile-thinking
description: 从知识图谱中编译用户的个人思维方式——分析 mental_model 调用模式、跨域连接习惯和原创框架，生成 ThinkingScript 实体和思维脚本文件，维护场景索引供 /review 和 /chat 路由调用。
---

## 角色

认知编译器。从用户的知识图谱中提取思维模式，将声明式的"我知道这些工具"编译为程序式的"面对这类问题，按这个步骤思考"。

**编译 ≠ 发明**：不是凭空创造思维方式，而是从用户已有的认知行为中**提炼和显性化**。

## 编译产物的三层结构

| 层 | 位置 | 作用 |
|----|------|------|
| **图谱实体** | `ontology/ontology.jsonld` 中的 `ThinkingScript` 节点 | 存元数据、场景标签、来源边，供 grep 查询 |
| **内容文件** | `scripts/thinking/{ts_id}.md` | 存实际的思维步骤，供 Agent 读取并执行 |
| **场景索引** | `ontology/_meta/thinking_scenarios.md` | 轻量路由表，`/review` 和 `/chat` 通过 grep 匹配场景 |

## 数据来源

| 数据 | 含义 | 查询 |
|------|------|------|
| `nodeRole: mental_model` 节点 | 用户内化的思维工具 | `grep "mental_model" ontology/ontology.jsonld` |
| `nodeRole: methodology` 节点 | 用户的工作方法 | `grep "methodology" ontology/ontology.jsonld` |
| `appliedIn` 记录 | 思维工具的实际调用日志 | `grep "appliedIn" ontology/ontology.jsonld` |
| `CrossDomainLink` 实体 | 用户习惯的跨域连接路径 | `grep "CrossDomainLink" ontology/ontology.jsonld` |
| `ThinkingDeposit` 实体 | 用户的原创框架 | `grep "ThinkingDeposit" ontology/ontology.jsonld` |
| `depth ≥ 有独立见解` 的节点 | 深度内化的知识 | `grep "有独立见解\|可教授他人" ontology/ontology.jsonld` |

## 处理逻辑

### 第一步：扫描认知工具箱

1. grep 所有 `nodeRole: mental_model` 和 `nodeRole: methodology` 的节点
2. 对每个工具节点，提取：name、depth、userInsight、appliedIn 记录
3. 按 `appliedIn` 记录数量排序——调用次数多的是核心工具
4. 按 `depth` 筛选——至少"理解"级别的才有编译价值

### 第二步：分析调用模式

对每个有足够 appliedIn 记录的工具（≥ 2 条），分析：

1. **场景聚类**：提取所有 `context` 字段，归纳场景类别
   - 例：奥卡姆剃刀 → "设计决策"、"信息筛选"
2. **决策模式**：提取所有 `decision` 字段，归纳决策模式
   - 例：奥卡姆剃刀 → "在多个方案中选择最简洁的"
3. **组合模式**：同一次交互中是否有多个工具一起使用
   - 例：系统思维 + 数据驱动 经常组合

### 第三步：分析跨域连接习惯

1. grep 所有 CrossDomainLink，提取 `link_type` 和连接的领域
2. 统计偏好的连接方式（类比多还是同构多？哪些领域间最频繁？）
3. 这构成用户的"跨域思维签名"

### 第四步：提取原创框架

1. grep 所有 ThinkingDeposit，读取导读部分
2. 识别其中包含可操作思维流程的（有步骤，不只是观点）
3. 这些是"思维脚本草稿"

### 第五步：编译思维脚本

将以上分析综合，为每个可编译的思维模式生成三样东西：

**1. 图谱实体**（追加到 ontology.jsonld @graph）：
```json
{
  "@type": "ThinkingScript",
  "@id": "ts_{short_id}",
  "name": "脚本名称",
  "description": "一句话描述这个思维方式做什么",
  "scenarioTags": ["设计取舍", "方案选择", "简化"],
  "derivedFrom": ["来源 mental_model / methodology / ThinkingDeposit 的 @id"],
  "contentPath": "scripts/thinking/ts_{short_id}.md",
  "compiledAt": "ISO 8601",
  "appliedInCount": 5
}
```

**2. 内容文件**（写入 `scripts/thinking/ts_{short_id}.md`）：
```markdown
# {脚本名称}

> **适用场景**：{什么类型的问题适合用这个思维方式}
> **来源**：{基于哪些 mental_model / methodology / ThinkingDeposit}
> **调用证据**：{用户实际使用过的场景摘要，来自 appliedIn}
> **编译时间**：{日期}

## 步骤

1. {第一步}
2. {第二步}
3. ...

## 你的独特视角

{来自 userInsight 和 ThinkingDeposit 的个人化注解——不是教科书怎么说，而是你怎么用}
```

**3. 更新场景索引**（追加到 `ontology/_meta/thinking_scenarios.md`）：
```
| 设计取舍、方案选择、简化 | ts_occam_decision | 奥卡姆剃刀决策法 |
```

**脚本类型**：

| 类型 | 来源 | 示例 |
|------|------|------|
| **通用框架的个人版** | 成熟方法论 + appliedIn + userInsight | "你的系统思维：先找反馈回路，再匹配基模，最后找杠杆点" |
| **跨域分析路径** | CrossDomainLink 模式 | "认知科学×系统论分析法：先用类比找结构，再用系统论看动力学" |
| **原创思维框架** | ThinkingDeposit | "知识时间传播分析法：区分空间维度传播和时间维度传播" |
| **决策模式** | 多个 mental_model 的 appliedIn 组合 | "设计决策：先奥卡姆剃刀删繁，再系统思维看全局" |

### 第六步：用户审阅

1. 将编译结果输出给用户
2. 用户可以：确认、修改步骤、调整场景标签、删除、合并
3. **只有用户确认后才写入图谱和文件**

### 第七步：增量更新

如果图谱中已有 ThinkingScript 实体：
1. grep 已有的 ThinkingScript，读取 contentPath 的内容
2. 检查是否有新的 appliedIn 记录、新的 CrossDomainLink 或 ThinkingDeposit
3. 对有新数据的脚本：更新内容文件（补充调用证据、微调步骤）、更新图谱实体的 `compiledAt` 和 `appliedInCount`
4. 如有新的可编译模式 → 走第五步创建新脚本
5. 如场景标签有变化 → 更新 `thinking_scenarios.md`
6. 向用户报告变化

## 数据充分性判断

| 条件 | 最低要求 | 不足时 |
|------|----------|--------|
| mental_model 节点 | ≥ 3 个 depth ≥ 理解 | 输出**认知工具箱盘点**，不强行编译 |
| appliedIn 记录 | 至少 1 个工具有 ≥ 2 条 | 建议多在聊天中使用思维工具 |
| CrossDomainLink | ≥ 1 条 | 跨域分析路径无法编译，其他类型正常 |

## 命名规则

| 实体 | ID 前缀 | 示例 |
|------|---------|------|
| ThinkingScript | `ts_` | `ts_occam_decision` |

内容文件名与 @id 一致：`scripts/thinking/ts_occam_decision.md`

## 约束

- **不凭空发明**——每个脚本必须有图谱数据支撑，列出证据来源
- **用户审阅优先**——编译结果必须经用户确认才写入
- **场景索引必须同步**——每次新增或修改 ThinkingScript，同步更新 `thinking_scenarios.md`
