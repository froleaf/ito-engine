#!/bin/bash
# 同步框架文件到公开仓库目录
# 用法：bash scripts/sync_to_public.sh ["可选的附加说明"]
# commit message 会基于实际 diff 自动生成，附加说明追加在末尾

PUBLIC_DIR="../ito-engine-public"

if [ ! -e "$PUBLIC_DIR/.git" ]; then
  echo "错误：$PUBLIC_DIR 不存在或不是 git 仓库"
  exit 1
fi

# 同步所有文件（排除 .git 目录），public 的 .gitignore 会自动过滤私人数据
rsync -av --delete \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='.cache' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  ./ "$PUBLIC_DIR/"

# 进入 public 目录
cd "$PUBLIC_DIR"

# 暂存所有变更（让 .gitignore 生效过滤私人数据）
git add -A

# 检查是否有变更
if git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "没有需要更新的框架文件"
  exit 0
fi

# === 基于实际 diff 自动生成 commit message ===
generate_commit_msg() {
  local changed_files
  changed_files=$(git diff --cached --name-only)

  # 按路径前缀分类统计
  local skills=0 templates=0 scripts=0 docs=0 readme=0 claude=0 init=0 other=0
  local skill_names=""

  while IFS= read -r file; do
    case "$file" in
      .claude/skills/*)
        skills=$((skills + 1))
        # 提取 skill 名称
        local sname
        sname=$(echo "$file" | sed 's|.claude/skills/||;s|/.*||')
        if [[ ! "$skill_names" == *"$sname"* ]]; then
          skill_names="${skill_names:+$skill_names, }$sname"
        fi
        ;;
      templates/*)        templates=$((templates + 1)) ;;
      scripts/*)          scripts=$((scripts + 1)) ;;
      docs/*)             docs=$((docs + 1)) ;;
      README.md)          readme=1 ;;
      CLAUDE.md)          claude=$((claude + 1)) ;;
      _init/*)            init=$((init + 1)) ;;
      *)                  other=$((other + 1)) ;;
    esac
  done <<< "$changed_files"

  # 组装 commit message
  local parts=()

  if [ $skills -gt 0 ]; then
    parts+=("skills($skill_names)")
  fi
  if [ $templates -gt 0 ]; then
    parts+=("templates")
  fi
  if [ $scripts -gt 0 ]; then
    parts+=("scripts")
  fi
  if [ $docs -gt 0 ]; then
    parts+=("docs")
  fi
  if [ $readme -gt 0 ]; then
    parts+=("README")
  fi
  if [ $claude -gt 0 ]; then
    parts+=("CLAUDE.md")
  fi
  if [ $init -gt 0 ]; then
    parts+=("_init")
  fi
  if [ $other -gt 0 ]; then
    parts+=("other")
  fi

  # 判断前缀：全是新文件用 feat，有删除用 refactor，否则用 update
  local has_add has_modify has_delete
  has_add=$(git diff --cached --diff-filter=A --name-only | head -1)
  has_delete=$(git diff --cached --diff-filter=D --name-only | head -1)
  has_modify=$(git diff --cached --diff-filter=M --name-only | head -1)

  local prefix="update"
  if [ -n "$has_add" ] && [ -z "$has_modify" ] && [ -z "$has_delete" ]; then
    prefix="feat"
  elif [ -n "$has_delete" ]; then
    prefix="refactor"
  fi

  # 组装最终 message
  local scope
  scope=$(IFS=', '; echo "${parts[*]}")
  local msg="${prefix}: ${scope}"

  # 追加用户的附加说明（如果有）
  if [ -n "$1" ]; then
    msg="${msg} — $1"
  fi

  echo "$msg"
}

COMMIT_MSG=$(generate_commit_msg "$1")

echo "自动生成 commit message: $COMMIT_MSG"
echo ""
git diff --cached --stat
echo ""

git commit -m "$COMMIT_MSG"
git push origin main

echo "公开仓库已更新"
