import json, pathlib, time
from binance.client import Client
BASE=pathlib.Path.home()/"CryptoMasterX1"
STATE=BASE/"state"
def get_client():
    b=json.loads((STATE/"account_binding.json").read_text())
    c=Client(b["api_key"], b["api_secret"])
    c.timestamp_offset=c.get_server_time()["serverTime"]-int(time.time()*1000)
    return c
client=get_client()
for o in client.get_open_orders():
    try:
        client.cancel_order(symbol=o["symbol"], orderId=o["orderId"])
        print(f"Cancelled {o['symbol']}")
    except: pass
