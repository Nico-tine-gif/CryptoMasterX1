#!/usr/bin/env python3

"""
CryptoMasterX1
PHASE 5 — TRADE INTELLIGENCE + DETECTORS

OWNER:
    Market intelligence only.

PHASE 5 MUST NOT:
    - construct Entry
    - construct SL
    - construct TP1/TP2
    - calculate position size
    - submit orders

It consumes the Phase 4 discovered universe and refreshes
Binance market data before intelligence analysis.
"""

import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
REPORTS = ROOT / "reports"

PHASE4_STATE = STATE / "phase4_market_discovery.json"
PHASE5_STATE = STATE / "phase5_market_intelligence.json"

BINANCE = "https://api.binance.com"

MIN_CONFIDENCE = 75.0
RSI_OVERBOUGHT = 75.0
RSI_OVERSOLD = 25.0
MAX_5M_EXTENSION_ATR = 2.0

TIMEOUT = 15


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def get_json(path, params=None):
    r = requests.get(path, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def fetch_klines(symbol, interval, limit=120):
    return get_json(
        f"{BINANCE}/api/v3/klines",
        {"symbol": symbol, "interval": interval, "limit": limit},
    )


def closes(c):
    return [float(x[4]) for x in c]


def highs(c):
    return [float(x[2]) for x in c]


def lows(c):
    return [float(x[3]) for x in c]


def ema(values, period):
    if len(values) < period:
        return None

    value = sum(values[:period]) / period
    multiplier = 2 / (period + 1)

    for price in values[period:]:
        value = ((price - value) * multiplier) + value

    return value


def rsi(values, period=14):
    if len(values) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(candles, period=14):
    if len(candles) <= period:
        return None

    trs = []

    for i in range(1, len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        previous_close = float(candles[i - 1][4])

        trs.append(
            max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
        )

    return sum(trs[-period:]) / period


def trend_score(values):
    if len(values) < 50:
        return 0.0

    e9 = ema(values, 9)
    e20 = ema(values, 20)
    e50 = ema(values, 50)

    if not all(x is not None for x in (e9, e20, e50)):
        return 0.0

    score = 0

    if e9 > e20:
        score += 1
    else:
        score -= 1

    if e20 > e50:
        score += 1
    else:
        score -= 1

    if values[-1] > e20:
        score += 1
    else:
        score -= 1

    return score / 3.0


def momentum_score(values):
    if len(values) < 20:
        return 0.0

    recent = values[-1]
    previous = values[-6]

    if previous == 0:
        return 0.0

    pct = ((recent - previous) / previous) * 100

    return max(-1.0, min(1.0, pct / 5.0))


def analyze_symbol(symbol):
    """
    Detector output only.

    No Entry/SL/TP/position sizing is created here.
    """

    h1 = fetch_klines(symbol, "1h", 120)
    m15 = fetch_klines(symbol, "15m", 120)
    m5 = fetch_klines(symbol, "5m", 120)

    h1c = closes(h1)
    m15c = closes(m15)
    m5c = closes(m5)

    current_price = m5c[-1]

    h1_trend = trend_score(h1c)
    m15_trend = trend_score(m15c)
    m5_trend = trend_score(m5c)

    momentum = (
        momentum_score(h1c)
        + momentum_score(m15c)
        + momentum_score(m5c)
    ) / 3

    rsi5 = rsi(m5c)
    atr5 = atr(m5)

    if atr5 is None or atr5 <= 0:
        return None

    direction_score = (
        h1_trend * 0.40
        + m15_trend * 0.35
        + m5_trend * 0.25
    )

    if direction_score > 0.15:
        direction = "LONG"
    elif direction_score < -0.15:
        direction = "SHORT"
    else:
        direction = "NEUTRAL"

    confidence = 50.0 + abs(direction_score) * 35.0
    confidence += abs(momentum) * 15.0

    if rsi5 is not None:
        if direction == "LONG" and rsi5 >= RSI_OVERBOUGHT:
            confidence -= 10
        if direction == "SHORT" and rsi5 <= RSI_OVERSOLD:
            confidence -= 10

    confidence = max(0.0, min(100.0, confidence))

    extension = abs(m5c[-1] - m5c[-6])

    anti_chase = extension <= (atr5 * MAX_5M_EXTENSION_ATR)

    qualified = (
        direction in ("LONG", "SHORT")
        and confidence >= MIN_CONFIDENCE
        and anti_chase
    )

    return {
        "symbol": symbol,
        "timestamp_utc": now_utc(),
        "data_source": "BINANCE_SPOT_REST",
        "data_fresh": True,

        "direction": direction,

        "h1_trend": round(h1_trend, 4),
        "m15_trend": round(m15_trend, 4),
        "m5_trend": round(m5_trend, 4),

        "momentum": round(momentum, 4),
        "rsi_5m": round(rsi5, 4) if rsi5 is not None else None,
        "atr_5m": round(atr5, 12),

        "current_price": current_price,

        "extension": extension,
        "anti_chase": anti_chase,

        "confidence": round(confidence, 2),
        "qualified": qualified,

        "phase5_owner": "TRADE_INTELLIGENCE_DETECTORS",

        # Explicitly forbidden in Phase 5:
        "entry": None,
        "sl": None,
        "tp1": None,
        "tp2": None,
        "risk": None,
        "reward": None,
        "rr": None,
        "position_size": None,
    }


def get_phase4_symbols():
    data = load_json(PHASE4_STATE)

    symbols = []

    discovery = data.get("discovery", {})
    markets = discovery.get("markets", [])

    for item in markets:
        if isinstance(item, dict):
            symbol = item.get("symbol")
            if symbol and symbol not in symbols:
                symbols.append(symbol)

    for key in ("safe_bulls", "safe_bears"):
        for item in data.get(key, []):
            if isinstance(item, dict):
                symbol = item.get("symbol")
                if symbol and symbol not in symbols:
                    if symbol not in symbols:
                        symbols.append(symbol)

    return symbols


def main():
    STATE.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)

    symbols = get_phase4_symbols()

    results = []
    qualified = []

    for symbol in symbols:
        try:
            result = analyze_symbol(symbol)

            if result is None:
                continue

            results.append(result)

            if result["qualified"]:
                qualified.append(result)

        except Exception as exc:
            print(f"INTELLIGENCE ERROR {symbol}: {exc}", flush=True)

    output = {
        "phase": 5,
        "phase_name": "TRADE INTELLIGENCE + DETECTORS",
        "timestamp_utc": now_utc(),
        "source_phase": 4,
        "symbols_received": len(symbols),
        "symbols_analyzed": len(results),
        "qualified_candidates": len(qualified),
        "results": results,
        "qualified": qualified,

        "ownership": {
            "market_discovery": "PHASE_4",
            "intelligence_detectors": "PHASE_5",
            "trade_construction": "PHASE_6",
            "execution": "PHASE_7",
            "lifecycle": "PHASE_8",
        },

        "forbidden_in_phase5": [
            "entry",
            "sl",
            "tp1",
            "tp2",
            "risk",
            "reward",
            "rr",
            "position_size",
            "order_submission",
        ],
    }

    save_json(PHASE5_STATE, output)

    print()
    print("PHASE 5 — TRADE INTELLIGENCE + DETECTORS")
    print(f"Phase 4 symbols received : {len(symbols)}")
    print(f"Symbols analyzed         : {len(results)}")
    print(f"Qualified setups         : {len(qualified)}")
    print(f"State saved              : {PHASE5_STATE}")


if __name__ == "__main__":
    main()
