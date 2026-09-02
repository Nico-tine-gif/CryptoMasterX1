#!/usr/bin/env python3
import json, pathlib, time, math
from binance.client import Client
BASE=pathlib.Path.home()/"CryptoMasterX1"
STATE=BASE/"state"
def get_client():
    b=json.loads((STATE/"account_binding.json").read_text())
    c=Client(b["api_key"], b["api_secret"])
    c.timestamp_offset=c.get_server_time()["serverTime"]-int(time.time()*1000)
    return c
def round_tick(p,tick):
    return float(f"{math.floor(p/tick)*tick:.10f}".rstrip('0').rstrip('.') or '0')

client=get_client()
data=json.loads((STATE/"phase6_trade_intelligence.json").read_text())
trades=data.get("trades",[])
if not trades: print("No trades"); exit()
for tr in trades:
    sym=tr["symbol"]; qty=tr["quantity"]
    info=client.get_symbol_info(sym)
    tick=float([f for f in info["filters"] if f["filterType"]=="PRICE_FILTER"][0]["tickSize"])
    lot=float([f for f in info["filters"] if f["filterType"]=="LOT_SIZE"][0]["stepSize"])
    entry=round_tick(tr["entry"],tick); sl=round_tick(tr["sl"],tick); tp1=round_tick(tr["tp1"],tick); tp2=round_tick(tr["tp2"],tick)
    print(f"=== BUY {sym} {qty} @ {entry} SL {sl} TP1 {tp1} TP2 {tp2} ===")
    try:
        o=client.order_market_buy(symbol=sym, quantity=qty)
        print(f"✅ FILLED {o['executedQty']}")
        time.sleep(1)
        bal=float([b for b in client.get_account()["balances"] if b["asset"]==sym.replace("USDT","")][0]["free"])
        sell_qty=math.floor(bal/lot)*lot
        # SL
        try:
            client.create_order(symbol=sym, side='SELL', type='STOP_LOSS_LIMIT', quantity=sell_qty, price=sl, stopPrice=sl, timeInForce='GTC')
            print(f"✅ SL {sl}")
        except Exception as e: print(f"SL fail {e}")
        # TPs - split 50/50
        try:
            q1=math.floor((sell_qty/2)/lot)*lot
            q2=sell_qty-q1
            q2=math.floor(q2/lot)*lot
            if q1>0:
                client.order_limit_sell(symbol=sym, quantity=q1, price=tp1)
                print(f"✅ TP1 {tp1} qty {q1}")
            if q2>0:
                client.order_limit_sell(symbol=sym, quantity=q2, price=tp2)
                print(f"✅ TP2 {tp2} qty {q2}")
        except Exception as e: print(f"TP fail {e}")
    except Exception as e: print(f"BUY fail {e}")
