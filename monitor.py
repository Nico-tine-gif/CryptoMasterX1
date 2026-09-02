from binance.client import Client
import json, pathlib, time
BASE=pathlib.Path.home()/"CryptoMasterX1"
d=json.loads((BASE/"state"/"account_binding.json").read_text())
c=Client(d["api_key"], d["api_secret"])

targets={"SOXLBUSDT":103.24,"APTUSDT":0.563,"CRVUSDT":0.3659,"DOTUSDT":0.872}
print("Monitoring 4 coins - CTRL+C to stop")
while True:
    for sym, buy_price in targets.items():
        price=float(c.get_symbol_ticker(symbol=sym)["price"])
        pnl=(price-buy_price)/buy_price*100
        print(f"{sym} {price:.4f} pnl {pnl:+.2f}%")
        # auto sell +5% or -3%
        if pnl>=5 or pnl<=-3:
            asset=sym.replace("USDT","")
            bal=float(c.get_asset_balance(asset=asset)["free"])
            print(f"  -> SELL {asset} {bal}")
            # c.order_market_sell(symbol=sym, quantity=bal)
    time.sleep(10)
