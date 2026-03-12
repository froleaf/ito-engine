# AI滑雪私人教练系统：知识图谱×PDCA×多维评估

> **类型**：思考沉淀
> **状态**：沉淀（工作方案）
> **涉及领域**：AI Agent、教育、健康与情绪健康
> **关联节点**：td_agent_knowledge_architecture, branch_ai_product, branch_ai_frameworks, branch_ai_memory_systems, kd_exercise_health_framework, td_compound_feedback_education
> **更新时间**：2026-03

## 导读

基于前一篇 Agent 知识库架构推演（td_agent_knowledge_architecture）的 Local-first + JSON-LD + Memory 架构，直接落地为滑雪硬件产品的 AI Coach 系统方案。解决滑雪学习者五大核心困惑：我在什么水平？进阶安全吗？下一步怎么走？为什么卡住？如何解决卡点？

**核心教学策略**分为两条并行回路：
1. **积木式教学**（目标导向）：基于知识图谱的"等级-技能点-知识"上下位关联 + 与"问题"的相关性网络，Agent 精准推荐下一步待学课程而非推送整套视频。图谱赋予 Agent 制定长期/阶段性 Plan 的能力。
2. **反馈式教学**（问题导向）：基于每弯/每趟/每天的数据追踪 + 长线 Memory，通过"输出逻辑门"（完美进阶/专项练习/降级/调整/鼓励/休息）给出切实反馈，降低用户认知选择成本。

**技术架构**完全同构于 ITO Engine：
- JSON-LD 网状知识图谱：节点 ID = 语义标签，挂载多模态教学资源（视频/动图/图解）
- JSONL Memory 层：plan_memory（规划）、daily_memory（每趟数据）、whole_memory（日汇总）、feedback_memory（反馈效果追踪+用户主观评价→Agent自优化）
- PDCA 闭环：每日训练后 daily_memory 对比 plan_memory → 输出完成情况 → 生成下次规划

**TTPPEE 六维评估模型**（滑雪领域原创框架）：
- **T**echnical（核心观测靶点）：真实动作技能水平
- **T**actical（导航意图）：为适应地形选择的策略，解释动作合理性
- **P**hysical（物理天花板）：身体硬件条件+疲劳度，提醒系统不生搬硬套理想模型
- **P**sychological（技术阻断器）：恐惧是重心后坐、身体僵硬的头号元凶
- **E**nvironment（容错度系数）：雪况/坡度/天气动态调整评判标准
- **E**quipment（传输介质）：装备对能力的放大或限制

**I.A.C.R.C.V. 五阶段技能掌握模型**，每阶段对应不同的 AI 反馈策略：
1. Initiation（保姆模式）→ 2. Acquisition（引导模式）→ 3. Consolidation（教练闭嘴模式）→ 4. Refinement（数据分析师模式）→ 5. Creative Variation（平级交流模式）

这个模型的认知科学基础极为扎实：从"意识控制"到"肌肉记忆"到"创造性变体"的进阶，精确对应了认知负荷理论中固有负荷从高到低的过程。而 AI 反馈策略从"高频正向激励"→"启发式提问"→"减少干预"→"微观数据"→"平等共决"的演变，暗合了维果茨基的最近发展区（ZPD）和脚手架理论的精髓——在学习者能力边界处提供恰到好处的支撑，然后逐步撤除。

**与 ITO Engine 的同构关系**：这个 Coach 系统就是"运动领域的 ITO"——JSON-LD 图谱存储领域知识、JSONL Memory 记录成长轨迹、PDCA 驱动闭环进化、Skill 系统路由不同场景。区别仅在于：ITO 的"领域"是用户的全部认知版图，Coach 的"领域"是滑雪技能树。

---

## 原文

（原文同 inbox/processed/滑雪AI Coach系统方案-202603.md）
