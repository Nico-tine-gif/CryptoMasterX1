#!/usr/bin/env python3

"""
CryptoMasterX1
PHASE 6 — TRADE VERIFICATION + FINAL CONSTRUCTION

Phase 6 owns:
    Entry
    SL
    TP1
    TP2
    risk
    reward
    R:R
    position size

Phase 6 refreshes Binance price data before construction.

NO order submission.
"""

import json
import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"

PHASE5_STATE = STATE / "phase5_market_intelligence.json"
PHASE6_STATE = STATE / "phase6_trade_intelligence.json"

BINANCE = "https://api.binance.com"

SL_ATR_MULTIPLIER = Decimal("1.20")
TP1_R_MULTIPLIER = Decimal("1.50")
TP2_R_MULTIPLIER = Decimal("2.50")

RISK_PER_TRADE = Decimal("0.005")
MIN_RR = Decimal("1.50")

TIMEOUT = 15


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def get_json(path, params=None):
    r = requests.get(path, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def load_json(path):
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def current_price(symbol):
    data = get_json(
        f"{BINANCE}/api/v3/ticker/price",
        {"symbol": symbol},
    )
    return Decimal(str(data["price"]))


def build_trade(candidate):
    symbol = candidate["symbol"]
    direction = candidate["direction"]

    live_price = current_price(symbol)

    atr_value = Decimal(str(candidate["atr_5m"]))

    if atr_value <= 0:
        return None

    risk_distance = atr_value * SL_ATR_MULTIPLIER

    if direction == "LONG":
        entry = live_price
        sl = entry - risk_distance
        tp1 = entry + (risk_distance * TP1_R_MULTIPLIER)
        tp2 = entry + (risk_distance * TP2_R_MULTIPLIER)

    elif direction == "SHORT":
        entry = live_price
        sl = entry + risk_distance
        tp1 = entry - (risk_distance * TP1_R_MULTIPLIER)
        tp2 = entry - (risk_distance * TP2_R_MULTIPLIER)

    else:
        return None

    risk = abs(entry - sl)
    reward = abs(tp2 - entry)

    if risk <= 0:
        return None

    rr = reward / risk

    if rr < MIN_RR:
        return None

    # Position sizing is deliberately represented as a construction
    # output. Account-specific sizing is verified against the live
    # account/exchange state before execution.
    position_size_required = True

    return {
        "symbol": symbol,
        "direction": direction,
        "constructed_at_utc": now_utc(),

        "market_data_source": "BINANCE_SPOT_REST",
        "price_refreshed_before_construction": True,

        "entry": float(entry),
        "sl": float(sl),
        "tp1": float(tp1),
        "tp2": float(tp2),

        "risk": float(risk),
        "reward": float(reward),
        "rr": float(rr),

        "risk_per_trade": float(RISK_PER_TRADE),
        "position_size_required": position_size_required,

        "phase5_confidence": candidate.get("confidence"),
        "phase6_owner": "TRADE_VERIFICATION_FINAL_CONSTRUCTION",

        "execution_authorized": False,
        "order_submission": False,
    }


def main():
    STATE.mkdir(exist_ok=True)

    source = load_json(PHASE5_STATE)
    candidates = source.get("qualified", [])

    constructed = []

    for candidate in candidates:
        try:
            trade = build_trade(candidate)

            if trade is not None:
                constructed.append(trade)

        except Exception as exc:
            print(
                f"CONSTRUCTION ERROR {candidate.get('symbol')}: {exc}",
                flush=True,
            )

    output = {
        "phase": 6,
        "phase_name": "TRADE VERIFICATION + FINAL CONSTRUCTION",
        "timestamp_utc": now_utc(),

        "phase5_candidates": len(candidates),
        "constructed_trades": len(constructed),

        "trades": constructed,

        "ownership": {
            "trade_intelligence": "PHASE_5",
            "final_construction": "PHASE_6",
            "execution": "PHASE_7",
            "lifecycle": "PHASE_8",
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "live_execution": False,
        },
    }

    save_json(PHASE6_STATE, output)

    print()
    print("PHASE 6 — TRADE VERIFICATION + FINAL CONSTRUCTION")
    print(f"Phase 5 candidates : {len(candidates)}")
    print(f"Constructed trades : {len(constructed)}")
    print(f"State saved        : {PHASE6_STATE}")
    print("ORDER SUBMISSION   : LOCKED")


if __name__ == "__main__":
    main()
