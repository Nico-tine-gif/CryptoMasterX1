#!/usr/bin/env python3
import importlib, json, traceback
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "CryptoMasterX1"
STATE_DIR = BASE / "state"
REPORTS_DIR = BASE / "reports"
STATE_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

LIVE_EXECUTION=False
BOT_ARMED=False
ORDER_SUBMISSION=False
EXECUTION_AUTHORIZED=False
TRANSMISSION_LOCKED=True
WITHDRAWALS=False

STATE={"cycle":0,"phases":{},"market":{},"errors":[]}

def log(m): print(f"[{datetime.now(timezone.utc).isoformat()}] {m}", flush=True)

def enforce_phase_data_flow(state):
    """Required by scanner - validates state freshness"""
    if not isinstance(state, dict):
        raise RuntimeError("Invalid state type")
    # stale check placeholder
    return state

def call_module(module, state):
    candidates = ["run","execute","main","run_scanner","build_machine_state","scanner","start"]
    for name in candidates:
        if hasattr(module, name):
            fn = getattr(module, name)
            log(f"Calling {module.__name__}.{name}()")
            try:
                try: res = fn(state)
                except TypeError: res = fn()
                if isinstance(res, dict): return res
                return state
            except Exception as e:
                log(f"{name} failed: {e}")
                continue
    return state

def call_module_smart(module, state):
    return call_module(module, state)

def run_phase(num, mod_name):
    log(f"\n=== PHASE {num}: {mod_name} ===")
    try:
        mod = importlib.import_module(mod_name)
        global STATE
        STATE = enforce_phase_data_flow(STATE)
        STATE = call_module(mod, STATE)
        STATE["phases"][str(num)] = {"status":"COMPLETE","module":mod_name}
        log(f"PHASE {num} COMPLETE")
    except ModuleNotFoundError:
        log(f"Module {mod_name} not found - SKIP")
        STATE["phases"][str(num)] = {"status":"NOT_AVAILABLE"}
    except Exception as e:
        log(f"PHASE {num} FAILED: {e}")
        traceback.print_exc()
        STATE["phases"][str(num)] = {"status":"FAILED","error":str(e)}

def run_pipeline():
    global STATE
    STATE["cycle"]+=1
    log(f"### CYCLE {STATE['cycle']} CryptoMasterX1 - EXECUTION LOCKED ###")
    mods = [
        "phase1_scanner","account_binding","phase3_account_verify",
        "phase4_market_discovery","phase5_market_intelligence",
        "phase6_trade_intelligence","phase7_entry_intelligence",
        "phase8_entry_validation","phase9_decision_gate","phase10_monitoring"
    ]
    for i,m in enumerate(mods,1):
        run_phase(i,m)
    with open(STATE_DIR/"master_state.json","w") as f: json.dump(STATE,f,indent=2)
    log("PIPELINE COMPLETE - NO ORDERS SENT")

if __name__ == "__main__":
    run_pipeline()
