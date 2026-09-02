import json, os, time
from pathlib import Path
from dotenv import load_dotenv
from binance.client import Client

BASE=Path.home()/"CryptoMasterX1"
load_dotenv(BASE/".env")
d=json.loads((BASE/"state"/"account_binding.json").read_text())
client=Client(d["api_key"], d["api_secret"])

# load trades
STATE_DIR=BASE/"state"
trades=[]
try:
    trades=json.loads((STATE_DIR/"phase7_entry_intelligence.json").read_text()).get("trades") or []
except: pass
if not trades:
    trades=json.loads((STATE_DIR/"phase6_trade_intelligence.json").read_text()).get("trades") or []
trades=trades[:4]

print(f"LIVE BUY {len(trades)} x 5.2 USDT = quoteOrderQty (fixes LOT_SIZE)")

filled=[]
for t in trades:
    sym=t["symbol"]
    try:
        print(f" -> {sym} BUY 5.2 USDT market...")
        # Use quoteOrderQty to let Binance calculate qty - fixes LOT_SIZE
        order=client.order_market_buy(symbol=sym, quoteOrderQty=5.2)
        print(f"    ✅ FILLED {sym} qty={order['executedQty']} USDT={order['cummulativeQuoteQty']} id={order['orderId']}")
        filled.append(order)
        time.sleep(1)
    except Exception as e:
        print(f"    ❌ FAILED {sym}: {e}")

print(f"\nDONE {len(filled)}/{len(trades)} FILLED")
