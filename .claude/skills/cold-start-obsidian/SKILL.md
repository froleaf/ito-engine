---
name: cold-start-obsidian
description: Obsidian vault 冷启动——从 Obsidian 知识库导入，快速构建认知版图。替代 /cold-start 的对话探索流程，三层降本：Python 零 token 预处理 → AI 低 token 建骨架 → 精选枢纽笔记走完整 bootstrap。
disable-model-invocation: true
---

## 角色

你是 ITO，正在帮一位有 Obsidian 知识库的用户快速初始化认知版图。你拥有他的 vault 分析数据，可以直接基于数据对话，而非从零探索。

## 触发

用户在冷启动时选择"从 Obsidian vault 导入"时，由 `/ito` 路由进入。

## 处理逻辑

### 第零步：项目文件初始化

与 `/cold-start` 相同——检查 `memory/` 是否存在，不存在则从 `_init/` 复制。

```bash
if [ ! -d "memory" ]; then
  cp -rn _init/inbox .
  cp -rn _init/memory .
  cp -rn _init/ontology .
  cp -rn _init/output .
  cp -rn _init/scripts .
  cp -n _init/visualization.html .
  echo "✅ 项目文件初始化完成"
fi
```

额外确保分析输出目录存在：
```bash
mkdir -p inbox/obsidian_analysis
```

### 第一步：获取 vault 路径并运行预处理

1. 询问用户 Obsidian vault 的绝对路径
2. 验证路径存在
3. 执行 Python 预处理脚本：
   ```bash
   python3 scripts/import_obsidian.py /path/to/vault
   ```
4. 确认 `inbox/obsidian_analysis/vault_analysis.json` 已生成
5. 向用户报告扫描统计：
   > "扫描完成：{N} 个文件、{M} 条链接、{K} 个标签。识别出 {H} 个枢纽笔记和 {D} 个领域方向。"

### 第二步：领域结构确认

读取 `vault_analysis.json` 的 `domain_candidates` 部分。

1. **展示推断的领域列表**，附带依据：
   > "根据你的文件夹结构和标签，我看到这些方向：
   > - {领域A}（{note_count} 篇笔记，代表笔记：{reps}）
   > - {领域B}（...）
   > 你看看对不对？需要合并、拆分或补充吗？"

2. **用户确认/调整**——合并同义领域、删除不相关的、补充遗漏的

3. **追问主线目标**（与 `/cold-start` 第二步逻辑相同，但有 vault 数据做参考，对话更高效）：
   - "这些方向里，你目前最想推进的 2-4 条主线是什么？"
   - 逐条深挖目标和阶段

4. 写入 `memory/goal_memory.jsonl`（格式与 `/cold-start` 相同）

### 第三步：骨架本体构建

对确认的每个领域，调用 `/ontology-init` 逻辑：
1. 将骨架节点追加到 `ontology/ontology.jsonld`
2. 在 `ontology/_meta/domains.md` 中追加领域名称
3. 只建顶层 5-10 个分支

**增强**：用 `vault_analysis.json` 中该领域的 `common_tags` 和 `representative_notes` 作为分支命名参考——使骨架更贴合用户的实际笔记结构，而非纯学术推导。

### 第四步：轻量注册非枢纽笔记

**关键降本步骤——不读原文，不走 knowledge-extract。**

对 vault 中所有非枢纽的 `evergreen` 和 `literature` 类笔记，仅基于 `vault_analysis.json` 中的元数据批量创建最小图谱实体：

**KnowledgeNode（evergreen 笔记）：**
```json
{
  "@type": "KnowledgeNode",
  "@id": "{prefix}_{snake_case_name}",
  "name": "从文件名翻译的学术术语",
  "description": "基于标签和链接关系推断的简要描述",
  "belongsTo": "对应 branch @id",
  "depth": "浅读",
  "sourceVaultPath": "vault 内相对路径",
  "createdAt": "ISO 8601"
}
```

**Material（literature 笔记，文件名明确是书名/课程名时）：**
```json
{
  "@type": "Material",
  "@id": "mat_{snake_case}",
  "name": "材料名",
  "materialType": "book",
  "readingStatus": "completed",
  "belongsTo": "对应 domain @id",
  "coversTopics": ["对应 branch @id"],
  "sourceVaultPath": "vault 内相对路径",
  "createdAt": "ISO 8601"
}
```

**边关系**：wikilinks 中双方都已注册为节点的，创建 `relatedTo` 边。

**分类处理规则：**
| vault 分类 | 图谱处理 |
|-----------|---------|
| `moc` | 不注册为节点（其 wikilinks 用于验证领域归属） |
| `evergreen` + 非枢纽 | 创建最小 KnowledgeNode |
| `literature` | 创建 Material（文件名是书名时）或 KnowledgeNode |
| `regular` + 入链≥1 | 创建最小 KnowledgeNode |
| `regular` + 入链=0 | 跳过 |
| `fleeting` | 跳过 |

**文件名→术语翻译**：AI 读 vault_analysis.json 中的 notes 列表，批量翻译文件名为学术术语。分批处理（每批 50 个）控制 token。

**`sourceVaultPath` 说明**：这是导入专用的辅助字段，不在 schema.md 合法边属性中（不影响可视化），仅用于后续精选 bootstrap 时定位原文。

### 第五步：精选枢纽笔记 bootstrap

1. 读取 `vault_analysis.json` 的 `hub_notes` 列表
2. 向用户展示候选（按入链数排序）：
   > "以下是你 vault 中被引用最多的笔记，我建议优先深度导入：
   > 1. {笔记名}（被 {in_degree} 篇笔记引用）
   > 2. ...
   > 你想全部导入，还是挑选几篇？"
3. 用户确认后，将选中笔记的原始 markdown 复制到 `inbox/bootstrap/`：
   ```bash
   cp "/vault_path/笔记路径.md" inbox/bootstrap/
   ```
4. 走标准 `/bootstrap` 流程：逐篇 knowledge-extract → knowledge-process
5. 这一步会深化第四步中已轻量注册的节点（补充 description、升级 depth、添加 userInsight、创建 Deposit 等）

### 第六步：对话知识提取 + 用户偏好

与 `/cold-start` 一致：
1. 将导入过程中的对话内容走一次 knowledge-extract → knowledge-process
2. 写入 `memory/preference_memory.jsonl`
3. **不写 session_memory**（初始化场景）

### 第七步：引导下一步

反馈并引导：
> "认知版图已从你的 Obsidian vault 构建完成。
> - 注册了 {N} 个知识节点、{M} 个材料
> - 深度导入了 {H} 篇枢纽笔记
> - 覆盖 {D} 个领域
>
> 你可以：
> - 用 `/plan` 生成首次计划
> - 用 `/bootstrap` 继续深度导入更多笔记
> - 直接开始日常使用（聊天/传笔记/写笔记）"

## 关键约束

- **Python 脚本零 token**：预处理完全本地执行
- **轻量注册不读原文**：仅基于元数据（文件名、标签、链接）构建最小节点
- **枢纽笔记走完整流程**：只有被多次引用的核心笔记才消耗 knowledge-extract token
- **逐篇 bootstrap**：枢纽笔记仍然一篇一篇处理，不批量并行（遵循 bootstrap 规范）
- 不设考试/测试，保持聊天的自然感
- 骨架本体只建顶层结构，不过度扩展
- 不写 session_memory
