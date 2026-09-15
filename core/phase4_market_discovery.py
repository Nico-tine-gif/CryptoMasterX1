def process(ctx):
    ctx.data["P4"] = f"Discovery: BTCUSDT UP trend"
    ctx.data["opportunity"] = {"coin":"BTCUSDT","trend":"UP","price":64900}
    print(f" P4 -> {ctx.data['P4']} | passing opportunity")
    return ctx
