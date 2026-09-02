#!/usr/bin/env python3
import requests, json
from pathlib import Path
from datetime import datetime
STATE_DIR=Path("state"); REPORT_DIR=Path("reports")
STATE_DIR.mkdir(exist_ok=True); REPORT_DIR.mkdir(exist_ok=True)

def get_all_usdt():
    try:
        data=requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=15).json()
        spot=[s for s in data['symbols'] if s['symbol'].endswith('USDT') and s['status']=='TRADING']
        return [s['symbol'] for s in spot]
    except: return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

def get_24h(symbols):
    try:
        all24=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=15).json()
        m={x['symbol']:x for x in all24}
        return [m[s] for s in symbols if s in m]
    except: return []

print("DISCOVERING BINANCE SPOT/USDT UNIVERSE")
symbols=get_all_usdt()
print(f"Eligible Spot USDT markets : {len(symbols)}")
tickers=get_24h(symbols)
qualified=[]; bulls=[]; bears=[]
for t in tickers:
    try:
        vol=float(t['quoteVolume']); ch=float(t['priceChangePercent']); trades=int(t['count'])
        if vol>5000000 and abs(ch)>1.0:
            q=70+abs(ch)
            qualified.append(t)
            if ch>0: bulls.append((t['symbol'], ch, q, vol, trades))
            else: bears.append((t['symbol'], ch, q, vol, trades))
    except: pass

bulls=sorted(bulls, key=lambda x: x[2], reverse=True)[:100]
bears=sorted(bears, key=lambda x: x[2], reverse=True)[:100]
all_markets = bulls + bears

print(f"Qualified markets : {len(all_markets)} Bull {len(bulls)} Bear {len(bears)}")

# Build OLD structure that phase5 expects
markets_list = [{"symbol": b[0], "priceChangePercent": b[1], "quality": b[2]} for b in all_markets]

out={
  "timestamp": datetime.utcnow().isoformat()+"+00:00",
  "eligible": len(symbols),
  "discovery": {
    "markets": markets_list,
    "qualified_markets": len(markets_list),
    "eligible_markets": len(symbols)
  },
  # also keep new keys for display
  "safe_bulls": [{"symbol":b[0],"priceChangePercent":b[1],"quality":b[2],"volume":b[3],"trades":b[4]} for b in bulls],
  "safe_bears": [{"symbol":b[0],"priceChangePercent":b[1],"quality":b[2],"volume":b[3],"trades":b[4]} for b in bears],
}

(STATE_DIR/"phase4_market_discovery.json").write_text(json.dumps(out, indent=2))
print(f"State saved with discovery.markets = {len(markets_list)}")

print("\nTOP BULLISH")
for i,b in enumerate(bulls[:10],1): print(f"{i}. {b[0]} {b[1]:+.2f}%")
print("\nTOP BEARISH")
for i,b in enumerate(bears[:10],1): print(f"{i}. {b[0]} {b[1]:+.2f}%")
