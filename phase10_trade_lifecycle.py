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

def round_tick(price, tick):
    # proper tick rounding
    return float(f"{math.floor(price/tick)*tick:.10f}".rstrip('0').rstrip('.') or '0')

def main(*a,**k):
    data=json.loads((STATE/"phase7_entry_intelligence.json").read_text()) if (STATE/"phase7_entry_intelligence.json").exists() else {}
    trades=data.get("accepted",[])
    if not trades:
        data2=json.loads((STATE/"phase6_trade_intelligence.json").read_text()) if (STATE/"phase6_trade_intelligence.json").exists() else {}
        trades=data2.get("trades",[])
    client=get_client()

    for tr in trades:
        sym=tr["symbol"]
        info=client.get_symbol_info(sym)
        tick=float([f for f in info["filters"] if f["filterType"]=="PRICE_FILTER"][0]["tickSize"])
        lot=float([f for f in info["filters"] if f["filterType"]=="LOT_SIZE"][0]["stepSize"])

        # Use tick-rounded values from phase6
        entry=round_tick(tr.get("entry_tick", tr["entry"]), tick)
        sl=round_tick(tr.get("sl_tick", tr["sl"]), tick)
        tp1=round_tick(tr.get("tp1_tick", tr["tp1"]), tick)
        tp2=round_tick(tr.get("tp2_tick", tr["tp2"]), tick)
        qty=math.floor(float(tr["quantity"])/lot)*lot

        print(f"\n=== LIVE EXECUTING {sym} ===")
        print(f"Entry {entry} SL {sl}({tr['sl_pct']}%) TP1 {tp1}({tr['tp1_pct']}%) TP2 {tp2}({tr['tp2_pct']}%) RR {tr['rr']} RSI {tr['rsi']} Conf {tr['confidence']}%")
        print(f"BUY {qty} @ ~{entry} Notional ${round(qty*entry,2)}")

        try:
            o=client.order_market_buy(symbol=sym, quantity=qty)
            print(f"✅ FILLED {o['executedQty']} USDT {o['cummulativeQuoteQty']}")
            time.sleep(1)

            # Get real balance after buy
            bal=float([b for b in client.get_account()["balances"] if b["asset"]==sym.replace("USDT","")][0]["free"])
            sell_qty=math.floor(bal/lot)*lot
            if sell_qty==0:
                print(f"No balance to sell for {sym}")
                continue

            # Try OCO - if fails, place separate SL and TP
            try:
                client.order_oco_sell(symbol=sym, quantity=sell_qty, price=tp1, stopPrice=sl, stopLimitPrice=sl, stopLimitTimeInForce='GTC')
                print(f"✅ OCO SL {sl} + TP1 {tp1} qty {sell_qty}")
            except Exception as e:
                print(f"OCO fail {e} - placing separate orders")
                try:
                    # SL as stop-loss-limit
                    client.create_order(symbol=sym, side='SELL', type='STOP_LOSS_LIMIT', quantity=sell_qty, price=sl, stopPrice=sl, timeInForce='GTC')
                    print(f"✅ SL placed {sl} qty {sell_qty}")
                except Exception as e2:
                    print(f"SL fail {e2}")
                try:
                    tp1_qty=math.floor((sell_qty/2)/lot)*lot
                    client.order_limit_sell(symbol=sym, quantity=tp1_qty, price=tp1)
                    print(f"✅ TP1 placed {tp1} qty {tp1_qty}")
                except Exception as e3:
                    print(f"TP1 fail {e3}")
                try:
                    tp2_qty=math.floor((sell_qty/2)/lot)*lot
                    client.order_limit_sell(symbol=sym, quantity=tp2_qty, price=tp2)
                    print(f"✅ TP2 placed {tp2} qty {tp2_qty}")
                except Exception as e4:
                    print(f"TP2 fail {e4}")

        except Exception as e:
            print(f"BUY fail {e}")

if __name__=="__main__": main()
