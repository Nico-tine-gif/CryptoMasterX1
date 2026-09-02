#!/data/data/com.termux/files/usr/bin/bash

BASE="$HOME/CryptoMasterX1"
LOG_DIR="$BASE/logs"
LOG="$LOG_DIR/master_runner.log"

mkdir -p "$LOG_DIR"

cd "$BASE" || exit 1

echo "============================================================" >> "$LOG"
echo "[START] CryptoMasterX1 supervisor $(date)" >> "$LOG"
echo "============================================================" >> "$LOG"

# ------------------------------------------------------------
# ANDROID WAKE LOCK
# ------------------------------------------------------------

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
    echo "[$(date)] Termux wake-lock: ENABLED" >> "$LOG"
else
    echo "[$(date)] WARNING: termux-wake-lock unavailable" >> "$LOG"
fi

# ------------------------------------------------------------
# HARD EXECUTION SAFETY BOUNDARY
# This supervisor does NOT unlock execution.
# It does NOT submit orders.
# It does NOT arm the bot.
# ------------------------------------------------------------

echo "[$(date)] Execution boundary preserved: LOCKED" >> "$LOG"
echo "[$(date)] Order submission: DISABLED" >> "$LOG"
echo "[$(date)] Bot armed: NO" >> "$LOG"
echo "[$(date)] Live execution: FALSE" >> "$LOG"

# ------------------------------------------------------------
# EXISTING CRYPTOMASTERX1 ENGINES
# ------------------------------------------------------------

PHASES=(
    "phase4_market_discovery.py"
    "phase5_market_intelligence.py"
    "phase6_trade_quality.py"
    "phase7_entry_intelligence.py"
    "phase8_entry_validation.py"
    "phase9_decision_gate.py"
    "phase10_trade_lifecycle.py"
)

declare -A PIDS

start_phase() {
    local script="$1"

    if [ ! -f "$BASE/$script" ]; then
        echo "[$(date)] MISSING: $script" >> "$LOG"
        return
    fi

    echo "[$(date)] Starting $script" >> "$LOG"

    python -u "$BASE/$script" >> "$LOG" 2>&1 &

    PIDS["$script"]=$!

    echo "[$(date)] $script PID=${PIDS[$script]}" >> "$LOG"
}

stop_phase() {
    local script="$1"
    local pid="${PIDS[$script]}"

    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
    fi
}

# ------------------------------------------------------------
# START ALL EXISTING CONTINUOUS PHASES
# ------------------------------------------------------------

for phase in "${PHASES[@]}"; do
    start_phase "$phase"
    sleep 2
done

echo "[$(date)] All available CryptoMasterX1 engines started." >> "$LOG"

# ------------------------------------------------------------
# SUPERVISOR LOOP
# ------------------------------------------------------------

while true; do

    # Keep Android awake.
    if command -v termux-wake-lock >/dev/null 2>&1; then
        termux-wake-lock >/dev/null 2>&1 || true
    fi

    # Restart any phase that has stopped.
    for phase in "${PHASES[@]}"; do

        pid="${PIDS[$phase]}"

        if [ -z "$pid" ]; then
            continue
        fi

        if ! kill -0 "$pid" 2>/dev/null; then

            echo "[$(date)] $phase stopped. Restarting..." >> "$LOG"

            sleep 5

            start_phase "$phase"
        fi

    done

    sleep 15

done
