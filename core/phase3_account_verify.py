def process(ctx):
    ctx.data["P3"] = f"Balance 100 USDT verified, auth={ctx.data.get('auth')}"
    ctx.data["balance"] = 100
    print(f" P3 -> {ctx.data['P3']} | passing balance")
    return ctx
