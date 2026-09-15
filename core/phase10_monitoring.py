import importlib.util
from pathlib import Path

_adapter_path = Path(__file__).parent / "spot_execution_adapter.py"
_spec = importlib.util.spec_from_file_location("spot_execution_adapter", _adapter_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SpotExecutionAdapter = _mod.SpotExecutionAdapter

def process(ctx):
    adapter = SpotExecutionAdapter(dry_run=True)
    positions = adapter.get_positions()
    ctx.active_positions = positions
    ctx.data["P10"] = f"Monitoring {len(positions)} positions, {len(adapter.orders)} total orders"
    print(f" P10-MONITOR -> {ctx.data['P10']} | {positions}")
    return ctx
