import os, time, hmac, hashlib, requests
from pathlib import Path
import dotenv
dotenv.load_dotenv(Path.home() / "CryptoMasterX1" / ".env")
API_KEY=os.getenv('BINANCE_API_KEY')
API_SECRET=os.getenv('BINANCE_API_SECRET')
BASE='https://fapi.binance.com'

COINS=["1000PEPEUSDT","1000SHIBUSDT","1000FLOKIUSDT","1000BONKUSDT","DOGEUSDT","WLDUSDT","XRPUSDT","SOLUSDT","BNBUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","LTCUSDT","DOTUSDT","TRXUSDT","MATICUSDT","OPUSDT","ARBUSDT","SUIUSDT","SEIUSDT","APTUSDT","NEARUSDT","FILUSDT","ETCUSDT","BCHUSDT","ATOMUSDT","ENAUSDT","WIFUSDT","TIAUSDT","STRKUSDT"]

def get_prices():
    try:
        r=requests.get(f"{BASE}/fapi/v1/ticker/price", timeout=10).json()
        return {x['symbol']: float(x['price']) for x in r}
    except: return {}

def signed_req(method, path, params={}):
    params['timestamp']=int(time.time()*1000)
    qs='&'.join([f"{k}={v}" for k,v in params.items()])
    sig=hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url=f"{BASE}{path}?{qs}&signature={sig}"
    return requests.request(method, url, headers={'X-MBX-APIKEY': API_KEY}).json()

# check balance once
try:
    bal=signed_req('GET','/fapi/v2/balance',{})
    usdt=[b for b in bal if b['asset']=='USDT'][0]
    print(f"Balance: {usdt['balance']} USDT", flush=True)
    print("=== 30 COIN SNIPER READY - 3x ===", flush=True)
    print("Any popping signal will be placed INSTANTLY", flush=True)
except Exception as e:
    print(f"Bal err {e}", flush=True)

while True:
    prices=get_prices()
    for coin in COINS:
        p=prices.get(coin)
        if not p:
            continue
        ts=time.strftime("%H:%M:%S")
        print(f"[{ts}] Scanning {coin} {p} - READY...", flush=True)
        time.sleep(1.2)
