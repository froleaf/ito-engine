# Material 规范

## 信息检索规范

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

## 阅读状态管理

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
