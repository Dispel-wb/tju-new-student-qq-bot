#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/run/napcat.pid"
WATCHDOG_FILE="$ROOT/run/protocol-watchdog.pid"

if [[ -f "$WATCHDOG_FILE" ]]; then
  watchdog_pid="$(cat "$WATCHDOG_FILE")"
  if [[ -r "/proc/$watchdog_pid/cmdline" ]] && \
      tr '\0' ' ' < "/proc/$watchdog_pid/cmdline" | grep -Fq "protocol-watchdog.sh"; then
    kill "$watchdog_pid" 2>/dev/null || true
  fi
  rm -f "$WATCHDOG_FILE"
fi

if [[ ! -f "$PID_FILE" ]]; then
  echo "NapCat QQ is not running."
  exit 0
fi

pid="$(cat "$PID_FILE")"
if [[ -r "/proc/$pid/cmdline" ]] && \
    tr '\0' ' ' < "/proc/$pid/cmdline" | grep -Fq "$ROOT/protocol/squashfs-root/qq"; then
  kill "$pid"
  for _ in {1..20}; do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
fi

rm -f "$PID_FILE"
echo "NapCat QQ stopped."
