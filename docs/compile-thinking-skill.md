# 编译分析报告

## 一、认知工具箱盘点

mental_model 节点（depth ≥ 理解，共 10 个）：

| 节点 | 名称 | depth | 领域 |
|------|------|-------|------|
| st_mece_principle | MECE原则 | 可教授他人 | 系统论 |
| da_data_consumer_layers | 数据消费者三层模型 | 可教授他人 | 数据分析 |
| da_north_star_decomposition | 北极星指标拆解四步法 | 可教授他人 | 数据分析 |
| cs_marr_three_levels | Marr 三层级框架 | 可教授他人 | 认知科学 |
| cs_act_r_model | ACT-R 认知架构 | 可教授他人 | 认知科学 |
| cs_chunking_miller | 分块与抽象 7±2 | 可教授他人 | 认知科学 |
| st_three_problem_domains | 问题的三个域 (Weinberg) | 可教授他人 | 系统论 |
| ps_grit_theory | 坚毅理论 | 有独立见解 | 心理学 |
| ps_growth_mindset | 成长型思维 | 有独立见解 | 心理学 |
| cs_abstraction_ladder | 抽象阶梯 | 有独立见解 | 认知科学 |

methodology 节点（1 个）：
- ps_deliberate_practice：刻意练习，depth=理解

## 二、appliedIn 记录

目前图谱中没有任何 appliedIn 调用日志。这意味着虽然你有丰富的思维工具，但系统还没有记录到你在对话中实际调用它们的场景。

## 三、跨域连接习惯

16 条 CrossDomainLink，偏好模式：

| link_type | 数量 | 含义 |
|-----------|------|------|
| structural_isomorphism（结构同构） | 6 | 最偏爱——找不同领域底层结构的相似性 |
| application（应用迁移） | 5 | 把一个领域的知识应用到另一个 |
| confirmed/theoretical_integration | 3 | 理论融合 |
| complementary | 2 | 互补视角 |

最频繁的跨域路径：认知科学 ↔ AI（4条）、认知科学 ↔ 教育（2条）、心理学 ↔ 经济学（2条）

## 四、原创框架（ThinkingDeposit 中包含可操作思维流程的）

从 24 个 ThinkingDeposit 中，有明确步骤/框架结构的：

1. td_three_level_decision — 人生决策三层级（显著重大→不起眼小决策→元决策）
2. td_model_taxonomy — 模型分类三维（流程/层级/维度）
3. td_cognitive_four_components — 信息处理四器（感应/处理/存储/效应）
4. td_iceberg_model_learning — 冰山模型学习法（术源于道）
5. td_motivation_five_sources — 动机来源五维框架
6. td_subjectivity_four_stages — 主体性发展四阶段
7. td_compression_progress — ABCD学习者分类
8. td_procrastination_dynamics — 拖延动因动力学（驱动力 vs 阻碍力）
9. td_practice_theory_integration — 实践论与冰山渗透模型

## 五、数据充分性判断

| 条件 | 实际情况 | 状态 |
|------|----------|------|
| mental_model ≥ 3 | 10 个 | ✅ 充分 |
| appliedIn ≥ 2 条 | 0 条 | ❌ 不足 |
| CrossDomainLink ≥ 1 | 16 条 | ✅ 充分 |

关键缺口：没有 appliedIn 记录，无法编译"通用框架的个人版"和"决策模式"类脚本——这两类需要实际调用证据。

但可以编译的类型有：
- 原创思维框架（来自 ThinkingDeposit）
- 跨域分析路径（来自 CrossDomainLink 模式）

---

## 可编译的思维脚本（草案）

### 脚本1：ts_three_level_decision — 三层决策分析法

**适用场景：** 面对人生重大选择、分析决策失误原因、审视决策质量
**来源：** td_three_level_decision + link_decision_stock_war_life
**步骤：**
1. 识别当前问题属于哪一层（显著重大 / 不起眼的小决策 / 元决策）
2. 如果是显著重大决策——选项有限，列出选项和可预测影响
3. 如果是小决策——注意：自由度最高但后果最难预估，一次败仗可吞噬百次胜仗
4. 追问元决策层：是什么"决策逻辑的决策"在支配我？哪些认知参与了/被排除了？
5. 检查：上层决策的可决策范围是否被下层限制住了？

### 脚本2：ts_model_building — 三维建模法

**适用场景：** 搭建分析框架、整理知识结构、理解复杂系统
**来源：** td_model_taxonomy + st_mece_principle + td_cognitive_four_components
**步骤：**
1. 判断当前问题适合哪种模型：
   - 流程模型（事物在同一层如何流动？）→ 流程图
   - 层级模型（事物如何向上抽象/向下分解？）→ 模块化/树形
   - 维度模型（事物可沿哪些维度拆解？）→ 四象限/星型
2. 用 MECE 检验：独立不重叠、穷尽不遗漏
3. 必要时叠加第二维：流程 × 层级 是你的习惯组合
4. 用信息处理四器检验完整性：感应→处理→存储→效应，是否有被忽略的环节？

### 脚本3：ts_cross_domain_isomorphism — 跨域结构同构发现法

**适用场景：** 发现不同领域的底层共性、产生创造性洞察、写跨学科分析
**来源：** 16条 CrossDomainLink（6条 structural_isomorphism）+ cs_abstraction_ladder + td_compression_progress
**步骤：**
1. 将当前概念用抽象阶梯提升到 L4-L5（抽象原理层），剥离领域特有表述
2. 寻找结构同构：另一个领域是否有相同的"骨架"？
   - 你的高频路径：认知科学 ↔ AI、认知科学 ↔ 教育、心理学 ↔ 经济学
3. 验证同构深度：是表面类比（形似）还是结构一致（力的方向、反馈回路一致）？
4. 如果结构一致——检查是否一个领域有成熟解法可以迁移到另一个
5. 压缩表达：用一句话概括这个同构关系（你擅长这一步）

### 脚本4：ts_motivation_diagnosis — 动机与行动力诊断法

**适用场景：** 拖延时自检、评估是否值得投入、理解他人的动力缺失
**来源：** td_motivation_five_sources + td_procrastination_dynamics + ps_grit_theory
**步骤：**
1. 动机五维扫描：内在需求 / 个人优势 / 社会认可 / 有用 / 价值观——哪些被点亮？
2. 核心三维聚焦：需求 + 有用 + 价值观（其余两个可暂时搁置）
3. 如果动机存在但行动停滞——切换到力学分析：
   - 驱动力：问题推 / 目标拉 / 他人推 / 他人拉，哪个在起作用？
   - 阻碍力：主观（精神健康）还是客观（事情难度/卡点）？
4. 找"钩子"：能改变现状的最小干预点（作用于驱动力或阻碍力）
5. Grit 校验：这件事是"指南针"（长期方向）还是"烟花"（短期兴奋）？

---

以上是 4 个可编译的思维脚本草案。还有几个 ThinkingDeposit（主体性四阶段、冰山学习法、实践论渗透模型等）也有编译潜力，但它们更偏向"认知发展理论"而非"面对问题的操作步骤"，暂不强行编译。
