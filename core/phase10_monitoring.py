def process(ctx):
    ctx.data["P10"] = f"Monitoring active, gate {ctx.gate_passed}"
    ctx.active_positions["BTCUSDT"] = {"pnl":"+1.2%"}
    print(f" P10 -> {ctx.data['P10']} | positions {ctx.active_positions}")
    return ctx
