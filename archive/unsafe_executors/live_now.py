import os, time, hmac, hashlib, requests, json
from dotenv import load_dotenv
load_dotenv()

API_KEY=os.getenv('BINANCE_API_KEY')
API_SECRET=os.getenv('BINANCE_API_SECRET')
BASE='https://fapi.binance.com'
SYMBOL='WLDUSDT'
LEVERAGE=3
RISK_PCT=0.02

def signed_req(method, path, params={}):
    params['timestamp']=int(time.time()*1000)
    qs='&'.join([f"{k}={v}" for k,v in params.items()])
    sig=hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url=f"{BASE}{path}?{qs}&signature={sig}"
    headers={'X-MBX-APIKEY': API_KEY}
    r=requests.request(method, url, headers=headers)
    return r.json()

print("=== CHECKING REAL BALANCE ===")
bal=signed_req('GET','/fapi/v2/balance',{})
if not isinstance(bal, list):
    print(f"API Error: {bal}")
    exit()
usdt_list=[b for b in bal if b.get('asset')=='USDT']
if not usdt_list:
    print("No USDT found in futures")
    exit()
usdt=usdt_list[0]
print(f"Futures Balance: {usdt['balance']} USDT")
print(f"Available: {usdt['availableBalance']} USDT")

if float(usdt['availableBalance']) < 5:
    print("ERROR: Need at least 5 USDT free")
    exit()

print(f"\n=== SETTING LEVERAGE {LEVERAGE}x FOR {SYMBOL} ===")
try:
    signed_req('POST','/fapi/v1/leverage',{'symbol':SYMBOL,'leverage':LEVERAGE})
    print("Leverage set")
except Exception as e:
    print(e)

price_data=requests.get(f"{BASE}/fapi/v1/ticker/price?symbol={SYMBOL}").json()
price=float(price_data['price'])
print(f"\n{SYMBOL} Price: {price}")

balance=float(usdt['availableBalance'])
risk_usdt=balance * RISK_PCT
qty=round(risk_usdt * LEVERAGE / price, 0)
if qty < 1:
    qty=1
print(f"Risk: ${risk_usdt:.2f} | Qty: {qty} WLD | Notional: ${qty*price:.2f}")

print("\n=== READY TO TRADE LIVE ===")
print("This will place REAL order on Binance.")
confirm=input("Type YES to open LONG now: ")

if confirm=="YES":
    order=signed_req('POST','/fapi/v1/order',{
        'symbol':SYMBOL,
        'side':'BUY',
        'type':'MARKET',
        'quantity':qty
    })
    print("\n*** LIVE ORDER PLACED ***")
    print(json.dumps(order, indent=2))
    print("\nCheck Binance App -> Futures -> Positions")
else:
    print("Cancelled - no trade placed")
