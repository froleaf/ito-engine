---
name: add-material
description: 创建或更新 Material 实体——标准化的材料录入流程，确保信息补全、边关系正确、可视化同步。由 knowledge-process、bootstrap、ito 待命模式等场景调用。
user-invocable: false
---

## 角色

材料管理员。负责 Material 实体的创建和更新，保证每个 Material 都有完整的元信息、正确的图谱边关系和同步的可视化。

## 触发场景

- `/knowledge-process` 创建 Material 时
- `/bootstrap` 处理学习笔记创建 Material 时
- 待命模式下用户说"帮我加本书"/"记录书单"等
- 任何需要向 ontology.jsonld 添加 Material 实体的场景

## 流程

### 第一步：查重

`grep "材料名关键词" ontology/ontology.jsonld` 检查是否已存在。
- 已存在 → 跳到第五步（更新已有 Material）
- 不存在 → 继续

### 第二步：信息补全

基于 AI 知识储备**主动补全**以下信息，不能只记录用户提到的片段：

**书籍（book）**：
- `author`：完整作者列表（数组），查证准确的姓名拼写
- `publicationYear`：首版出版年份
- `translator`：翻译版本时查证译者
- `publisher`：出版社（如可知）
- `language`：原著语言

**在线课程/视频（video_course/online_course）**：
- `author`：讲师/机构
- `url`：课程链接（公开平台）
- `platform`：所在平台

**文章/论文（article/paper）**：
- `author`：作者列表
- `url`：公开链接（如有）
- `publicationYear`：发表年份

**原则**：确信时直接填写，不确定时留空，不用幻觉填充。

### 第三步：确定边关系

每个 Material 必须至少有一条边连接到图谱：
- `coversTopics`：覆盖的知识节点/分支（**必填**，至少 1 个）
- `belongsTo`：归属的领域（可选，但推荐填写）

确定 coversTopics 时，grep 图谱查找最相关的已有节点。如果没有合适的节点，挂到最相关的 Branch 上。

### 第四步：写入图谱

```json
{
  "@type": "Material",
  "@id": "mat_{short_id}",
  "name": "材料名称",
  "author": ["作者"],
  "materialType": "book|online_course|video_course|article|paper|documentation",
  "language": "zh-CN",
  "readingStatus": "wishlist|in_progress|completed",
  "coversTopics": ["相关节点@id"],
  "belongsTo": "领域@id",
  "createdAt": "ISO 8601"
}
```

如果 `readingStatus` 为 `in_progress`，额外填写：
- `progress`：当前进度描述
- `startedAt`：开始日期
- `lastProgressUpdate`：最近更新日期

### 第五步：更新已有 Material（如查重命中）

- 更新 `readingStatus`（如状态变化）
- 更新 `progress`、`lastProgressUpdate`
- 补充缺失的元信息（author、publicationYear 等）
- 补充缺失的边关系（coversTopics、belongsTo）

### 第六步：Todo 联动

- `readingStatus` 为 `in_progress` 或 `wishlist` → 在 `memory/todo.json` 中创建 `reading` 类型 todo
- `readingStatus` 变为 `completed` 或 `abandoned` → 更新对应 todo 状态

### 第七步：重建可视化

执行 `python3 scripts/build_visualization.py`。

**此步骤不可跳过**——这是本 skill 存在的核心保障之一。
