#!/usr/bin/env bash
# 发布人才政策图谱到 release 分支（服务器端 git fetch + reset --hard origin/release）
# 用法：先 python _build_html.py 生成最新 人才引进政策_2026.html，再 bash release.sh
set -euo pipefail
cd "$(dirname "$0")"

SRC="人才引进政策_2026.html"
if [ ! -f "$SRC" ]; then echo "❌ 找不到 $SRC，先跑构建"; exit 1; fi
SCRIPT_DIR=$(pwd)
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "https://github.com/cannotcodetao/talent-policy-atlas.git")
case "$REMOTE_URL" in
  http*|git@*|ssh*|file:*|[A-Za-z]:*|/*) : ;;
  *) REMOTE_URL="$SCRIPT_DIR/$REMOTE_URL" ;;
esac
mkdir -p _deploy && cd _deploy
if [ ! -d .git ]; then
  git init -b release
fi
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"
cp "../$SRC" index.html
git add -A
if git diff --cached --quiet 2>/dev/null && [ -n "$(git rev-parse HEAD 2>/dev/null || true)" ]; then
  echo "无变化，跳过发布"
  exit 0
fi
git -c user.name="deploy" -c user.email="deploy@local" commit -m "release: talent-policy $(date +%Y-%m-%d\ %H:%M)"
git push origin release --force
echo "✅ talent-policy release 分支已更新：$REMOTE_URL"
