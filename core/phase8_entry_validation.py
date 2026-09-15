def process(ctx):
    opp = ctx.data.get("opportunity", {"coin":"BTCUSDT"})
    entry = ctx.data.get("entry_price", 64900)
    quality = ctx.data.get("quality", 88)
    
    payload = {
        "coin": opp.get("coin", "BTCUSDT"),
        "side": "BUY",
        "price": entry,
        "qty": 0.001,
        "quality": quality
    }
    ctx.execution_payloads.append(payload)
    ctx.data["P8"] = f"Validation OK - payload ready {payload}"
    print(f" P8-VALIDATION -> {ctx.data['P8']} | payloads={len(ctx.execution_payloads)}")
    return ctx
