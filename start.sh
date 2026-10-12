#!/bin/zsh
# 浏览器模式启动（不用桌面窗口时用这个）
cd "$(dirname "$0")"
PY=/Users/terrence/.workbuddy/binaries/python/envs/default/bin/python
$PY -m uvicorn backend.app:app --host 127.0.0.1 --port 8765

