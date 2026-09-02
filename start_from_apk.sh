#!/data/data/com.termux/files/usr/bin/bash
cd ~/CryptoMasterX1
termux-wake-lock
pkill -f auto_trader.py; sleep 1
nohup python3 auto_trader.py > auto.log 2>&1 &
