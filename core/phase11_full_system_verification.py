def process(ctx):
    ctx.system_verification_status = "VERIFIED"
    ctx.data["P11"] = f"Loop {ctx.loop_count} VERIFIED - full ctx: {list(ctx.data.keys())}"
    print(f" P11 -> {ctx.data['P11']}")
    print(f" 📦 CONTEXT CARRY TO NEXT LOOP: symbols={ctx.data.get('symbols')} -> opportunity -> signal -> gate")
    return ctx
