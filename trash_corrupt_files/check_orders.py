import os, time, hmac, hashlib, requests
from dotenv import load_dotenv
load_dotenv()
API_KEY=os.getenv("BINANCE_API_KEY")
API_SECRET=os.getenv("BINANCE_API_SECRET")
FAPI="https://fapi.binance.com"
def signed_req(m,p,pa):
    pa['timestamp']=int(time.time()*1000)
    qs='&'.join([f"{k}={v}" for k,v in pa.items()])
    sig=hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    r=requests.request(m, f"{FAPI}{p}?{qs}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, timeout=10)
    return r.json()
bal=signed_req("GET","/fapi/v2/balance",{})
avail=float([b for b in bal if b['asset']=='USDT'][0]['availableBalance']) if isinstance(bal,list) else 0
pos=signed_req("GET","/fapi/v2/positionRisk",{})
opens=[p for p in pos if float(p.get('positionAmt',0))!=0]
print(f"Balance available: ${avail:.2f}")
if not opens:
    print("No open positions - READY")
else:
    total=0
    for p in opens:
        pnl=float(p['unRealizedProfit'])
        total+=pnl
        print(f"OPEN: {p['symbol']} {p['positionAmt']} Entry {p['entryPrice']} Mark {p['markPrice']} PnL ${pnl:.2f} ({float(p['unRealizedProfit'])/10:.2f}%)")
    print(f"Total Unrealized: ${total:.2f}")
