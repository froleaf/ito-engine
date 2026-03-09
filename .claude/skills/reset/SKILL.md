---
name: reset
description: 重置项目数据——提供保留内容重置和完全重置两种模式。需要用户输入确认口令。
disable-model-invocation: true
---

## 用途

将 ITO 引擎的数据恢复到初始状态。提供两种模式：
- **保留内容重置**：保留用户的原始笔记和对话，仅清除图谱和记忆，便于重新加载处理
- **完全重置**：清除所有数据，恢复到全新状态，适合交付给新用户使用

## 处理逻辑

### 第一步：询问重置模式

向用户展示两个选项：

> **选项 A — 保留内容重置**
> 保留你的笔记和对话存档（将 `inbox/processed/` 中的已处理文件移回 `inbox/notes/`），清除图谱、记忆和输出。重置后可通过 `/reload` 重新处理这些笔记。
>
> **选项 B — 完全重置**
> 清除所有数据，包括笔记、对话、图谱、记忆和输出。适合把项目交给新用户使用。

### 第二步：强验证确认

**必须**在执行前完成以下确认流程，缺一不可：

1. **告知影响范围**：

   **选项 A 会清除**：
   - `memory/`：所有记忆文件
   - `ontology/ontology.jsonld`：统一知识图谱
   - `ontology/_meta/domains.md`：领域索引
   - `output/`：所有沉淀产出和草稿

   **选项 A 会保留**：
   - `inbox/notes/`：原有笔记 + 从 `processed/` 移回的已处理笔记
   - `inbox/conversations/`：对话存档

   **选项 B 会清除**：以上所有内容，加上 `inbox/` 中的全部笔记和对话

2. **要求用户输入确认口令**：
   - 选项 A：输入「确认保留重置」
   - 选项 B：输入「确认完全重置」

3. **只有收到完全匹配的口令才执行**。

### 第三步：执行重置

#### 选项 A — 保留内容重置

```bash
# 1. 将 processed 中的文件移回 notes
mv inbox/processed/* inbox/notes/ 2>/dev/null

# 2. 重置 memory
rm -rf memory/*
cp _init/memory/*.jsonl memory/
cp _init/memory/todo.json memory/todo.json
mkdir -p memory/session_memory

# 3. 重置 ontology
cp _init/ontology/ontology.jsonld ontology/ontology.jsonld
echo "# 领域索引" > ontology/_meta/domains.md

# 4. 重置 output
rm -rf output/*
mkdir -p output/deposits output/drafts output/reviews output/thinking_scripts

# 5. 重置可视化
cp _init/visualization.html visualization.html

# 6. 重置思维脚本和场景索引
rm -f scripts/thinking/*
cp _init/ontology/_meta/thinking_scenarios.md ontology/_meta/thinking_scenarios.md
```

#### 选项 B — 完全重置

```bash
# 1. 清空 inbox 所有内容
rm -f inbox/notes/* inbox/processed/* inbox/conversations/*

# 2-6. 同选项 A
```

### 第四步：验证与后续引导

重置完成后：
1. 检查数据文件是否正确清空
2. 向用户确认重置成功
3. 根据模式给出后续建议：
   - **选项 A**：提示用户可使用 `/reload`
   - **选项 B**：提示用户可通过 `/cold-start` 重新初始化

## 注意事项

- **绝不跳过确认步骤**，即使用户催促
- 此操作不可逆，没有撤销机制
- 此操作不影响 `.claude/skills/`、`templates/`、`agent_profile.json` 等结构文件
- `_init/` 文件夹本身不会被修改
