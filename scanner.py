#!/usr/bin/env python3
import json, pathlib, time
from binance.client import Client
BASE=pathlib.Path.home()/"CryptoMasterX1"
STATE=BASE/"state"; STATE.mkdir(exist_ok=True)
def get_client():
    b=json.loads((STATE/"account_binding.json").read_text())
    c=Client(b["api_key"], b["api_secret"])
    c.timestamp_offset=c.get_server_time()["serverTime"]-int(time.time()*1000)
    return c
def ema(d,n):
    k=2/(n+1); e=d[0]
    for p in d[1:]: e=p*k+e*(1-k)
    return e
def rsi(c,p=14):
    d=[c[i]-c[i-1] for i in range(1,len(c))]
    g=sum(x for x in d[-p:] if x>0)/p; lo=-sum(x for x in d[-p:] if x<0)/p
    return 100-100/(1+g/lo) if lo!=0 else 50
def fvg_count(kl):
    cnt=0
    for i in range(2,len(kl)):
        if float(kl[i-2][2]) < float(kl[i][3]): cnt+=1
    return cnt
def fakeout(c,h,l):
    f=0
    for i in range(1,len(c)):
        body=abs(c[i]-c[i-1])
        if body==0: continue
        up=h[i]-max(c[i],c[i-1]); lo=min(c[i],c[i-1])-l[i]
        if up>body*2.5 or lo>body*2.5: f+=1
    return f

client=get_client()
tickers=client.get_ticker()
uni=[t for t in tickers if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>1000000 and "UP" not in t["symbol"] and "DOWN" not in t["symbol"]]
print(f"[SCANNER] UNIVERSE {len(uni)} coins")
bulls=[]
for t in uni:
    sym=t["symbol"]
    try:
        kl15=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
        kl5=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_5MINUTE, limit=100)
        c15=[float(k[4]) for k in kl15]; h15=[float(k[2]) for k in kl15]; l15=[float(k[3]) for k in kl15]
        c5=[float(k[4]) for k in kl5]; h5=[float(k[2]) for k in kl5]; l5=[float(k[3]) for k in kl5]; v5=[float(k[5]) for k in kl5]
        price=c5[-1]
        e20_15=ema(c15[-20:],20); e50_15=ema(c15[-50:],50)
        e20_5=ema(c5[-20:],20); e50_5=ema(c5[-50:],50)
        r15=rsi(c15); r5=rsi(c5)
        bull_15 = price>e20_15 and e20_15>e50_15
        bull_5 = c5[-1]>e20_5 and e20_5>e50_5
        high5=max(h5[-12:]); pullback=(high5-price)/high5*100 if high5>0 else 0
        is_pullback = 0.3 <= pullback <= 6.0
        vol_surge=v5[-1]/(sum(v5[-20:])/20) if sum(v5[-20:])>0 else 1
        fvg=fvg_count(kl15)+fvg_count(kl5)
        fk=fakeout(c15,h15,l15)+fakeout(c5,h5,l5)
        score=0
        if bull_15: score+=20
        if bull_5: score+=15
        if bull_15 and bull_5: score+=15
        if is_pullback and bull_15: score+=20
        elif bull_15: score+=10
        if 38 < r15 < 72 and 38 < r5 < 72: score+=15
        if vol_surge>1.05: score+=5
        if vol_surge>1.25: score+=5
        if fvg>=1: score+=10
        if fvg>=2: score+=5
        if fk>=5: score-=25
        elif fk>=3: score-=10
        score=min(100,max(0,score))
        if bull_15 and bull_5:
            bulls.append({"symbol":sym,"price":price,"score":score,"pullback":round(pullback,2),"rsi_5m":round(r5,1),"rsi_15m":round(r15,1),"volx":round(vol_surge,2),"fvg":fvg,"fakes":fk,"vol":float(t["quoteVolume"]),"change":round(float(t["priceChangePercent"]),2)})
    except: continue

bulls=sorted(bulls, key=lambda x: x["score"], reverse=True)
qualified=[b for b in bulls if b["score"]>=65]
qualified75=[b for b in bulls if b["score"]>=75]
print(f"🟢 BULLS {len(bulls)} | >=75% {len(qualified75)} | >=65% {len(qualified)}")
for q in bulls[:15]:
    g="✅" if q["score"]>=75 else "⚠️" if q["score"]>=65 else " "
    print(f"{g} {q['symbol']} {q['score']}% PB{q['pullback']}% RSI{q['rsi_5m']}/{q['rsi_15m']} VOLx{q['volx']} FVG{q['fvg']} F{q['fakes']} {q['change']}%")
trade_pool = qualified75 if qualified75 else qualified
(STATE/"phase1_universe.json").write_text(json.dumps({"qualified":trade_pool,"qualified75":qualified75,"bulls":bulls}, indent=2))
