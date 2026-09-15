def process(ctx):
    ctx.data["P1"] = "Scanned BTC, ETH, SOL - 3 symbols"
    ctx.data["symbols"] = ["BTCUSDT","ETHUSDT","SOLUSDT"]
    ctx.market_intelligence["symbols"] = ctx.data["symbols"]
    print(f" P1 -> {ctx.data['P1']} | output: {ctx.data['symbols']}")
    return ctx
