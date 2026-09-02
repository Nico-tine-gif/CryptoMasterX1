#!/data/data/com.termux/files/usr/bin/bash
cd ~/CryptoMasterX1
source .env 2>/dev/null
export PAPER_MODE ALLOW_LIVE MAX_POSITION_USDT
echo "[$(date)] Activating CryptoMasterX1"
echo " PAPER=$PAPER_MODE LIVE=$ALLOW_LIVE"
while true; do
  python3 master_pipeline.py
  CODE=$?
  echo "[$(date)] Cycle ended code $CODE"
  echo "Restart in 15s... (Ctrl+C to stop)"
  sleep 15
done
