def process(ctx):
    ctx.data["P2"] = f"Auth OK for {ctx.data.get('symbols')}"
    ctx.data["auth"] = True
    print(f" P2 -> {ctx.data['P2']} | passing auth=True")
    return ctx
