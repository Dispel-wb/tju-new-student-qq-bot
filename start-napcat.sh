#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPDIR="$ROOT/protocol/squashfs-root"
LOG_DIR="$ROOT/logs"
RUN_DIR="$ROOT/run"
CONFIG_DIR="$ROOT/protocol/config"

mkdir -p "$LOG_DIR" "$RUN_DIR" "$CONFIG_DIR"

pid_is_napcat() {
  local candidate="$1"
  [[ -r "/proc/$candidate/cmdline" ]] || return 1
  tr '\0' ' ' < "/proc/$candidate/cmdline" | grep -Fq "$APPDIR/qq"
}

if [[ -f "$RUN_DIR/napcat.pid" ]]; then
  current_pid="$(cat "$RUN_DIR/napcat.pid")"
  if pid_is_napcat "$current_pid"; then
    echo "NapCat QQ is already running (PID $current_pid)."
    exit 0
  fi
  rm -f "$RUN_DIR/napcat.pid"
fi

if [[ ! -x "$APPDIR/qq" ]]; then
  echo "Missing executable: $APPDIR/qq" >&2
  exit 1
fi

export APPDIR
export NAPCAT_WORKDIR="$ROOT/protocol"
export XDG_CONFIG_HOME="$CONFIG_DIR"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"
if [[ -z "${XAUTHORITY:-}" ]]; then
  shopt -s nullglob
  xauthority_candidates=("$XDG_RUNTIME_DIR"/.mutter-Xwaylandauth.*)
  shopt -u nullglob
  if (( ${#xauthority_candidates[@]} > 0 )); then
    export XAUTHORITY="${xauthority_candidates[0]}"
  fi
fi
export PATH="$APPDIR:$APPDIR/usr/sbin:$PATH"
export LD_LIBRARY_PATH="$APPDIR:$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="$APPDIR/usr/share:/usr/local/share:/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
export GSETTINGS_SCHEMA_DIR="$APPDIR/usr/share/glib-2.0/schemas${GSETTINGS_SCHEMA_DIR:+:$GSETTINGS_SCHEMA_DIR}"
export LIBGL_ALWAYS_SOFTWARE=1
export QT_OPENGL=software
export QT_QUICK_BACKEND=software
export VK_ICD_FILENAMES="$APPDIR/vk_swiftshader_icd.json"

cd "$ROOT/protocol"
qq_args=(
  --no-sandbox
  --enable-logging
  --ozone-platform=x11
  --use-gl=angle
  --use-angle=swiftshader
  --enable-unsafe-swiftshader
  --disable-gpu-sandbox
  --disable-gpu-compositing
)
if [[ -s "$ROOT/protocol/account" ]]; then
  qq_account="$(tr -cd '0-9' < "$ROOT/protocol/account")"
  if [[ -n "$qq_account" ]]; then
    qq_args+=(-q "$qq_account")
  fi
fi

nohup "$APPDIR/qq" "${qq_args[@]}" \
  >>"$LOG_DIR/napcat-console.log" 2>&1 &
pid=$!
echo "$pid" >"$RUN_DIR/napcat.pid"
for _ in $(seq 1 12); do
  sleep 1
  if ! pid_is_napcat "$pid"; then
    replacement_pid="$(pgrep -u "$(id -u)" -f "$APPDIR/qq" | head -n 1 || true)"
    if [[ -n "$replacement_pid" ]] && pid_is_napcat "$replacement_pid"; then
      pid="$replacement_pid"
      echo "$pid" >"$RUN_DIR/napcat.pid"
    else
      break
    fi
  fi
done

if ! pid_is_napcat "$pid"; then
  rm -f "$RUN_DIR/napcat.pid"
  echo "NapCat QQ exited during startup. See $LOG_DIR/napcat-console.log" >&2
  tail -n 80 "$LOG_DIR/napcat-console.log" >&2 || true
  exit 1
fi

echo "NapCat QQ started and remained stable (PID $pid)."
