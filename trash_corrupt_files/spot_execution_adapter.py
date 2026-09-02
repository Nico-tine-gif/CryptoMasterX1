#!/usr/bin/env python3
"""
CryptoMasterX1 — Binance Spot Execution Adapter

Single intended boundary for future Binance Spot order submission.

Safety:
- Execution locked
- Live execution disabled
- Order submission disabled
- Bot unarmed
- Withdrawals forbidden
- No Futures endpoints
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from decimal import Decimal
from urllib.parse import urlencode

import requests

BINANCE = "https://api.binance.com"
TIMEOUT = 15

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
WITHDRAWALS = False
EXECUTION_BOUNDARY = "LOCKED"


class SpotExecutionError(Exception):
    pass


def get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise SpotExecutionError(
            "BINANCE_API_KEY / BINANCE_API_SECRET not set"
        )

    return api_key, api_secret


def execution_enabled() -> bool:
    return (
        EXECUTION_AUTHORIZED
        and ORDER_SUBMISSION
        and BOT_ARMED
        and LIVE_EXECUTION
        and not WITHDRAWALS
        and EXECUTION_BOUNDARY == "UNLOCKED"
    )


def assert_execution_enabled() -> None:
    if not execution_enabled():
        raise SpotExecutionError(
            "ORDER BLOCKED: CMX1 execution boundary is not authorized"
        )


def signed_request(method: str, endpoint: str, params: dict) -> dict:
    api_key, api_secret = get_credentials()

    params = dict(params)
    params.setdefault("timestamp", int(time.time() * 1000))
    params.setdefault("recvWindow", 5000)

    query = urlencode(params)

    signature = hmac.new(
        api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    params["signature"] = signature

    response = requests.request(
        method,
        f"{BINANCE}{endpoint}",
        params=params,
        headers={"X-MBX-APIKEY": api_key},
        timeout=TIMEOUT,
    )

    if not response.ok:
        try:
            error = response.json()
            raise SpotExecutionError(
                f"Binance HTTP {response.status_code} | "
                f"code={error.get('code')} | "
                f"msg={error.get('msg')}"
            )
        except ValueError:
            raise SpotExecutionError(
                f"Binance HTTP {response.status_code} | "
                f"response={response.text[:300]}"
            )

    return response.json()


def get_account() -> dict:
    return signed_request("GET", "/api/v3/account", {})


def get_exchange_info(symbol: str) -> dict:
    response = requests.get(
        f"{BINANCE}/api/v3/exchangeInfo",
        params={"symbol": symbol},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def submit_order(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
) -> dict:

    assert_execution_enabled()

    if WITHDRAWALS:
        raise SpotExecutionError(
            "SAFETY FAILURE: withdrawals must remain disabled"
        )

    if side not in {"BUY", "SELL"}:
        raise SpotExecutionError(f"Invalid order side: {side}")

    if order_type not in {"MARKET", "LIMIT"}:
        raise SpotExecutionError(
            f"Unsupported Spot order type: {order_type}"
        )

    if Decimal(str(quantity)) <= 0:
        raise SpotExecutionError("Order quantity must be positive")

    return signed_request(
        "POST",
        "/api/v3/order",
        {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        },
    )


def main() -> int:
    print("=" * 72)
    print("CRYPTOMASTERX1 — SPOT EXECUTION ADAPTER")
    print("=" * 72)
    print(f"Execution boundary : {EXECUTION_BOUNDARY}")
    print(f"Execution authorized: {EXECUTION_AUTHORIZED}")
    print(f"Order submission   : {ORDER_SUBMISSION}")
    print(f"Bot armed          : {BOT_ARMED}")
    print(f"Live execution     : {LIVE_EXECUTION}")
    print(f"Withdrawals        : {WITHDRAWALS}")
    print()

    try:
        get_credentials()
        print("Binance credentials : PRESENT")
        print("Order transmission  : BLOCKED")
        print("Adapter status      : SAFE / NOT ACTIVE")
        return 0

    except Exception as exc:
        print(f"Adapter check       : FAILED — {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
