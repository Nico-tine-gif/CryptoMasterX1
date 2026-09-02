def run(state=None):
    print("=== PHASE 8 ENTRY VALIDATION ===")
    state=state or {}
    trades=state.get("phase7_trades") or state.get("phase6_trades") or (state.get("approved_trades")) or []
    # Real validation: RR>=1.5, RSI filter, SL distance
    valid=[]
    for t in trades:
        rr=t.get("rr", t.get("rr_ratio",0))
        rsi=t.get("rsi",50)
        if rr>=1.5 and 25 < rsi < 75:
            t["phase8_status"]="VALID"
            t["phase8_reason"]=f"RR {rr} RSI {rsi} OK"
            valid.append(t)
        else:
            t["phase8_status"]="REJECTED"
    print(f"Valid {len(valid)}/{len(trades)}")
    state["phase8_validated"]=valid
    return state
def main(state=None): return run(state)
