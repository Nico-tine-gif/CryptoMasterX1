def run(state=None):
    print("=== PHASE 9 DECISION GATE ===")
    state=state or {}
    trades=state.get("phase8_validated") or []
    # Sort by Phase5 confidence * RR
    trades=sorted(trades, key=lambda x: (x.get("phase5_confidence",0) or x.get("confidence",0))*x.get("rr",0), reverse=True)
    top=trades[:3]  # risk: max 3 positions
    for t in top:
        print(f"APPROVED {t['symbol']} Entry {t['entry']} SL {t['sl']} TP1 {t['tp1']} TP2 {t['tp2']} RR {t['rr']} RSI {t.get('rsi')}")
    state["approved_trades"]=top
    state["decision"]="APPROVED"
    return state
def main(state=None): return run(state)
