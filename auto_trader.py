import json, time
from pathlib import Path
from dotenv import load_dotenv
from binance.client import Client
BASE=Path.home()/"CryptoMasterX1"
load_dotenv(BASE/".env")
d=json.loads((BASE/"state"/"account_binding.json").read_text())
client=Client(d["api_key"], d["api_secret"])
STATE=BASE/"state"/"live_loop_state.json"
print("=== AUTO 24/7 TP+5 SL-3 LIVE ===", flush=True)
active=[]
if STATE.exists():
 try:
  active=json.loads(STATE.read_text()).get("active",[])
  print(f"RECOVERED {len(active)}", flush=True)
 except: pass
if not active:
 active=[
  {"symbol":"SOXLBUSDT","buy_price":103.24},
  {"symbol":"APTUSDT","buy_price":0.563},
  {"symbol":"CRVUSDT","buy_price":0.3659},
  {"symbol":"DOTUSDT","buy_price":0.872},
 ]
 STATE.write_text(json.dumps({"active":active}, indent=2))
 print(f"INJECTED {len(active)} bags", flush=True)

while True:
 try:
  if not active:
   print("[WAITING] No active bags", flush=True)
   time.sleep(30)
   continue
  print(f"Monitoring {len(active)} coins...", flush=True)
  still=[]
  for pos in active:
   sym=pos["symbol"]
   try:
    price=float(client.get_symbol_ticker(symbol=sym)["price"])
    buy=float(pos["buy_price"])
    pnl=(price-buy)/buy*100 if buy else 0
    print(f"{sym} {price} pnl {pnl:+.2f}%", flush=True)
    if pnl>=5 or pnl<=-3:
     asset=sym.replace("USDT","")
     free=float(client.get_asset_balance(asset=asset)['free'])
     print(f"SELL SIGNAL {sym} free={free}", flush=True)
     if free>0:
      o=client.order_market_sell(symbol=sym, quantity=free)
      print(f"SOLD {sym} -> {o['cummulativeQuoteQty']} USDT", flush=True)
     else:
      print(f"No balance {sym}", flush=True)
    else:
     still.append(pos)
   except Exception as e:
    print(f"ERR {sym}: {e}", flush=True)
    still.append(pos)
   time.sleep(1)
  active=still
  STATE.write_text(json.dumps({"active":active}, indent=2))
  time.sleep(10)
 except Exception as e:
  print(f"LOOP CRASH {e}", flush=True)
  time.sleep(15)
