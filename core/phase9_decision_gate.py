import importlib.util
from pathlib import Path

# Load adapter without relative import
_adapter_path = Path(__file__).parent / "spot_execution_adapter.py"
_spec = importlib.util.spec_from_file_location("spot_execution_adapter", _adapter_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SpotExecutionAdapter = _mod.SpotExecutionAdapter

def process(ctx):
    quality = ctx.data.get("quality", 0)
    if quality >= 75 and ctx.data.get("opportunity"):
        ctx.gate_passed = True
        adapter = SpotExecutionAdapter(dry_run=True)
        if ctx.execution_payloads:
            last = ctx.execution_payloads[-1]
            result = adapter.execute(last)
            ctx.data["last_execution"] = result
        ctx.data["P9"] = f"GATE PASSED - executed {ctx.data.get('last_execution')}"
    else:
        ctx.gate_passed = False
        ctx.data["P9"] = f"GATE BLOCKED - quality {quality} < 75"
    print(f" P9-GATE -> {ctx.data['P9']} | gate={ctx.gate_passed}")
    return ctx
