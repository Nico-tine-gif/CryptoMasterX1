def process(ctx):
    ctx.data["P8"] = f"Validation OK price {ctx.data.get('entry_price')}"
    ctx.execution_payloads.append({"price": ctx.data.get("entry_price")})
    print(f" P8 -> {ctx.data['P8']} | payloads={len(ctx.execution_payloads)}")
    return ctx
