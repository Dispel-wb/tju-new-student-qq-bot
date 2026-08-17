#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT/run"
LOG_DIR="$ROOT/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"

pid_matches() {
  local candidate="$1"
  local expected="$2"
  [[ -r "/proc/$candidate/cmdline" ]] || return 1
  tr '\0' ' ' < "/proc/$candidate/cmdline" | grep -Fq "$expected"
}

pid_is_bot() {
  local candidate="$1"
  [[ -r "/proc/$candidate/cmdline" ]] || return 1
  [[ "$(readlink -f "/proc/$candidate/cwd" 2>/dev/null || true)" == "$ROOT/src" ]] || return 1
  tr '\0' ' ' < "/proc/$candidate/cmdline" | grep -Eq '(^| )bot\.py( |$)'
}

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "缺少 Python 环境：$ROOT/.venv" >&2
  sleep 8
  exit 1
fi

if [[ -f "$RUN_DIR/protocol-watchdog.pid" ]]; then
  watchdog_pid="$(cat "$RUN_DIR/protocol-watchdog.pid")"
else
  watchdog_pid=""
fi
if [[ -z "$watchdog_pid" ]] || ! pid_matches "$watchdog_pid" "protocol-watchdog.sh"; then
  nohup "$ROOT/scripts/protocol-watchdog.sh" >>"$LOG_DIR/protocol-watchdog.log" 2>&1 &
  watchdog_pid=$!
  echo "$watchdog_pid" >"$RUN_DIR/protocol-watchdog.pid"
fi

if [[ -f "$RUN_DIR/bot-launch.pid" ]]; then
  bot_pid="$(cat "$RUN_DIR/bot-launch.pid")"
else
  bot_pid=""
fi
if [[ -z "$bot_pid" ]] || ! pid_is_bot "$bot_pid"; then
  bot_pid=""
  while read -r candidate; do
    if pid_is_bot "$candidate"; then
      bot_pid="$candidate"
      break
    fi
  done < <(pgrep -u "$(id -u)" -f 'python.*bot\.py' || true)
fi
if [[ -n "$bot_pid" ]]; then
  echo "$bot_pid" >"$RUN_DIR/bot-launch.pid"
  echo "新版机器人已经在运行（PID $bot_pid）。"
  sleep 3
  exit 0
fi

echo "正在等待 QQ 协议端就绪……"
if "$ROOT/.venv/bin/python" "$ROOT/src/onebot_endpoint.py" \
    --config-dir "$ROOT/protocol/config" --wait 120 >/dev/null; then
  nohup "$ROOT/scripts/run-bot.sh" >>"$LOG_DIR/bot-console.log" 2>&1 &
  bot_pid=$!
  echo "$bot_pid" >"$RUN_DIR/bot-launch.pid"
  sleep 3
  if pid_is_bot "$bot_pid"; then
    echo "新版机器人启动成功（PID $bot_pid）。"
    echo "日志：$LOG_DIR/bot-console.log"
    sleep 3
    exit 0
  fi
  rm -f "$RUN_DIR/bot-launch.pid"
  echo "机器人启动失败，最近日志如下：" >&2
  tail -n 40 "$LOG_DIR/bot-console.log" >&2 || true
  sleep 8
  exit 1
fi

echo "没有发现可连接的 OneBot WebSocket。请确认 QQ 已登录后重试。" >&2
read -r -p "按回车退出..." _
exit 1
