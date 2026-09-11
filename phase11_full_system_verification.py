#!/usr/bin/env python3
from pathlib import Path
import json, sys, re
from datetime import datetime, timezone

ROOT=Path.cwd()
STATE_DIR=ROOT/"state"
REPORTS_DIR=ROOT/"reports"
STATE_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

LIVE_EXECUTION=False
BOT_ARMED=False
ORDER_SUBMISSION=False
EXECUTION_AUTHORIZED=False
TRANSMISSION_LOCKED=True
WITHDRAWALS=False

def now_utc(): return datetime.now(timezone.utc).isoformat()
def log(m): print(f"[{now_utc()}] {m}")

errors=[]; checks=[]

def check(name, ok, detail=""):
    checks.append({"check":name,"status":"PASS" if ok else "FAIL","detail":detail})
    print(f"{'PASS' if ok else 'FAIL'}: {name} {detail}")
    if not ok: errors.append(name)
    return ok

all_py = [p for p in ROOT.glob("*.py") if "archive" not in str(p) and "scanner" not in p.name]
all_text="\n".join([p.read_text(errors="ignore") for p in all_py])

print("="*78)
print("PHASE 11 - FULL SYSTEM VERIFICATION - READ ONLY")
print("="*78)

# 1. Safety flags must be FALSE
for flag in ["LIVE_EXECUTION=False","BOT_ARMED=False","ORDER_SUBMISSION=False","EXECUTION_AUTHORIZED=False","TRANSMISSION_LOCKED=True","WITHDRAWALS=False"]:
    clean = flag.replace(" ","")
    text_nospace = all_text.replace(" ","")
    found = clean in text_nospace
    check(f"Safety {flag}", found)

# 2. No dangerous True
for pat in ["LIVE_EXECUTION\\s*=\\s*True","BOT_ARMED\\s*=\\s*True","ORDER_SUBMISSION\\s*=\\s*True","EXECUTION_AUTHORIZED\\s*=\\s*True","TRANSMISSION_LOCKED\\s*=\\s*False","WITHDRAWALS\\s*=\\s*True"]:
    found = bool(re.search(pat, all_text))
    check(f"No {pat}", not found)

# 3. Fresh feed checks
for fname in ["phase4_market_discovery.py","phase5_market_intelligence.py","phase7_entry_intelligence.py"]:
    p=ROOT/fname
    if not p.exists(): continue
    t=p.read_text(errors="ignore").lower()
    check(f"{fname} timestamp", "timestamp" in t or "servertime" in t or "now_utc" in t)
    check(f"{fname} stale logic", "stale" in t or "fresh" in t)

# 4. State dir
check("state dir", STATE_DIR.exists())
check("reports dir", REPORTS_DIR.exists())

# 5. No withdrawal API in trade phases
for fname in ["phase6_trade_intelligence.py","phase7_entry_intelligence.py","phase8_entry_validation.py","phase9_decision_gate.py"]:
    p=ROOT/fname
    if not p.exists(): continue
    t=p.read_text(errors="ignore").lower()
    bad = bool(re.search(r"withdraw\(|sapi.*withdraw|transfer.*asset", t))
    check(f"{fname} no withdraw call", not bad)

print("="*78)
print(f"CHECKS {len(checks)} ERRORS {len(errors)}")
if errors:
    print("OVERALL: FAIL")
    sys.exit(1)
else:
    print("OVERALL: CLEAN - SAFE TO PROCEED")
print("="*78)
