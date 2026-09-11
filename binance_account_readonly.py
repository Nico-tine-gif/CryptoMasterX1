#!/usr/bin/env python3

"""
CryptoMasterX1 — Read-Only Binance Account Interface

PURPOSE:
    Provide authenticated READ-ONLY account information to Phase 6.

ALLOWED:
    - Read account information
    - Read available USDT balance

FORBIDDEN:
    - Order creation
    - Order cancellation
    - Withdrawals
    - Deposits/transfers
    - Live execution
"""

import hashlib
import hmac
import os
import time
from decimal import Decimal
from urllib.parse import urlencode

import requests


BINANCE = "https://api.binance.com"
TIMEOUT = 15

# Hard safety boundary
LIVE_EXECUTION = False
BOT_ARMED = False
ORDER_SUBMISSION = False
WITHDRAWALS = False
EXECUTION_AUTHORIZED = False


class BinanceReadOnlyError(Exception):
    pass


def get_credentials():
    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise BinanceReadOnlyError(
            "BINANCE_API_KEY / BINANCE_API_SECRET not set"
        )

    return api_key, api_secret


def signed_account_request():
    api_key, api_secret = get_credentials()

    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000,
    }

    query = urlencode(params)

    signature = hmac.new(
        api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    params["signature"] = signature

    response = requests.get(
        f"{BINANCE}/api/v3/account",
        params=params,
        headers={
            "X-MBX-APIKEY": api_key,
        },
        timeout=TIMEOUT,
    )

    if not response.ok:
        try:
            error = response.json()
            raise BinanceReadOnlyError(
                f"Binance HTTP {response.status_code} | "
                f"code={error.get("code")} | "
                f"msg={error.get("msg")}"
            )
        except ValueError:
            raise BinanceReadOnlyError(
                f"Binance HTTP {response.status_code} | "
                f"response={response.text[:300]}"
            )

    return response.json()


def get_usdt_balance():
    account = signed_account_request()

    for balance in account.get("balances", []):
        if balance.get("asset") == "USDT":
            return Decimal(
                str(balance.get("free", "0"))
            )

    return Decimal("0")


def main():
    print("=" * 70)
    print("CMX1 — READ-ONLY BINANCE ACCOUNT TEST")
    print("=" * 70)

    print("Execution authorized :", EXECUTION_AUTHORIZED)
    print("Live execution       :", LIVE_EXECUTION)
    print("Order submission     :", ORDER_SUBMISSION)
    print("Withdrawals          :", WITHDRAWALS)
    print()

    try:
        balance = get_usdt_balance()

        print("BINANCE AUTHENTICATION: PASS")
        print(f"AVAILABLE USDT: {balance}")
        print()
        print("READ-ONLY ACCOUNT ACCESS: PASS")

    except Exception as exc:
        print("READ-ONLY ACCOUNT ACCESS: FAILED")
        print(f"Reason: {exc}")

        raise SystemExit(1)


if __name__ == "__main__":
    main()
