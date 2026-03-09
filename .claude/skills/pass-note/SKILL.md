---
name: pass-note
description: 传笔记——读取 inbox/notes/ 中的笔记文件或用户提供的 URL，进行知识提取和图谱更新。
---

## 角色

处理用户传入的笔记文件或链接内容，提取知识结构并更新图谱。

## 输入

- `inbox/notes/` 中的 .md 文件（一个或多个）
- 用户在对话中给出的 URL 链接（通过 WebFetch 读取后等同于一篇笔记）

### URL 作为输入源

当输入来源是 URL 时：
1. 通过 WebFetch 读取链接内容，走相同的处理流程
2. 根据用户说明区分来源类型：
   - **外部材料**（"我读了这个"等）：正常提取知识，创建 Material 实体，标记 `source_type: external`
   - **用户自己的产出**（"这是我写的"等）：提取知识和见解，不创建 Material，标记 `source_type: user_output`
3. 如果 URL 无法读取，必须明确告知用户，请其粘贴内容或口述要点

## 处理逻辑

对每篇笔记执行：

1. **阅读全文**，理解核心内容和作者意图
2. **领域识别**：读取 `ontology/_meta/domains.md`，判断涉及哪些领域
3. **知识点提取**：执行 `/knowledge-extract` 的逻辑
4. **与图谱比对**：
   - grep `ontology/ontology.jsonld` 查找已有的相关节点（查看 depth 等个人元数据）
   - 哪些是已有的（深化）？哪些是全新的（新建）？
5. **跨域线索识别**：寻找可能的跨域关联
6. **生成摘要**：为用户生成简要的阅读反馈
7. **归档**：将处理完的文件从 `inbox/notes/` 移到 `inbox/processed/`
8. 执行 `/knowledge-process` 的逻辑完成图谱更新和反馈

## 输出

结构化的知识提取结果 + 用户反馈摘要。
