#!/usr/bin/env python3
import json, pathlib, math
from binance.client import Client
BASE=pathlib.Path.home()/"CryptoMasterX1"
STATE=BASE/"state"
def get_client():
    import time
    b=json.loads((STATE/"account_binding.json").read_text())
    c=Client(b["api_key"], b["api_secret"])
    c.timestamp_offset=c.get_server_time()["serverTime"]-int(time.time()*1000)
    return c
def round_tick(p,tick):
    return float(f"{math.floor(p/tick)*tick:.10f}".rstrip('0').rstrip('.') or '0')

client=get_client()
usdt=float([b for b in client.get_account()["balances"] if b["asset"]=="USDT"][0]["free"])
print(f"USDT {usdt}")
data=json.loads((STATE/"phase1_universe.json").read_text())
qualified=data.get("qualified",[])
if not qualified:
    print("No trades"); exit()
cand=qualified[0]
sym=cand["symbol"]
kl5=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_5MINUTE, limit=100)
c5=[float(k[4]) for k in kl5]; h5=[float(k[2]) for k in kl5]; l5=[float(k[3]) for k in kl5]
price=c5[-1]
tr=[max(h-l, abs(h-c5[i-1]), abs(l-c5[i-1])) for i,(h,l) in enumerate(zip(h5[1:], l5[1:]),1)]
atr=sum(tr[-14:])/14
sl_dist=max(price*0.022, atr*1.5); tp1_dist=sl_dist*1.4; tp2_dist=sl_dist*2.6
info=client.get_symbol_info(sym)
lot=float([f for f in info["filters"] if f["filterType"]=="LOT_SIZE"][0]["stepSize"])
tick=float([f for f in info["filters"] if f["filterType"]=="PRICE_FILTER"][0]["tickSize"])
qty=math.floor((min(usdt*0.92,19.5)/price)/lot)*lot

trd={
"symbol":sym,"entry":round_tick(price,tick),"sl":round_tick(price-sl_dist,tick),"tp1":round_tick(price+tp1_dist,tick),"tp2":round_tick(price+tp2_dist,tick),
"quantity":qty,"lot_size":lot,"tick_size":tick,"confidence":cand["score"],"rsi":cand["rsi_5m"]
}
print(f"""
✅ TRADE {sym} Score {trd['confidence']}%
Entry {trd['entry']} SL {trd['sl']} TP1 {trd['tp1']} TP2 {trd['tp2']} Qty {qty}
""")
(STATE/"phase6_trade_intelligence.json").write_text(json.dumps({"trades":[trd]}, indent=2))
