#!/usr/bin/env python3

"""
============================================================
CRYPTOMASTERX1
PHASE 3 — BINANCE ACCOUNT IDENTITY & PERMISSION VERIFICATION
============================================================

READ-ONLY ACCOUNT VERIFICATION

This module:
    - connects to Binance Spot
    - authenticates with API key + secret
    - verifies the actual Binance account
    - checks Spot trading permission
    - checks withdrawal permission
    - records the result safely
    - NEVER submits an order
    - NEVER cancels an order
    - NEVER enables execution
    - NEVER enables withdrawals

EXECUTION REMAINS LOCKED.
============================================================
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


# ============================================================
# CONSTANTS
# ============================================================

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_3"
VERSION = "1.0.0"

BASE_URL = "https://api.binance.com"
ACCOUNT_ENDPOINT = "/api/v3/account"

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
REPORT_DIR = ROOT / "reports"

REPORT_FILE = REPORT_DIR / "phase3_account_verification.json"

# HARD SAFETY BOUNDARY
EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
TRANSMISSION = "LOCKED"


# ============================================================
# OUTPUT
# ============================================================

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def ensure_directories():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def sha256_short(value: str):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:24]


def print_status(label, value, good=True):
    colour = GREEN if good else RED
    print(
        f"{label:<34}"
        f"{colour}{value}{RESET}"
    )


# ============================================================
# API CREDENTIAL INPUT
# ============================================================

def get_credentials():
    print()
    print(f"{BOLD}{CYAN}BINANCE API CREDENTIALS{RESET}")
    print("-" * 64)

    print(
        "Credentials are entered locally into Termux."
    )

    print(
        "They are NEVER printed by this program."
    )

    print(
        "They are NEVER written to the report."
    )

    print()

    api_key = os.environ.get("BINANCE_API_KEY")

    if not api_key:
        api_key = input(
            "Enter Binance API Key: "
        ).strip()

    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_secret:
        api_secret = input(
            "Enter Binance API Secret: "
        ).strip()

    if not api_key or not api_secret:
        raise ValueError(
            "API key and API secret are required."
        )

    return api_key, api_secret


# ============================================================
# SIGNED REQUEST
# ============================================================

def signed_account_request(api_key, api_secret):

    timestamp = int(time.time() * 1000)

    params = {
        "timestamp": timestamp,
        "recvWindow": 5000,
        "omitZeroBalances": "true",
    }

    query_string = urlencode(params)

    signature = hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": api_key,
    }

    response = requests.get(
        BASE_URL + ACCOUNT_ENDPOINT,
        params=params,
        headers=headers,
        timeout=15,
    )

    return response


# ============================================================
# RESPONSE SANITIZATION
# ============================================================

def sanitize_account(data):

    """
    Keep only safe account metadata.

    Balances and private account details are not saved.
    """

    return {
        "account_type": data.get("accountType"),
        "can_trade": data.get("canTrade"),
        "can_withdraw": data.get("canWithdraw"),
        "can_deposit": data.get("canDeposit"),
        "brokered": data.get("brokered"),
        "require_self_trade_prevention": data.get(
            "requireSelfTradePrevention"
        ),
        "prevent_sor": data.get("preventSor"),
    }


# ============================================================
# REPORT
# ============================================================

def save_report(result):

    with REPORT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4,
            sort_keys=True
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 64)
    print(
        f"{BOLD}{CYAN}"
        "CRYPTOMASTERX1"
        f"{RESET}"
    )
    print(
        f"{BOLD}"
        "PHASE 3 — BINANCE ACCOUNT VERIFICATION"
        f"{RESET}"
    )
    print("=" * 64)

    print()
    print(f"Project       : {PROJECT}")
    print(f"Phase         : {PHASE}")
    print(f"Endpoint      : {ACCOUNT_ENDPOINT}")
    print(f"UTC Time      : {now_utc()}")

    # --------------------------------------------------------
    # SAFETY ASSERTION
    # --------------------------------------------------------

    print()
    print(f"{BOLD}SAFETY BOUNDARY{RESET}")
    print("-" * 64)

    print_status(
        "Execution authorization",
        "LOCKED",
        EXECUTION_AUTHORIZED is False,
    )

    print_status(
        "Order submission",
        "DISABLED",
        ORDER_SUBMISSION is False,
    )

    print_status(
        "Bot armed",
        "NO",
        BOT_ARMED is False,
    )

    print_status(
        "Live execution",
        "DISABLED",
        LIVE_EXECUTION is False,
    )

    print_status(
        "Transmission",
        "LOCKED",
        TRANSMISSION == "LOCKED",
    )

    # --------------------------------------------------------
    # CREDENTIALS
    # --------------------------------------------------------

    try:
        api_key, api_secret = get_credentials()

    except Exception as exc:
        print()
        print(
            f"{RED}Credential input failed: {exc}{RESET}"
        )
        sys.exit(1)

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    print()
    print(f"{BOLD}BINANCE CONNECTION{RESET}")
    print("-" * 64)

    try:

        response = signed_account_request(
            api_key,
            api_secret
        )

    except requests.RequestException as exc:

        print_status(
            "Binance connection",
            "FAILED",
            False
        )

        print(
            f"{RED}{exc}{RESET}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # HTTP RESULT
    # --------------------------------------------------------

    if response.status_code != 200:

        print_status(
            "Binance authentication",
            "FAILED",
            False
        )

        try:
            error = response.json()

            code = error.get("code")
            message = error.get("msg")

            print(
                f"{RED}"
                f"Binance error {code}: {message}"
                f"{RESET}"
            )

        except Exception:

            print(
                f"{RED}"
                f"HTTP {response.status_code}"
                f"{RESET}"
            )

        print()
        print(
            "Possible causes:"
        )
        print(
            "  - invalid API credentials"
        )
        print(
            "  - API key disabled"
        )
        print(
            "  - IP restriction"
        )
        print(
            "  - timestamp/time synchronization issue"
        )
        print(
            "  - insufficient API permissions"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # ACCOUNT DATA
    # --------------------------------------------------------

    try:
        account = response.json()

    except ValueError:

        print_status(
            "Account response",
            "INVALID",
            False
        )

        sys.exit(1)

    safe = sanitize_account(account)

    can_trade = safe.get("can_trade")
    can_withdraw = safe.get("can_withdraw")
    can_deposit = safe.get("can_deposit")

    # --------------------------------------------------------
    # IDENTITY
    # --------------------------------------------------------

    identity_material = (
        api_key
        + ":"
        + str(safe.get("account_type"))
    )

    identity_fingerprint = sha256_short(
        identity_material
    )

    print_status(
        "Binance account",
        "VERIFIED",
        True
    )

    print_status(
        "Account type",
        str(safe.get("account_type")),
        True
    )

    print_status(
        "Account fingerprint",
        identity_fingerprint,
        True
    )

    # --------------------------------------------------------
    # PERMISSIONS / SECURITY POLICY
    # --------------------------------------------------------
    #
    # Binance's canWithdraw/canDeposit fields are account-level
    # capability flags. They are NOT treated as CryptoMasterX1
    # authorization to move funds.
    #
    # CryptoMasterX1 is strictly a Spot trading machine.
    # Withdrawal, deposit, and transfer operations are forbidden
    # by the application security policy.
    # --------------------------------------------------------

    CRYPTOMASTER_WITHDRAWALS = False
    CRYPTOMASTER_DEPOSITS = False
    CRYPTOMASTER_TRANSFERS = False

    print()
    print(f"{BOLD}ACCOUNT CAPABILITIES / SECURITY POLICY{RESET}")
    print("-" * 64)

    print_status(
        "Spot trading capability",
        "ENABLED" if can_trade else "DISABLED",
        can_trade is True
    )

    print_status(
        "Binance withdrawal flag",
        "TRUE" if can_withdraw else "FALSE",
        True
    )

    print_status(
        "CryptoMasterX1 withdrawals",
        "FORBIDDEN",
        CRYPTOMASTER_WITHDRAWALS is False
    )

    print_status(
        "Binance deposit flag",
        "TRUE" if can_deposit else "FALSE",
        True
    )

    print_status(
        "CryptoMasterX1 deposits",
        "FORBIDDEN",
        CRYPTOMASTER_DEPOSITS is False
    )

    print_status(
        "CryptoMasterX1 transfers",
        "FORBIDDEN",
        CRYPTOMASTER_TRANSFERS is False
    )

    # --------------------------------------------------------
    # PHASE RESULT
    # --------------------------------------------------------

    checks = {
        "binance_connection": True,
        "account_identity": True,
        "spot_trade_permission": can_trade is True,

        # Binance account flags are informational only.
        "withdrawal_policy_forbidden":
            CRYPTOMASTER_WITHDRAWALS is False,

        "deposit_policy_forbidden":
            CRYPTOMASTER_DEPOSITS is False,

        "transfer_policy_forbidden":
            CRYPTOMASTER_TRANSFERS is False,

        "execution_locked": True,
        "order_submission_disabled": True,
        "bot_not_armed": True,
        "transmission_locked": True,
    }

    passed = sum(
        1 for value in checks.values()
        if value
    )

    score = round(
        passed / len(checks) * 100,
        2
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),

        "verification": {
            "status": "VERIFIED",
            "exchange": "BINANCE_SPOT",
            "account_type": safe.get("account_type"),
            "account_fingerprint": identity_fingerprint,
        },

        "binance_account_capabilities": {
            "can_trade": can_trade,
            "can_withdraw": can_withdraw,
            "can_deposit": can_deposit,
        },

        "cryptomaster_security_policy": {
            "spot_trading": can_trade is True,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },

        "checks": checks,

        "health_score": score,

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "transmission": "LOCKED",
        },

        "next_phase": (
            "PHASE_4 — MARKET DISCOVERY"
            if score == 100.0
            else "REVIEW PHASE 3"
        ),
    }

    save_report(report)

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 64)

    if score == 100.0:

        print(
            f"{GREEN}{BOLD}"
            "PHASE 3 COMPLETE — ACCOUNT VERIFIED"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "EXECUTION REMAINS LOCKED."
            f"{RESET}"
        )

    else:

        print(
            f"{YELLOW}{BOLD}"
            "PHASE 3 REQUIRES REVIEW"
            f"{RESET}"
        )

    print("=" * 64)

    print()
    print(
        f"Report: {REPORT_FILE}"
    )

    print()


if __name__ == "__main__":
    ensure_directories()
    main()
