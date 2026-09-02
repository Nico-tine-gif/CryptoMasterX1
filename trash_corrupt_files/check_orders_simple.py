import requests, time, hmac, hashlib

with open("binance.key") as f:
    lines=[l.strip() for l in f.read().splitlines() if l.strip()]
    API_KEY=lines[0].split("=")[-1].strip().strip('"').strip("'") if "=" in lines[0] else lines[0]
    API_SECRET=lines[1].split("=")[-1].strip().strip('"').strip("'") if len(lines)>1 and "=" in lines[1] else lines[1]

def signed_req(path):
    ts=int(time.time()*1000)
    qs=f"timestamp={ts}"
    sig=hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url=f"https://fapi.binance.com{path}?{qs}&signature={sig}"
    r=requests.get(url, headers={"X-MBX-APIKEY": API_KEY}, timeout=10)
    return r.json()

print("=== CHECKING ORDERS & POSITIONS ===")
bal=signed_req("/fapi/v2/balance")
if isinstance(bal, dict) and 'code' in bal:
    print(f"Balance ERROR: {bal} -> Fix API permissions")
else:
    for b in bal:
        if b.get('asset')=='USDT':
            print(f"Balance: {b['balance']} USDT | PnL: {b['crossUnPnl']}")

pos=signed_req("/fapi/v2/positionRisk")
if isinstance(pos, dict): print("Positions error:", pos)
else:
    opens=[p for p in pos if float(p.get('positionAmt',0))!=0]
    print("No open positions - READY" if not opens else opens)

ords=signed_req("/fapi/v1/openOrders")
if isinstance(ords, dict): print("Orders error:", ords)
else:
    print("No open orders - READY" if not ords else ords)
print("=== DONE ===")
