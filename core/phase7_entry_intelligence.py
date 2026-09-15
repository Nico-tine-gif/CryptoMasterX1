def process(ctx):
    ctx.data["P7"] = f"Entry price 64900, qty 0.001 calculated"
    ctx.data["entry_price"] = 64900
    print(f" P7 -> {ctx.data['P7']} | passing entry")
    return ctx
