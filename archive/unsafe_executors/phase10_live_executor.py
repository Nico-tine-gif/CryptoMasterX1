#!/usr/bin/env python3
import os, json, time, hmac, hashlib, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
STATE_DIR=Path("state")
API_KEY=os.getenv("BINANCE_API_KEY"); API_SECRET=os.getenv("BINANCE_API_SECRET")
FAPI="https://fapi.binance.com"; LEVERAGE=5; HOLD_MINUTES=15
TP_PCT=0.012; SL_PCT=0.01; BLACKLIST=["FFUSDT","TUTUSDT"]

def sr(m,p,pa):
    pa['timestamp']=int(time.time()*1000); qs='&'.join([f"{k}={v}" for k,v in pa.items()])
    sig=hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return requests.request(m, f"{FAPI}{p}?{qs}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, timeout=15).json()
def bal():
    try:
        b=sr("GET","/fapi/v2/balance",{})
        return float([x for x in b if x['asset']=='USDT'][0]['availableBalance']) if isinstance(b,list) else 0
    except: return 0
def get_pos():
    try: return [p for p in sr("GET","/fapi/v2/positionRisk",{}) if float(p.get('positionAmt',0))!=0]
    except: return []
def close_all():
    for p in get_pos():
        try: sr("POST","/fapi/v1/order",{"symbol":p['symbol'],"side":"SELL" if float(p['positionAmt'])>0 else "BUY","type":"MARKET","quantity":abs(float(p['positionAmt']))})
        except: pass
def klines(sym, interval="1m", limit=100):
    try:
        r=requests.get(f"{FAPI}/fapi/v1/klines?symbol={sym}&interval={interval}&limit={limit}", timeout=10).json()
        return [float(x[4]) for x in r], [float(x[5]) for x in r]
    except: return [], []
def ema(data, period):
    if len(data)<period: return data[-1] if data else 0
    k=2/(period+1); e=data[0]
    for price in data[1:]: e=price*k+e*(1-k)
    return e
def rsi(data, period=14):
    if len(data)<period+1: return 50
    gains=[]; losses=[]
    for i in range(1,len(data)):
        d=data[i]-data[i-1]; gains.append(max(0,d)); losses.append(max(0,-d))
    avg_g=sum(gains[-period:])/period; avg_l=sum(losses[-period:])/period+0.00001
    return 100-(100/(1+avg_g/avg_l))

def check_pullback(sym):
    c1,v1=klines(sym,"1m",80)
    c5,_=klines(sym,"5m",50)
    if len(c1)<50: return False, "no data"
    e9=ema(c1,9); e20=ema(c1,20); e50=ema(c1,50)
    e20_5=ema(c5,20); last=c1[-1]; r=rsi(c1,14)
    mom5=(c5[-1]-c5[-5])/c5[-5]*100 if len(c5)>=5 else 0
    trend = last>e20 and e9>e20 and e20>e50 and c5[-1]>e20_5
    near_ema20 = abs(last-e20)/e20 < 0.006 # within 0.6% of EMA20 = pullback
    rsi_ok = 38 <= r <= 64
    mom_ok = mom5 > -0.5
    green = c1[-1] > c1[-2]
    ok = trend and near_ema20 and rsi_ok and mom_ok and green
    reason=f"${last:.3f} EMA9 {e9:.3f} EMA20 {e20:.3f} EMA50 {e50:.3f} RSI {r:.0f} Mom5 {mom5:+.2f}% nearEMA:{near_ema20} => {'BUY' if ok else 'WAIT'}"
    return ok, reason

def set_lev(sym):
    try: sr("POST","/fapi/v1/leverage",{"symbol":sym,"leverage":LEVERAGE})
    except: pass
def fmt_qty(sym,qty):
    try:
        ex=requests.get(f"{FAPI}/fapi/v1/exchangeInfo?symbol={sym}", timeout=10).json()
        step=float([f for f in ex['symbols'][0]['filters'] if f['filterType']=='LOT_SIZE'][0]['stepSize'])
        return round((qty//step)*step,6)
    except: return round(qty,3)

print(f"=== PULLBACK v2 LIVE | Bal ${bal():.2f} ===", flush=True)
last=time.time()-9999
while True:
    try:
        avail=bal(); pos=get_pos()
        print(f"[{time.strftime('%H:%M:%S')}] Bal ${avail:.2f} Pos {len(pos)} - scanning...", flush=True)
        if pos and (time.time()-last)>HOLD_MINUTES*60:
            close_all(); print("TIME CLOSE", flush=True); pos=[]; time.sleep(2); avail=bal()
        if not pos:
            os.system("python3 phase4_market_discovery.py >/dev/null 2>&1")
            try: data=json.loads((STATE_DIR/"phase4_market_discovery.json").read_text())
            except:
                print("No discovery file, retry 5s", flush=True); time.sleep(5); continue
            bulls=[b for b in data.get('safe_bulls',[]) if b['symbol'] not in BLACKLIST][:5]
            print(f"Bulls to check: {[b['symbol'] for b in bulls]}", flush=True)
            picked=None
            for b in bulls:
                sym=b['symbol']
                ok,reason=check_pullback(sym)
                print(f" {sym} {b['priceChangePercent']:+.1f}% -> {reason}", flush=True)
                if ok: picked=b; break
            if not picked:
                print("No pullback -> WAIT 30s (protecting capital)", flush=True)
                time.sleep(30); continue
            sym=picked['symbol']
            pr=float(requests.get(f"{FAPI}/fapi/v1/ticker/price?symbol={sym}",timeout=10).json()['price'])
            notional=min(avail*0.35*LEVERAGE, 45); qty=fmt_qty(sym, notional/pr)
            print(f">>> LONG {sym} {picked['priceChangePercent']:+.2f}% Notional ${notional:.0f} Qty {qty}", flush=True)
            set_lev(sym)
            o=sr("POST","/fapi/v1/order",{"symbol":sym,"side":"BUY","type":"MARKET","quantity":qty})
            print(f"Order result: {o}", flush=True)
            if 'orderId' in o:
                last=time.time()
                sl=pr*(1-SL_PCT); tp=pr*(1+TP_PCT)
                sr("POST","/fapi/v1/order",{"symbol":sym,"side":"SELL","type":"STOP_MARKET","stopPrice":round(sl,6),"closePosition":"true"})
                sr("POST","/fapi/v1/order",{"symbol":sym,"side":"SELL","type":"TAKE_PROFIT_MARKET","stopPrice":round(tp,6),"closePosition":"true"})
        time.sleep(10)
    except Exception as e:
        print(f"Err {e}", flush=True); time.sleep(5)
