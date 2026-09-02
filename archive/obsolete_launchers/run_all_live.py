#!/usr/bin/env python3
import subprocess, time, json, os, sys
from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent

def run_phase(file):
    print(f"\n>>> RUNNING {file}")
    try:
        result=subprocess.run(
            [sys.executable, str(BASE_DIR/file)],
            capture_output=True, text=True, timeout=300
        )
        print(result.stdout[-1000:])
        if result.returncode!=0:
            print(f"Error in {file}: {result.stderr[-1000:]}")
            return False
        return True
    except Exception as e:
        print(f"Failed {file}: {e}")
        return False

print("=== CRYPTOMASTERX1 FULL AUTO LOOP ===")
print("Flow: phase4 → phase5 → phase6 → phase7 → phase8 → phase9 → phase10 executor (trades)")
while True:
    start=time.time()
    print(f"\n\n========== NEW CYCLE {time.strftime('%H:%M:%S')} ==========")
    # 1. Market discovery
    if not run_phase("phase4_market_discovery.py"): time.sleep(10); continue
    # 2. Intelligence
    if not run_phase("phase5_market_intelligence.py"): time.sleep(10); continue
    # 3. Trade quality
    if not run_phase("phase6_trade_quality.py"): time.sleep(10); continue
    # 4. Entry intelligence
    if not run_phase("phase7_entry_intelligence.py"): time.sleep(10); continue
    # 5. Validation
    if not run_phase("phase8_entry_validation.py"): time.sleep(10); continue
    # 6. Decision gate
    if not run_phase("phase9_decision_gate.py"): time.sleep(10); continue

    # Show qualified
    try:
        data=json.loads((BASE_DIR/"state"/"phase9_decision_gate.json").read_text())
        cands=data.get('decision_gate',{}).get('qualified_candidates',[])
        print(f"\nQUALIFIED THIS CYCLE: {len(cands)} -> {[c['symbol'] for c in cands[:5]]}")
    except: pass

    # 7. Trade lifecycle (monitor old)
    run_phase("phase10_trade_lifecycle.py")

    # 8. LIVE EXECUTOR - trades any new qualified (import function)
    print("\n>>> EXECUTING LIVE TRADES")
    try:
        subprocess.run([sys.executable, str(BASE_DIR/"phase10_live_executor.py")], timeout=30)
    except subprocess.TimeoutExpired:
        print("Executor running 30s then continuing (it loops, we kill cycle)")
        # Kill executor loop after one pass - we want single pass
        pass

    # Actually do single pass trade directly
    try:
        from phase10_live_executor import load_phase9, place_order
        for c in load_phase9():
            print(f"Auto trading {c['symbol']}")
            place_order(c)
            time.sleep(2)
    except Exception as e:
        print(f"Live trade error: {e}")
        import traceback; traceback.print_exc()

    elapsed=time.time()-start
    print(f"\nCycle done in {elapsed:.1f}s - Sleep 60s before next scan")
    time.sleep(60)
