#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT/run"
mkdir -p "$RUN_DIR"

pid_is_napcat() {
  local candidate="$1"
  [[ -r "/proc/$candidate/cmdline" ]] || return 1
  tr '\0' ' ' < "/proc/$candidate/cmdline" | grep -Fq "$ROOT/protocol/squashfs-root/qq"
}

while true; do
  napcat_pid=""
  if [[ -f "$RUN_DIR/napcat.pid" ]]; then
    napcat_pid="$(cat "$RUN_DIR/napcat.pid" 2>/dev/null || true)"
  fi
  if [[ -z "$napcat_pid" ]] || ! pid_is_napcat "$napcat_pid"; then
    rm -f "$RUN_DIR/napcat.pid"
    printf '[%s] NapCat 未运行，正在恢复。\n' "$(date '+%F %T')"
    "$ROOT/scripts/start-napcat.sh" || true
  fi
  sleep 10
done
