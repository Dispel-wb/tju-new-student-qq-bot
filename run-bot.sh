#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT/run"
mkdir -p "$RUN_DIR"

exec 9>"$RUN_DIR/bot.lock"
if ! flock -n 9; then
  echo "机器人已经在运行。"
  sleep 5
  exit 0
fi

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "缺少 Python 环境：$ROOT/.venv"
  read -r -p "按回车退出..." _
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "缺少密钥文件：$ROOT/.env"
  read -r -p "按回车退出..." _
  exit 1
fi

set -a
source "$ROOT/.env"
set +a

export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="$NO_PROXY"
if ! ss -lnt | grep -q '127.0.0.1:7897'; then
  for proxy_name in HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy; do
    proxy_value="${!proxy_name:-}"
    if [[ "$proxy_value" == *"127.0.0.1:7897"* ]]; then
      unset "$proxy_name"
    fi
  done
fi
export PYTHONUNBUFFERED=1

if ! "$ROOT/.venv/bin/python" "$ROOT/src/onebot_endpoint.py" \
    --config-dir "$ROOT/protocol/config" --wait 10 >/dev/null; then
  echo "当前没有可连接的 OneBot WebSocket；启动器会继续守护协议端，请稍后重试。"
  read -r -p "按回车退出..." _
  exit 1
fi

cd "$ROOT/src"
echo "正在启动 QQ 智能群机器人……"
echo "配置文件：$ROOT/src/bot.md"
echo "OneBot 地址：自动读取 NapCat 配置，断线后重新检测"
echo "按 Ctrl+C 可停止机器人。"
exec "$ROOT/.venv/bin/python" bot.py
