#!/usr/bin/env bash
# SITL fleet v5: detached, stdin-keepalive, port-safe, self-verifying,
# and DEATH-INSTRUMENTED: a wrapper logs the exact exit code of each daemon.
BIN="$HOME/ardupilot/build/sitl/bin/arducopter"
DEFAULTS="$HOME/ardupilot/Tools/autotest/default_params/copter.parm"
LOGDIR="$HOME/swarm-projectII/swarm-project/logs/sitl"
mkdir -p "$LOGDIR"

pkill -f "arducopter|MAVProxy" 2>/dev/null
for p in 5770 5780 5790 5800 5810; do
    for _ in $(seq 1 15); do ss -tln | grep -q ":$p " || break; sleep 1; done
done

HOMES=(
  "6.5244,3.3792,20,0"
  "6.5300,3.3850,20,0"
  "6.5360,3.3910,20,0"
  "6.5420,3.3970,20,0"
  "6.5480,3.4030,20,0"
)

for i in 1 2 3 4 5; do
    idx=$((i - 1))
    FIFO="$LOGDIR/.stdin_D$i"; rm -f "$FIFO"; mkfifo "$FIFO"
    LOG="$LOGDIR/D$i.log"; : > "$LOG"
    echo "[fleet] starting D$i (instance=$i sysid=$i tcp=$((5760 + 10 * i)))"
    setsid nohup bash -c '
        fifo="$1"; log="$2"; shift 2
        "$@" 0<>"$fifo" >>"$log" 2>&1
        code=$?
        echo "[wrapper] $(date +%T) EXITED code=$code" >>"$log"
    ' _ "$FIFO" "$LOG" "$BIN" -I"$i" --sysid "$i" \
        --model "+" --defaults "$DEFAULTS" --home "${HOMES[$idx]}" </dev/null &
    sleep 1
done

echo "[fleet] launched - verifying..."
alive=0
for attempt in 1 2 3 4; do
    sleep 5
    alive=$(pgrep -c arducopter 2>/dev/null); alive=${alive:-0}
    echo "[fleet] check $attempt: processes=$alive/5"
    [ "$alive" = "5" ] && break
done
[ "$alive" = "5" ] && echo "[fleet] HEALTHY at $((20))s mark." || \
  for i in 1 2 3 4 5; do echo "--- D$i ---"; tail -n 4 "$LOGDIR/D$i.log"; done
