import json
from pathlib import Path
def run(state=None):
    print("=== PHASE 11 VERIFICATION ===")
    state=state or {}
    trades=state.get("phase10_trades") or state.get("pre_exec_trades") or []
    for t in trades:
        print(f"✅ FINAL TRADE {t['symbol']}")
        print(f"   Entry: {t['entry']}  RSI: {t.get('rsi')}  ATR: {t.get('atr')}")
        print(f"   SL: {t['sl']} ({t.get('sl_pct')}%)  TP1: {t['tp1']} TP2: {t['tp2']}")
        print(f"   RR: {t['rr']}  Confidence: {t.get('confidence')}  Qty: {t.get('quantity')}")
    Path("state/final_trade.json").write_text(json.dumps(trades[:1], indent=2))
    return state
def main(state=None): return run(state)
