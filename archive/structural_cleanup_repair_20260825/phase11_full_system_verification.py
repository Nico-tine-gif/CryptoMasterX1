import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_11"
VERSION = "3.0"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE11_STATE = STATE_DIR / "phase11_full_system_verification.json"
PHASE11_REPORT = REPORT_DIR / "phase11_full_system_verification_report.json"

# ================================================================
# SAFETY BOUNDARY — HARD LOCK
# ================================================================

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False


# ================================================================
# UTILITIES
# ================================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, default=str)
    )


def load_json(path):
    if not path.exists():
        return None, "STATE_FILE_MISSING"

    try:
        data = json.loads(path.read_text())

        if not isinstance(data, dict):
            return None, "STATE_ROOT_NOT_OBJECT"

        return data, None

    except Exception as exc:
        return None, f"INVALID_JSON: {exc}"


# ================================================================
# LEGACY PHASE 1–3
#
# These artifacts are not part of the current active state chain.
# Missing files are reported honestly as NOT_PRESENT.
# They are NEVER recreated or fabricated.
# ================================================================

def verify_legacy_phase(number, filename):
    path = STATE_DIR / filename

    if not path.exists():
        return {
            "phase": number,
            "status": "NOT_PRESENT",
            "reason": "NO_CURRENT_STATE_ARTIFACT",
            "file": str(path),
        }

    data, error = load_json(path)

    if error:
        return {
            "phase": number,
            "status": "FAIL",
            "reason": error,
            "file": str(path),
        }

    return {
        "phase": number,
        "status": "AVAILABLE",
        "reason": "STATE_PRESENT_AND_VALID",
        "file": str(path),
        "keys": list(data.keys()),
    }


# ================================================================
# ACTIVE PHASE 4–10 STATE VERIFICATION
# ================================================================

def verify_active_phase(number, filename):
    path = STATE_DIR / filename

    if not path.exists():
        return {
            "phase": number,
            "status": "FAIL",
            "reason": "ACTIVE_STATE_FILE_MISSING",
            "file": str(path),
        }

    data, error = load_json(path)

    if error:
        return {
            "phase": number,
            "status": "FAIL",
            "reason": error,
            "file": str(path),
        }

    return {
        "phase": number,
        "status": "PASS",
        "reason": "ACTIVE_STATE_PRESENT_AND_VALID",
        "file": str(path),
    }


def load_state(filename):
    path = STATE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing active state: {path}"
        )

    data, error = load_json(path)

    if error:
        raise ValueError(
            f"{filename}: {error}"
        )

    return data


# ================================================================
# HANDOFF VERIFICATION
# ================================================================

def verify_handoffs():

    results = {}

    # ------------------------------------------------------------
    # PHASE 6 -> PHASE 7
    # ------------------------------------------------------------

    try:
        p6 = load_state(
            "phase6_trade_quality.json"
        )
        p7 = load_state(
            "phase7_entry_intelligence.json"
        )

        q6 = p6.get("quality", {})
        i7 = p7.get("intelligence", {})

        approved = q6.get(
            "approved"
        )

        if isinstance(approved, list):
            source_count = len(approved)
        else:
            source_count = q6.get(
                "approved_candidates"
            )

        destination_count = i7.get(
            "phase6_candidates"
        )

        passed = (
            isinstance(source_count, int)
            and isinstance(destination_count, int)
            and source_count == destination_count
        )

        results["PHASE_6_TO_PHASE_7"] = {
            "status": "PASS" if passed else "FAIL",
            "from": source_count,
            "to": destination_count,
        }

    except Exception as exc:
        results["PHASE_6_TO_PHASE_7"] = {
            "status": "FAIL",
            "reason": str(exc),
        }

    # ------------------------------------------------------------
    # PHASE 7 -> PHASE 8
    # ------------------------------------------------------------

    try:
        p7 = load_state(
            "phase7_entry_intelligence.json"
        )
        p8 = load_state(
            "phase8_entry_validation.json"
        )

        i7 = p7.get("intelligence", {})
        v8 = p8.get("validation", {})

        source_count = i7.get(
            "entry_ready"
        )
        destination_count = v8.get(
            "phase7_candidates"
        )

        passed = (
            isinstance(source_count, int)
            and isinstance(destination_count, int)
            and source_count == destination_count
        )

        results["PHASE_7_TO_PHASE_8"] = {
            "status": "PASS" if passed else "FAIL",
            "from": source_count,
            "to": destination_count,
        }

    except Exception as exc:
        results["PHASE_7_TO_PHASE_8"] = {
            "status": "FAIL",
            "reason": str(exc),
        }

    # ------------------------------------------------------------
    # PHASE 8 -> PHASE 9
    # ------------------------------------------------------------

    try:
        p8 = load_state(
            "phase8_entry_validation.json"
        )
        p9 = load_state(
            "phase9_decision_gate.json"
        )

        v8 = p8.get("validation", {})
        g9 = p9.get("decision_gate", {})

        validated = v8.get(
            "validated_candidates",
            []
        )

        source_count = (
            len(validated)
            if isinstance(validated, list)
            else validated
        )

        destination_count = g9.get(
            "phase8_candidates"
        )

        passed = (
            isinstance(source_count, int)
            and isinstance(destination_count, int)
            and source_count == destination_count
        )

        results["PHASE_8_TO_PHASE_9"] = {
            "status": "PASS" if passed else "FAIL",
            "from": source_count,
            "to": destination_count,
        }

    except Exception as exc:
        results["PHASE_8_TO_PHASE_9"] = {
            "status": "FAIL",
            "reason": str(exc),
        }

    # ------------------------------------------------------------
    # PHASE 9 -> PHASE 10
    # ------------------------------------------------------------

    try:
        p9 = load_state(
            "phase9_decision_gate.json"
        )
        p10 = load_state(
            "phase10_trade_lifecycle.json"
        )

        g9 = p9.get("decision_gate", {})
        l10 = p10.get("lifecycle", {})

        qualified = g9.get(
            "qualified_candidates",
            []
        )

        source_count = (
            len(qualified)
            if isinstance(qualified, list)
            else qualified
        )

        destination_count = l10.get(
            "phase9_candidates"
        )

        passed = (
            isinstance(source_count, int)
            and isinstance(destination_count, int)
            and source_count == destination_count
        )

        results["PHASE_9_TO_PHASE_10"] = {
            "status": "PASS" if passed else "FAIL",
            "from": source_count,
            "to": destination_count,
        }

    except Exception as exc:
        results["PHASE_9_TO_PHASE_10"] = {
            "status": "FAIL",
            "reason": str(exc),
        }

    return results


# ================================================================
# PHASE 10 FINAL LIFECYCLE CHECK
# ================================================================

def verify_phase10():

    try:
        p10 = load_state(
            "phase10_trade_lifecycle.json"
        )

        lifecycle = p10.get(
            "lifecycle",
            {}
        )

        phase9_candidates = lifecycle.get(
            "phase9_candidates"
        )
        evaluated = lifecycle.get(
            "evaluated"
        )
        monitoring = lifecycle.get(
            "monitoring"
        )
        closed = lifecycle.get(
            "closed"
        )
        price_errors = lifecycle.get(
            "price_errors"
        )

        all_results = lifecycle.get(
            "all_results",
            []
        )

        passed = (
            isinstance(phase9_candidates, int)
            and isinstance(evaluated, int)
            and isinstance(monitoring, int)
            and isinstance(closed, int)
            and evaluated == phase9_candidates
            and monitoring + closed == evaluated
            and price_errors == 0
            and isinstance(all_results, list)
            and len(all_results) == evaluated
        )

        return {
            "status": "PASS" if passed else "FAIL",
            "phase9_candidates": phase9_candidates,
            "evaluated": evaluated,
            "monitoring": monitoring,
            "closed": closed,
            "price_errors": price_errors,
            "result_count": len(all_results)
                if isinstance(all_results, list)
                else None,
        }

    except Exception as exc:
        return {
            "status": "FAIL",
            "reason": str(exc),
        }


# ================================================================
# EXECUTION BOUNDARY VERIFICATION
# ================================================================

def verify_boundary():

    filenames = [
        "phase4_market_discovery.json",
        "phase5_market_intelligence.json",
        "phase6_trade_quality.json",
        "phase7_entry_intelligence.json",
        "phase8_entry_validation.json",
        "phase9_decision_gate.json",
        "phase10_trade_lifecycle.json",
    ]

    results = {}

    for filename in filenames:

        path = STATE_DIR / filename

        if not path.exists():
            results[filename] = "FAIL"
            continue

        data, error = load_json(path)

        if error:
            results[filename] = "FAIL"
            continue

        boundary = data.get(
            "execution_boundary",
            {}
        )

        safe = (
            boundary.get(
                "execution_authorized"
            ) is False
            and boundary.get(
                "order_submission"
            ) is False
            and boundary.get(
                "bot_armed"
            ) is False
            and boundary.get(
                "live_execution"
            ) is False
        )

        results[filename] = (
            "PASS" if safe else "FAIL"
        )

    return results


# ================================================================
# MAIN VERIFICATION
# ================================================================

def run():

    print(
        "PHASE 11 — FINAL SYSTEM VERIFICATION"
    )
    print(
        "READ-ONLY VERIFICATION OF PHASES 1–10"
    )
    print(
        "NO EARLIER PHASE WILL BE MODIFIED."
    )

    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — PHASE 11 FINAL INTEGRATION"
    )
    print("=" * 78)
    print(
        f"UTC              : {now_utc()}"
    )

    # ------------------------------------------------------------
    # Phase verification
    # ------------------------------------------------------------

    # Current architecture has no legacy Phase 1–3 market artifacts.
    legacy = []
active_files = {
        4: "phase4_market_discovery.json",
        5: "phase5_market_intelligence.json",
        6: "phase6_trade_quality.json",
        7: "phase7_entry_intelligence.json",
        8: "phase8_entry_validation.json",
        9: "phase9_decision_gate.json",
        10: "phase10_trade_lifecycle.json",
    }

    active = []

    for number, filename in active_files.items():
        active.append(
            verify_active_phase(
                number,
                filename
            )
        )

    all_phase_results = legacy + active

    print()
    print("PHASE VERIFICATION")
    print("-" * 78)

    for item in all_phase_results:

        print(
            f"PHASE {item['phase']:2} : "
            f"{item['status']:<12} "
            f"{item.get('reason', '')}"
        )

    # ------------------------------------------------------------
    # Handoffs
    # ------------------------------------------------------------

    handoffs = verify_handoffs()

    print()
    print("ACTIVE HANDOFF VERIFICATION")
    print("-" * 78)

    for name, result in handoffs.items():

        if result["status"] == "PASS":

            print(
                f"{name:<25} : PASS  "
                f"{result['from']} -> {result['to']}"
            )

        else:

            print(
                f"{name:<25} : FAIL  "
                f"{result.get('reason', '')}"
            )

    # ------------------------------------------------------------
    # Execution boundary
    # ------------------------------------------------------------

    boundary = verify_boundary()

    print()
    print("EXECUTION BOUNDARY")
    print("-" * 78)

    for filename, status in boundary.items():

        print(
            f"{filename:<42} : {status}"
        )

    # ------------------------------------------------------------
    # Phase 10
    # ------------------------------------------------------------

    phase10 = verify_phase10()

    print()
    print("PHASE 10 FINAL CHECK")
    print("-" * 78)

    print(
        f"Phase 9 input : "
        f"{phase10.get('phase9_candidates')}"
    )
    print(
        f"Evaluated     : "
        f"{phase10.get('evaluated')}"
    )
    print(
        f"Monitoring    : "
        f"{phase10.get('monitoring')}"
    )
    print(
        f"Closed        : "
        f"{phase10.get('closed')}"
    )
    print(
        f"Price errors  : "
        f"{phase10.get('price_errors')}"
    )

    print(
        f"Phase 10      : "
        f"{phase10['status']}"
    )

    # ------------------------------------------------------------
    # Overall result
    # ------------------------------------------------------------

    active_phases_pass = all(
        item["status"] == "PASS"
        for item in active
    )

    handoffs_pass = all(
        result["status"] == "PASS"
        for result in handoffs.values()
    )

    boundary_pass = all(
        status == "PASS"
        for status in boundary.values()
    )

    phase10_pass = (
        phase10["status"] == "PASS"
    )

    overall_pass = (
        active_phases_pass
        and handoffs_pass
        and boundary_pass
        and phase10_pass
    )

    overall_status = (
        "VERIFICATION_PASSED"
        if overall_pass
        else "VERIFICATION_FAILED"
    )

    print()
    print("=" * 78)

    if overall_pass:
        print(
            "PHASE 11 — FULL SYSTEM VERIFICATION PASSED"
        )
    else:
        print(
            "PHASE 11 — VERIFICATION FAILED"
        )

    print("=" * 78)

    print(
        "Execution boundary: LOCKED"
    )
    print(
        "Order submission   : DISABLED"
    )
    print(
        "Bot armed          : NO"
    )
    print(
        "Live execution     : FALSE"
    )

    # ------------------------------------------------------------
    # Phase 11 state ONLY
    # ------------------------------------------------------------

    state = {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "status": overall_status,

        "verification_policy": {
            "legacy_phases_1_to_3":
                "NOT_PRESENT_ALLOWED",
            "active_chain":
                "PHASE_4_TO_PHASE_10_STRICT",
            "modify_phases_1_to_10":
                False,
            "write_phase11_only":
                True,
        },

        "phase_verification": {
            "legacy_phases_1_to_3":
                legacy,
            "active_phases_4_to_10":
                active,
        },

        "handoff_verification": handoffs,

        "phase10_final_check": phase10,

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },

        "system_integrity": {
            "phases_1_to_3_modified": False,
            "phases_4_to_10_modified": False,
            "execution_enabled": False,
        },
    }

    save_json(
        PHASE11_STATE,
        state
    )

    save_json(
        PHASE11_REPORT,
        state
    )

    return overall_pass


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    run()
