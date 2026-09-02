#!/data/data/com.termux/files/usr/bin/bash
set -u

cd "$(dirname "$0")" || exit 1

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock >/dev/null 2>&1 || true
fi

exec python3 "$PWD/master_pipeline.py"
