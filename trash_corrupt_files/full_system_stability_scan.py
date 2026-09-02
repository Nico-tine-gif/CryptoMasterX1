import json
import py_compile
import subprocess
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
STATE = BASE / "state"

PHASE_FILES = {
    1: "phase1_scanner.py",
    3: "phase3_account_verify.py",
    4: "phase4_market_discovery.py",
    5: "phase5_market_intelligence.py",
    6: "phase6_trade_quality.py",
    7: "phase7_entry_intelligence.py",
    8: "phase8_entry_validation.py",
    9: "phase9_decision_gate.py",
    10: "phase10_trade_lifecycle.py",
    11: "phase11_full_system_verification.py",
}

STATE_FILES = {
    4: "phase4_market_discovery.json",
    5: "phase5_market_intelligence.json",
    6: "phase6_trade_quality.json",
    7: "phase7_entry_intelligence.json",
    8: "phase8_entry_validation.json",
    9: "phase9_decision_gate.json",
    10: "phase10_trade_lifecycle.json",
    11: "phase11_full_system_verification.json",
}

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"{label:<38}: {status} {detail}")
    return condition

print("=" * 78)
print("CRYPTOMASTERX1 — FULL SYSTEM STABILITY SCAN")
print("=" * 78)
print("UTC:", datetime.now(timezone.utc).isoformat())
print("MODE: READ-ONLY")
print("ORDER SUBMISSION: NOT PERFORMED")
print("EXISTING PHASE FILES: NOT MODIFIED")
print("=" * 78)

fails = 0

# ------------------------------------------------------------
# FILE INTEGRITY
# ------------------------------------------------------------

print("\nFILE INTEGRITY")
print("-" * 78)

for phase, filename in PHASE_FILES.items():
    path = BASE / filename

    if not check(
        f"Phase {phase} source",
        path.exists(),
        filename
    ):
        fails += 1
        continue

    try:
        py_compile.compile(
            str(path),
            doraise=True
        )
        check(
            f"Phase {phase} compile",
            True,
            "OK"
        )
    except Exception as exc:
        check(
            f"Phase {phase} compile",
            False,
            str(exc)
        )
        fails += 1

# ------------------------------------------------------------
# STATE INTEGRITY
# ------------------------------------------------------------

print("\nSTATE FILE INTEGRITY")
print("-" * 78)

states = {}

for phase, filename in STATE_FILES.items():
    path = STATE / filename

    if not check(
        f"Phase {phase} state",
        path.exists(),
        filename
    ):
        fails += 1
        continue

    data = load_json(path)

    if not check(
        f"Phase {phase} JSON",
        isinstance(data, dict),
        "VALID"
    ):
        fails += 1
        continue

    states[phase] = data

# ------------------------------------------------------------
# ------------------------------------------------------------
# PHASE 9
# ------------------------------------------------------------

print("\nPHASE 9 DECISION GATE")
print("-" * 78)

p9 = states.get(9, {})
g9 = p9.get("decision_gate", {})

p9_candidates = g9.get("phase8_candidates")
p9_evaluated = g9.get("evaluated")
p9_qualified = g9.get("qualified")
p9_rejected = g9.get("rejected")
p9_list = g9.get("qualified_candidates", [])

print(f"Phase 9 candidates                    : INFO {p9_candidates}")
print(f"Phase 9 evaluated                     : INFO {p9_evaluated}")
print(f"Phase 9 qualified                     : INFO {p9_qualified}")
print(f"Phase 9 rejected                      : INFO {p9_rejected}")
print(
    "Phase 9 qualified list                : INFO "
    + (str(len(p9_list)) if isinstance(p9_list, list) else "INVALID")
)

print("Phase 9 state interpretation          : INFO historical/runtime state")
print("Phase 9 hard-coded count validation   : DISABLED")

# ------------------------------------------------------------
# PHASE 10
# ------------------------------------------------------------

print("\nPHASE 10 TRADE LIFECYCLE")
print("-" * 78)

p10 = states.get(10, {})
l10 = p10.get("lifecycle", {})

p10_input = l10.get("phase9_candidates")
p10_eval = l10.get("evaluated")
p10_monitoring = l10.get("monitoring")
p10_closed = l10.get("closed")
p10_errors = l10.get("price_errors")
p10_results = l10.get("all_results", [])

print(f"Phase 10 input                        : INFO {p10_input}")
print(f"Phase 10 evaluated                    : INFO {p10_eval}")
print(f"Phase 10 monitoring                   : INFO {p10_monitoring}")
print(f"Phase 10 closed                       : INFO {p10_closed}")
print(f"Phase 10 price errors                 : INFO {p10_errors}")
print(
    "Phase 10 result count                 : INFO "
    + (str(len(p10_results)) if isinstance(p10_results, list) else "INVALID")
)

print("Phase 10 state interpretation         : INFO historical/runtime state")
print("Phase 10 hard-coded count validation  : DISABLED")

# ------------------------------------------------------------
# PHASE 11
# ------------------------------------------------------------

print("\nPHASE 11 FINAL VERIFICATION")
print("-" * 78)

p11 = states.get(11, {})
p11_status = p11.get("status")

print(f"Phase 11 stored status                 : INFO {p11_status}")
print("Phase 11 historical status validation  : DISABLED")
print("Phase 11 live verification             : NOT CLAIMED")

# HANDOFFS
# ------------------------------------------------------------

print("\nACTIVE HANDOFFS")
print("-" * 78)

handoffs = p11.get("handoff_verification", {})

for name, result in handoffs.items():
    passed = result.get("status") == "PASS"
    detail = ""

    if "from" in result:
        detail = f"{result.get('from')} -> {result.get('to')}"

    if not check(name, passed, detail):
        fails += 1

# ------------------------------------------------------------
# EXECUTION BOUNDARY
# ------------------------------------------------------------

print("\nEXECUTION SAFETY BOUNDARY")
print("-" * 78)

boundary_failures = 0

for phase in range(4, 11):
    data = states.get(phase, {})
    boundary = data.get("execution_boundary", {})

    safe = (
        boundary.get("execution_authorized") is False
        and boundary.get("order_submission") is False
        and boundary.get("bot_armed") is False
        and boundary.get("live_execution") is False
    )

    if not check(
        f"Phase {phase} execution boundary",
        safe,
        "LOCKED" if safe else "UNEXPECTED STATE"
    ):
        fails += 1
        boundary_failures += 1

# ------------------------------------------------------------
# RUNNER
# ------------------------------------------------------------

print("\nBACKGROUND RUNNER")
print("-" * 78)

runner = BASE / "run_cryptomasterx1.sh"

check(
    "Runner script exists",
    runner.exists(),
    str(runner)
)

try:
    wake = subprocess.run(
        ["command", "-v", "termux-wake-lock"],
        capture_output=True,
        text=True,
        shell=False
    )

    if wake.returncode == 0:
        check(
            "Termux wake-lock available",
            True,
            "FOUND"
        )
    else:
        print(
            "Termux wake-lock available            : "
            "INFO NOT INSTALLED"
        )
        print(
            "Wake-lock is optional; this is not a "
            "stability failure."
        )

except Exception as exc:
    print(
        "Termux wake-lock available            : "
        f"INFO CHECK UNAVAILABLE ({exc})"
    )
    print(
        "Wake-lock is optional; this is not a "
        "stability failure."
    )


# ------------------------------------------------------------
# RUNNING PROCESSES
# ------------------------------------------------------------

print("\nRUNNING PROCESSES")
print("-" * 78)

try:
    ps = subprocess.run(
        ["ps", "-ef"],
        capture_output=True,
        text=True
    )

    lines = [
        line for line in ps.stdout.splitlines()
        if (
            "cryptomasterx1" in line.lower()
            and "full_system_stability_scan" not in line
        )
    ]

    if lines:
        for line in lines:
            print(line)
    else:
        print("No CryptoMasterX1 process currently running.")

except Exception as exc:
    print("Process scan error:", exc)

# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

print()
print("=" * 78)

if fails == 0:
    print("CRYPTOMASTERX1 STABILITY RESULT: PASS")
    print("All tested components are internally consistent.")
else:
    print("CRYPTOMASTERX1 STABILITY RESULT: ATTENTION REQUIRED")
    print(f"Failed checks: {fails}")

print("=" * 78)

print("IMPORTANT:")
print("This scan is READ-ONLY.")
print("No phase was modified.")
print("No Binance order was submitted.")
print("No execution setting was changed.")
print("=" * 78)
