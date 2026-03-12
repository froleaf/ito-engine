#!/bin/bash
# 同步框架文件到公开仓库目录
# 用法：bash scripts/sync_to_public.sh "commit message"

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

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "没有需要更新的框架文件"
  exit 0
fi

# 提交并推送
COMMIT_MSG="${1:-sync: 同步框架更新}"
git add -A
git commit -m "$COMMIT_MSG"
git push origin main

echo "公开仓库已更新"
