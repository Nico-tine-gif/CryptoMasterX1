#!/usr/bin/env python3

"""
============================================================
CRYPTOMASTERX1
PHASE 1 — MACHINE CORE / PERFORMANCE SCANNER
============================================================

Purpose:
    Establish the first foundation of CryptoMasterX1.

This phase:
    - identifies the machine
    - creates the required directory structure
    - maintains machine state
    - records heartbeat
    - checks core files
    - checks Python environment
    - checks execution lock state
    - checks telemetry
    - produces a machine health report

SAFETY:
    This phase NEVER:
        - connects to Binance trading endpoints
        - submits orders
        - cancels orders
        - changes execution authorization
        - unlocks the machine
        - trades
        - uses real money

Execution starts LOCKED.
============================================================
"""

from __future__ import annotations

import json
import platform
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# MACHINE CONSTANTS
# ============================================================

PROJECT_NAME = "CryptoMasterX1"
VERSION = "1.0.0"
PHASE = "PHASE_1"

EXECUTION_LOCKED = True
LIVE_EXECUTION = False
ORDER_SUBMISSION_ENABLED = False


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
STATE_DIR = ROOT / "state"
REPORT_DIR = ROOT / "reports"

STATE_FILE = STATE_DIR / "machine_state.json"
HEARTBEAT_FILE = STATE_DIR / "heartbeat.json"
REPORT_FILE = REPORT_DIR / "phase1_report.json"


# ============================================================
# COLORS
# ============================================================

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"


# ============================================================
# HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def mkdirs():
    for directory in (
        DATA_DIR,
        LOG_DIR,
        STATE_DIR,
        REPORT_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            sort_keys=True,
        )


def load_json(path: Path):
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def banner():
    print()
    print("=" * 64)
    print(f"{BOLD}{CYAN}CRYPTOMASTERX1{RESET}")
    print(f"{BOLD}{WHITE}PHASE 1 — MACHINE CORE / PERFORMANCE SCANNER{RESET}")
    print("=" * 64)
    print()


def status(label, value, ok=True):
    colour = GREEN if ok else RED

    print(
        f"{label:<32} "
        f"{colour}{value}{RESET}"
    )


# ============================================================
# MACHINE STATE
# ============================================================

def build_machine_state():

    state = {
        "machine": PROJECT_NAME,
        "version": VERSION,
        "phase": PHASE,

        "created_utc": utc_now(),

        "execution": {
            "locked": EXECUTION_LOCKED,
            "live_execution": LIVE_EXECUTION,
            "order_submission_enabled": ORDER_SUBMISSION_ENABLED,
        },

        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
        },

        "architecture": {
            "market_discovery": False,
            "safety_filter": False,
            "quality_momentum": False,
            "regime_1h": False,
            "structure_15m": False,
            "entry_5m": False,
            "exhaustion": False,
            "rsi_protection": False,
            "atr_extension": False,
            "pullback": False,
            "reclaim": False,
            "liquidity": False,
            "entry_quality": False,
            "confidence": False,
            "adaptive_sl_tp": False,
            "duplicate_protection": False,
            "execution": False,
            "telemetry": True,
        },

        "phase_status": "INITIALIZED",
    }

    save_json(STATE_FILE, state)

    return state


# ============================================================
# HEARTBEAT
# ============================================================

def write_heartbeat():

    heartbeat = {
        "machine": PROJECT_NAME,
        "phase": PHASE,
        "heartbeat_utc": utc_now(),
        "process_id": os.getpid(),
        "status": "ALIVE",
    }

    save_json(HEARTBEAT_FILE, heartbeat)

    return heartbeat


# ============================================================
# CORE CHECKS
# ============================================================

def check_project():

    return ROOT.exists()


def check_directories():

    required = [
        DATA_DIR,
        LOG_DIR,
        STATE_DIR,
        REPORT_DIR,
    ]

    return all(directory.exists() for directory in required)


def check_python():

    return sys.version_info >= (3, 10)


def check_execution_lock(state):

    execution = state.get("execution", {})

    locked = execution.get("locked") is True
    live = execution.get("live_execution") is False
    orders = execution.get("order_submission_enabled") is False

    return locked and live and orders


def check_telemetry(state):

    architecture = state.get("architecture", {})

    return architecture.get("telemetry") is True


# ============================================================
# PERFORMANCE METRICS
# ============================================================

def calculate_health(checks):

    total = len(checks)

    passed = sum(
        1 for value in checks.values()
        if value
    )

    if total == 0:
        return 0

    return round(
        (passed / total) * 100,
        2,
    )


# ============================================================
# REPORT
# ============================================================

def build_report(state, checks, health):

    report = {
        "machine": PROJECT_NAME,
        "version": VERSION,
        "phase": PHASE,

        "timestamp_utc": utc_now(),

        "health_score": health,

        "checks": checks,

        "execution": state["execution"],

        "runtime": state["runtime"],

        "architecture": state["architecture"],

        "next_phase": (
            "PHASE_2 — MARKET DISCOVERY"
            if health >= 90
            else "REPAIR PHASE 1 BEFORE CONTINUING"
        ),
    }

    save_json(REPORT_FILE, report)

    return report


# ============================================================
# SCANNER
# ============================================================

def run_scanner():

    banner()

    print(f"{BOLD}SYSTEM INFORMATION{RESET}")
    print("-" * 64)

    print(f"Project       : {PROJECT_NAME}")
    print(f"Version       : {VERSION}")
    print(f"Phase         : {PHASE}")
    print(f"Root          : {ROOT}")
    print(f"Python        : {platform.python_version()}")
    print(f"Platform      : {platform.platform()}")
    print(f"UTC Time      : {utc_now()}")
    print()

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    state = load_json(STATE_FILE)

    if state is None:
        state = build_machine_state()

    heartbeat = write_heartbeat()

    # --------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------

    checks = {}

    checks["project_root"] = check_project()
    checks["required_directories"] = check_directories()
    checks["python_runtime"] = check_python()
    checks["execution_lock"] = check_execution_lock(state)
    checks["telemetry"] = check_telemetry(state)
    checks["state_file"] = STATE_FILE.exists()
    checks["heartbeat"] = HEARTBEAT_FILE.exists()

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(f"{BOLD}CORE HEALTH CHECKS{RESET}")
    print("-" * 64)

    status(
        "Project root",
        "PASS" if checks["project_root"] else "FAIL",
        checks["project_root"],
    )

    status(
        "Required directories",
        "PASS" if checks["required_directories"] else "FAIL",
        checks["required_directories"],
    )

    status(
        "Python runtime",
        "PASS" if checks["python_runtime"] else "FAIL",
        checks["python_runtime"],
    )

    status(
        "Execution LOCK",
        "LOCKED" if checks["execution_lock"] else "UNSAFE",
        checks["execution_lock"],
    )

    status(
        "Telemetry",
        "ACTIVE" if checks["telemetry"] else "MISSING",
        checks["telemetry"],
    )

    status(
        "State file",
        "PASS" if checks["state_file"] else "FAIL",
        checks["state_file"],
    )

    status(
        "Heartbeat",
        "ALIVE" if checks["heartbeat"] else "FAIL",
        checks["heartbeat"],
    )

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    health = calculate_health(checks)

    print()
    print(f"{BOLD}MACHINE HEALTH{RESET}")
    print("-" * 64)

    if health >= 90:
        colour = GREEN
        state_text = "HEALTHY"

    elif health >= 70:
        colour = YELLOW
        state_text = "DEGRADED"

    else:
        colour = RED
        state_text = "CRITICAL"

    print(
        f"HEALTH SCORE : "
        f"{colour}{health:.2f}%{RESET}"
    )

    print(
        f"STATUS       : "
        f"{colour}{state_text}{RESET}"
    )

    # --------------------------------------------------------
    # EXECUTION BOUNDARY
    # --------------------------------------------------------

    print()
    print(f"{BOLD}EXECUTION BOUNDARY{RESET}")
    print("-" * 64)

    print(
        f"EXECUTION LOCK       : "
        f"{GREEN}LOCKED{RESET}"
    )

    print(
        f"LIVE EXECUTION       : "
        f"{GREEN}DISABLED{RESET}"
    )

    print(
        f"ORDER SUBMISSION     : "
        f"{GREEN}DISABLED{RESET}"
    )

    # --------------------------------------------------------
    # ARCHITECTURE
    # --------------------------------------------------------

    print()
    print(f"{BOLD}ARCHITECTURE STATUS{RESET}")
    print("-" * 64)

    for name, enabled in state["architecture"].items():

        readable = name.replace("_", " ").upper()

        if enabled:
            print(
                f"{readable:<28}"
                f"{GREEN}READY{RESET}"
            )
        else:
            print(
                f"{readable:<28}"
                f"{YELLOW}NOT BUILT{RESET}"
            )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = build_report(
        state,
        checks,
        health,
    )

    print()
    print(f"{BOLD}PHASE 1 REPORT{RESET}")
    print("-" * 64)

    print(f"Report file : {REPORT_FILE}")
    print(f"Heartbeat   : {HEARTBEAT_FILE}")
    print(f"State file  : {STATE_FILE}")

    print()
    print("=" * 64)

    if health >= 90:
        print(
            f"{GREEN}{BOLD}"
            "PHASE 1 COMPLETE — FOUNDATION HEALTHY"
            f"{RESET}"
        )
    else:
        print(
            f"{YELLOW}{BOLD}"
            "PHASE 1 COMPLETE — REVIEW FINDINGS"
            f"{RESET}"
        )

    print("=" * 64)
    print()


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    mkdirs()
    run_scanner()
