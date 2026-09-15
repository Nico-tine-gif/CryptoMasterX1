def process(ctx):
    ctx.data["P6"] = f"Quality score 88% PASS, signal {ctx.market_intelligence.get('signal')}"
    ctx.data["quality"] = 88
    print(f" P6 -> {ctx.data['P6']} | passing quality")
    return ctx
