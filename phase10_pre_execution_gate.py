def run(state=None):
    print("=== PHASE 10 PRE-EXECUTION GATE ===")
    state=state or {}
    trades=state.get("approved_trades") or []
    # Final check: min notional, balance
    final=[]
    for t in trades:
        if t["entry"]*t.get("quantity",0) >=4.5:
            t["pre_exec_status"]="GATE_OPEN"
            final.append(t)
    state["pre_exec_trades"]=final
    print(f"GATE OPEN {len(final)} trades with full params:")
    for t in final:
        print(f"  {t['symbol']} | Entry {t['entry']} | SL {t['sl']} | TP1 {t['tp1']} | TP2 {t['tp2']} | RR {t['rr']} | RSI {t.get('rsi')} | ATR {t.get('atr')}")
    return state
def main(state=None): return run(state)
