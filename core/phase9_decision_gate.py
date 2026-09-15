def process(ctx):
    ctx.gate_passed = True
    ctx.data["P9"] = f"GATE PASSED - authorized to execute"
    print(f" P9 -> {ctx.data['P9']} | gate={ctx.gate_passed}")
    return ctx
