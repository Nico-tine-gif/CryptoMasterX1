def process(ctx):
    opp = ctx.data.get("opportunity")
    ctx.data["P5"] = f"Intelligence RSI 68 BUY signal for {opp['coin']}"
    ctx.market_intelligence["signal"] = "BUY"
    print(f" P5 -> {ctx.data['P5']} | passing signal")
    return ctx
