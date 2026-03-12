---
name: weekly-review
description: 周度复盘——统计本周交互数据，生成知识饮食报告，追踪认知成长路径，盘点输出种子，更新下周计划。
disable-model-invocation: true
---

## 角色

数据分析师和成长顾问。将一段时间内的交互数据进行统计压缩，生成知识饮食报告，追踪认知成长路径，盘点输出种子。

## 触发

每周末 / 手动触发。

## 输入

- `memory/session_memory/{YYYY}-W{WW}.jsonl`：指定周的交互记录文件（直接读取对应周文件）
- `memory/plan_memory.jsonl`：当前计划
- `memory/rlhf_memory.jsonl`：策略反馈记录
- `ontology/ontology.jsonld`：统一图谱（grep 查询节点的个人元数据）
- `output/deposits/`：沉淀产出文件（读导读部分）
- `ontology/_meta/domains.md`：领域列表
- `templates/milestone_record.json`：milestone 条目模板

## 处理逻辑

### 第一步：统计聚合

1. 读取对应周的 `memory/session_memory/{YYYY}-W{WW}.jsonl` 文件
2. 计算：
   - 总交互次数、总时长
   - 每个领域的交互次数和时长
   - 整体 I/T/O 比例分布
   - 每个领域的 I/T/O 比例
   - 与计划的偏差

### 第二步：知识饮食光谱

按多个维度分析知识摄入的分布：
- 客观知识 vs 主观体验
- 理论探索 vs 实践应用
- 深度钻研 vs 广度探索
- 输入密度 vs 输出产出
- 与上一周期对比，标注变化趋势

### 第三步：成长路径追踪

通过 grep `ontology/ontology.jsonld` 查询带有个人元数据的节点：
1. 本周期新增了多少带 depth 标注的节点
2. 哪些节点的深度标签升级了
3. 新建了哪些 CrossDomainLink
4. 领域本体总计增长了多少节点
5. 生成认知成长叙事

### 第四步：在读材料跟进

1. `grep "readingStatus.*in_progress" ontology/ontology.jsonld` 找到所有在读材料
2. 对每个在读材料，向用户询问进展：
   - "你之前在读{材料名}，进展如何？"
3. 根据用户回答更新 Material 节点：
   - 有进展 → 更新 `progress`、`lastProgressUpdate`
   - 读完了 → `readingStatus: "completed"`，考虑是否触发 depth 升级或创建 KnowledgeDeposit
   - 暂时不读了 → `readingStatus: "paused"`
   - 不打算继续了 → `readingStatus: "abandoned"`
   - 用户说"没动" → 仅更新 `lastProgressUpdate`，不变其他字段
4. 同时检查长期 paused 的材料（`lastProgressUpdate` 超过 4 周），温和询问是否还打算继续

### 第四步半：Todo 盘点

1. 用脚本预过滤活跃条目（减少 token 消耗）：
   ```bash
   python3 -c "import json; data=json.load(open('memory/todo.json')); [print(json.dumps(t,ensure_ascii=False)) for t in data if t.get('status') in ('open','in_progress')]"
   ```
   按类型分组展示
2. 向用户逐一确认每条 todo 的状态：
   - 继续保留 → 不变
   - 已完成 → `status: "completed"`，填写 `completedAt`
   - 不再需要 → `status: "dropped"`
   - 有进展想补充 → 更新 `description`
3. **同步在读材料**：将图谱中 `readingStatus: "in_progress"` 的 Material 同步为 `reading` 类型 todo（如 todo.json 中尚不存在对应条目）
4. **扫描 deposit 导读**：快速浏览近期 Deposit 的导读部分，识别其中明确的"待深入方向"，补充为 `deep_thinking` 类型 todo
5. 更新 `memory/todo.json`

### 第五步：产出盘点

1. grep 图谱中本周期新增或更新的 Deposit 实体
2. grep `outputPotential` 为 high/potential 的节点，汇总潜在输出候选
3. 推荐下一步可以推进的方向

### 第六步：写入 milestone_memory

按 `templates/milestone_record.json` 格式组装并追加写入 `memory/milestone_memory.jsonl`。

### 第七步：调用 /plan 更新下周计划

在调用 /plan 时，将 `memory/todo.json` 中近期活跃（`open` 或 `in_progress`）的 todo 作为输入参考，帮助用户在安排下周精力时考虑这些待办。特别是 `topic_to_explore` 和 `deep_thinking` 类型的 todo，可能影响对话和思考方向的安排。

### 第八步：沉寂领域检查

执行 `/dormant-check` 的逻辑检查沉寂领域。

## 记忆读写规则

- JSONL 文件 append-only，每条记录单行 JSON，必须包含 `ts` 字段
- 读取策略：按 `ts` 字段筛选指定时间段，或读取最后 N 行
- 参照 `templates/` 下对应模板

## 输出

- milestone_memory 条目
- 知识饮食周报（参照 `templates/diet_report.md`）
- 向用户呈现周报 + 下周建议
