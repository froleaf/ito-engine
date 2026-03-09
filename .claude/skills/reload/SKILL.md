---
name: reload
description: 重新加载——从保留的对话存档和笔记中重建知识系统。用于保留内容重置之后的恢复。
disable-model-invocation: true
---

## 用途

从保留的对话存档和笔记中重建整个知识系统。典型使用场景：在「保留内容重置」之后，利用保留下来的冷启动对话和笔记，重新走一遍完整的构建流程。

## 触发

- 用户在保留内容重置后要求重新加载
- 用户主动要求从存档重建系统

## 输入

- `inbox/conversations/` 中的对话存档（重点关注冷启动对话）
- `inbox/bootstrap/` 中的历史内容（旧笔记、旧文章、聊天记录等）
- `inbox/notes/` 中的所有 .md 文件

## 处理逻辑

### 第一步：扫描与识别

1. 扫描 `inbox/conversations/` 中的所有 .md 文件
2. **识别冷启动对话**：查找文件名包含"冷启动"的文件
3. 扫描 `inbox/bootstrap/` 中的所有文件
4. 扫描 `inbox/notes/` 中的所有 .md 文件
5. 向用户展示完整的重建清单，包括各目录的文件数量
6. 确认是否开始重建

### 第二步：重建基础 — 重放冷启动对话

**这一步必须最先执行**，因为冷启动对话包含了领域注册和个人认知数据的初始信息。

1. 读取冷启动对话全文
2. 从对话内容中提取领域列表、自评深度、偏好等
3. 对每个识别到的领域，执行 `/ontology-init` 的逻辑
4. 在统一图谱的对应节点上标注初始个人元数据（depth、nodeRole、userInsight）
5. 写入 `preference_memory.jsonl`

### 第三步：重放历史内容（bootstrap）

如果 `inbox/bootstrap/` 中有文件：
1. 按文件名排序（日期升序）
2. 对每份内容执行 `/bootstrap` 的逻辑（knowledge-extract + knowledge-process，不写 session_memory，不触发 plan）
3. 处理完的文件移入 `inbox/processed/`
4. 每处理 3-5 篇给用户简要进度反馈
5. 如发现新领域候选，暂停询问用户是否注册

### 第四步：重放其他对话存档

如果有冷启动之外的对话存档：
1. 按文件名排序（日期升序）
2. 对每篇对话存档执行 `/knowledge-extract` + `/knowledge-process` 的逻辑

### 第五步：处理笔记

对 `inbox/notes/` 中的笔记按顺序处理：
1. 按文件名排序
2. 对每篇笔记走正常的传笔记流程
3. 将处理完的文件移入 `inbox/processed/`
4. 如遇到新领域：暂停，询问用户是否注册

### 第六步：生成计划

所有内容处理完毕后，执行 `/plan` 的逻辑生成首周计划。此时图谱已有充分数据，计划质量远高于冷启动后立即生成。

### 第七步：同步可视化

执行 `python3 scripts/build_visualization.py` 重新生成 `visualization.html`。

### 第八步：汇总报告

全部处理完成后反馈：
- 恢复了哪些领域
- 总共处理了多少篇：历史内容 + 对话存档 + 笔记
- 新增了多少个知识节点
- 创建了多少个 Deposit（知识沉淀 + 思考沉淀）
- 在读材料列表（readingStatus: in_progress）
- 发现的跨域关联（如有）

## 注意事项

- **执行顺序：冷启动 → bootstrap → 对话存档 → 笔记 → plan**——没有领域骨架，后续内容无法正确归属；plan 放在最后才有充分数据支撑
- 如果找不到冷启动对话存档，告知用户需要重新进行冷启动流程
- 重新加载是幂等的：通过 grep 去重避免重复节点
- 对话存档不会被移动——始终保留在 `inbox/conversations/` 中
- bootstrap 内容的处理不写 session_memory——与 `/bootstrap` 行为一致
