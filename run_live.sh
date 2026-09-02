#!/bin/bash
cd ~/CryptoMasterX1

# Force environment variables for LIVE trading
export ALLOW_LIVE=true
export PAPER_MODE=false

# Remove any paper trading state files
rm -f state/paper_trading.lock state/safe_mode.lock

# Ensure execution boundary is correct
cat > state/execution_boundary.json << 'BOUNDARY'
{
  "account_binding": "BOUND",
  "execution_authorization": "AUTHORIZED",
  "bot_armed": true,
  "order_submission": "ENABLED",
  "withdrawals": "ENABLED",
  "transmission": "OPEN",
  "live_execution": true,
  "paper_trading": false,
  "safe_mode": false,
  "timestamp": "2026-09-01T16:54:02.088311"
}
BOUNDARY

# Run the master pipeline
python master_pipeline.py
