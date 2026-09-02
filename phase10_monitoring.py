def run(state=None):
    print("=== PHASE 10.2 MONITORING ===")
    state=state or {}
    for t in state.get("phase10_trades",[]):
        print(f"Monitoring {t['symbol']} SL {t['sl']} TP {t['tp1']}/{t['tp2']}")
    return state
def main(state=None): return run(state)
