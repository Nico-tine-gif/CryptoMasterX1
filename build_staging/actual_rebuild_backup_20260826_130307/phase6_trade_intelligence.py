#!/usr/bin/env python3

import json
import time
import hmac
import hashlib
import urllib.parse
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_6"
VERSION = "6.0-CONSOLIDATED"

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
REPORTS = ROOT / "reports"

PHASE5_STATE = STATE / "phase5_market_intelligence.json"
PHASE6_STATE = STATE / "phase6_trade_intelligence.json"
PHASE6_REPORT = REPORTS / "phase6_trade_intelligence_report.json"

BINANCE = "https://api.binance.com"

ATR_PERIOD = 14
EMA_FAST = 9
EMA_SLOW = 20

MIN_CONFIDENCE = 75.0
MIN_RR = 1.50

SL_ATR_MULTIPLIER = 1.20
TP1_R_MULTIPLIER = 1.50
TP2_R_MULTIPLIER = 2.50

MAX_ENTRY_EXTENSION_ATR = 1.50
MAX_REFERENCE_DRIFT_ATR = 2.50

RISK_PER_TRADE = Decimal("0.005")

# ------------------------------------------------------------
# GLOBAL EXECUTION SAFETY
# ------------------------------------------------------------

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
TRANSMISSION_LOCKED = True

WITHDRAWALS = False
DEPOSITS = False
TRANSFERS = False


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def load(path):
    if not path.exists():
        raise FileNotFoundError(f"Required state missing: {path}")
    return json.loads(path.read_text())


def number(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------
# BINANCE PUBLIC DATA
# ------------------------------------------------------------

def binance_get(path, params=None):
    params = dict(params or {})
    query = urllib.parse.urlencode(params)

    url = BINANCE + path
    if query:
        url += "?" + query

    req = Request(
        url,
        headers={"User-Agent": "CryptoMasterX1-Consolidated/6.0"},
        method="GET",
    )

    try:
        with urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Binance HTTP {exc.code}: {body}")
    except URLError as exc:
        raise RuntimeError(f"Binance network error: {exc}")


def candles(symbol, interval="5m", limit=120):
    data = binance_get(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        },
    )

    result = []

    for row in data:
        result.append({
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "open_time": int(row[0]),
            "close_time": int(row[6]),
        })

    return result


# ------------------------------------------------------------
# INDICATORS
# ------------------------------------------------------------

def ema(values, period):
    if len(values) < period:
        return None

    value = sum(values[:period]) / period
    multiplier = 2 / (period + 1)

    for price in values[period:]:
        value = ((price - value) * multiplier) + value

    return value


def atr(rows, period=14):
    if len(rows) <= period:
        return None

    trs = []

    for i in range(1, len(rows)):
        current = rows[i]
        previous = rows[i - 1]

        tr = max(
            current["high"] - current["low"],
            abs(current["high"] - previous["close"]),
            abs(current["low"] - previous["close"]),
        )

        trs.append(tr)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


# ------------------------------------------------------------
# COMPLETE PHASE 5 DIGEST
# ------------------------------------------------------------

def extract_candidates(obj):
    """
    Recursively collect candidate dictionaries from Phase 5.

    This deliberately does not assume only one Phase 5 list name.
    It digests all candidate containers while preserving the
    original Phase 5 intelligence.
    """

    found = []

    def walk(value):
        if isinstance(value, dict):
            looks_like_candidate = (
                value.get("symbol")
                and (
                    value.get("direction")
                    or value.get("confidence") is not None
                    or value.get("quality_score") is not None
                    or value.get("h1_trend")
                    or value.get("m15_trend")
                    or value.get("m5_trend")
                )
            )

            if looks_like_candidate:
                found.append(value)

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)

    unique = {}
    for item in found:
        symbol = str(item.get("symbol", "")).upper()

        if symbol:
            # Preserve the richest version if duplicates exist.
            old = unique.get(symbol)

            if old is None or len(item) > len(old):
                unique[symbol] = item

    return list(unique.values())


def digest_phase5():
    state = load(PHASE5_STATE)

    candidates = extract_candidates(state)

    if not candidates:
        raise RuntimeError(
            "Phase 5 contains no digestible market-intelligence candidates."
        )

    return state, candidates


# ------------------------------------------------------------
# FRESH MARKET ANALYSIS
# ------------------------------------------------------------

def fresh_market(symbol):
    rows = candles(symbol, "5m", 120)

    if len(rows) < EMA_SLOW + ATR_PERIOD + 2:
        raise RuntimeError(f"{symbol}: insufficient fresh candles")

    # Use the latest completed candle for structural indicators.
    closed = rows[:-1]

    closes = [x["close"] for x in closed]

    fast = ema(closes, EMA_FAST)
    slow = ema(closes, EMA_SLOW)
    fresh_atr = atr(closed, ATR_PERIOD)

    if fast is None or slow is None or fresh_atr is None:
        raise RuntimeError(f"{symbol}: fresh indicator calculation failed")

    current_price = rows[-1]["close"]

    if current_price > fast > slow:
        direction = "LONG"
    elif current_price < fast < slow:
        direction = "SHORT"
    else:
        direction = "NEUTRAL"

    extension = abs(current_price - fast) / fresh_atr

    return {
        "symbol": symbol,
        "price": current_price,
        "ema_fast": fast,
        "ema_slow": slow,
        "atr": fresh_atr,
        "fresh_direction": direction,
        "extension_atr": extension,
        "latest_candle_close_time": rows[-1]["close_time"],
        "fresh_checked_utc": now(),
    }


# ------------------------------------------------------------
# BINANCE SPOT FILTERS
# ------------------------------------------------------------

def exchange_info(symbol):
    data = binance_get(
        "/api/v3/exchangeInfo",
        {"symbol": symbol},
    )

    symbols = data.get("symbols", [])

    if not symbols:
        raise RuntimeError(f"{symbol}: Binance symbol not found")

    info = symbols[0]

    if info.get("status") != "TRADING":
        raise RuntimeError(f"{symbol}: not currently TRADING")

    filters = {
        x.get("filterType"): x
        for x in info.get("filters", [])
    }

    lot = filters.get("LOT_SIZE")
    notional = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")

    if not lot:
        raise RuntimeError(f"{symbol}: LOT_SIZE unavailable")

    return {
        "min_qty": Decimal(lot.get("minQty", "0")),
        "max_qty": Decimal(lot.get("maxQty", "0")),
        "step_size": Decimal(lot.get("stepSize", "0")),
        "min_notional": Decimal(
            (notional or {}).get("minNotional", "0")
        ),
        "base_asset": info.get("baseAsset"),
        "quote_asset": info.get("quoteAsset"),
    }


def floor_step(value, step):
    if step <= 0:
        raise ValueError("Invalid Binance step size")

    units = (value / step).to_integral_value(
        rounding=ROUND_DOWN
    )

    return units * step


# ------------------------------------------------------------
# ACCOUNT BALANCE — READ ONLY
# ------------------------------------------------------------

def load_credentials():
    env = ROOT / ".env"

    values = {}

    if env.exists():
        for raw in env.read_text().splitlines():
            line = raw.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            values[key.strip()] = (
                value.strip().strip('"').strip("'")
            )

    import os

    key = os.environ.get("BINANCE_API_KEY") or values.get(
        "BINANCE_API_KEY"
    )

    secret = os.environ.get("BINANCE_API_SECRET") or values.get(
        "BINANCE_API_SECRET"
    )

    if not key or not secret:
        raise RuntimeError("Binance credentials unavailable")

    return key, secret


def signed_account():
    key, secret = load_credentials()

    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000,
    }

    query = urllib.parse.urlencode(params)

    signature = hmac.new(
        secret.encode(),
        query.encode(),
        hashlib.sha256,
    ).hexdigest()

    url = (
        BINANCE
        + "/api/v3/account?"
        + query
        + "&signature="
        + signature
    )

    req = Request(
        url,
        headers={
            "X-MBX-APIKEY": key,
            "User-Agent": "CryptoMasterX1-Consolidated-Sizing/6.0",
        },
        method="GET",
    )

    try:
        with urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Binance account HTTP {exc.code}: {body}")


def quote_balance(asset):
    account = signed_account()

    for balance in account.get("balances", []):
        if balance.get("asset") == asset:
            return Decimal(balance.get("free", "0"))

    return Decimal("0")


# ------------------------------------------------------------
# POSITION SIZING
# ------------------------------------------------------------

def calculate_position_size(symbol, entry, sl):
    filters = exchange_info(symbol)

    quote = filters["quote_asset"]

    available = quote_balance(quote)

    if available <= 0:
        raise RuntimeError(
            f"{symbol}: no available {quote} balance"
        )

    risk_distance = Decimal(str(abs(entry - sl)))

    if risk_distance <= 0:
        raise RuntimeError(f"{symbol}: invalid stop distance")

    risk_capital = available * RISK_PER_TRADE

    raw_qty = risk_capital / risk_distance

    # Never exceed what the available quote balance can buy.
    balance_qty = available / Decimal(str(entry))

    raw_qty = min(raw_qty, balance_qty)

    qty = floor_step(
        raw_qty,
        filters["step_size"],
    )

    if qty < filters["min_qty"]:
        raise RuntimeError(
            f"{symbol}: calculated quantity below Binance minimum"
        )

    notional = qty * Decimal(str(entry))

    if notional < filters["min_notional"]:
        raise RuntimeError(
            f"{symbol}: calculated notional below Binance minimum"
        )

    if filters["max_qty"] > 0 and qty > filters["max_qty"]:
        qty = filters["max_qty"]

    return {
        "quantity": float(qty),
        "quantity_decimal": format(qty, "f"),
        "quote_asset": quote,
        "available_quote_balance": format(available, "f"),
        "risk_capital": format(risk_capital, "f"),
        "risk_per_trade": float(RISK_PER_TRADE),
        "notional": format(notional, "f"),
        "step_size": format(filters["step_size"], "f"),
        "min_qty": format(filters["min_qty"], "f"),
        "min_notional": format(filters["min_notional"], "f"),
    }


# ------------------------------------------------------------
# CONSTRUCTION
# ------------------------------------------------------------

def construct(candidate, market):
    symbol = str(candidate["symbol"]).upper()

    direction = str(
        candidate.get("direction")
        or candidate.get("fresh_direction")
        or ""
    ).upper()

    confidence = number(
        candidate.get("confidence"),
        number(candidate.get("phase6_confidence"), 0),
    )

    if direction not in ("LONG", "SHORT"):
        raise RuntimeError(
            f"{symbol}: invalid Phase 5 direction"
        )

    if confidence is None or confidence < MIN_CONFIDENCE:
        raise RuntimeError(
            f"{symbol}: confidence below {MIN_CONFIDENCE}"
        )

    fresh_direction = market["fresh_direction"]

    if fresh_direction == "NEUTRAL":
        raise RuntimeError(
            f"{symbol}: fresh market direction is NEUTRAL"
        )

    if direction != fresh_direction:
        raise RuntimeError(
            f"{symbol}: Phase 5 direction {direction} "
            f"conflicts with fresh direction {fresh_direction}"
        )

    atr_value = market["atr"]
    entry = market["price"]

    extension = market["extension_atr"]

    if extension > MAX_ENTRY_EXTENSION_ATR:
        raise RuntimeError(
            f"{symbol}: anti-chase extension "
            f"{extension:.2f} ATR exceeds "
            f"{MAX_ENTRY_EXTENSION_ATR:.2f} ATR"
        )

    # Optional analytical/reference price from Phase 5.
    reference = number(
        candidate.get("price"),
        number(candidate.get("entry")),
    )

    reference_drift = None

    if reference is not None and atr_value > 0:
        reference_drift = (
            abs(entry - reference) / atr_value
        )

        if reference_drift > MAX_REFERENCE_DRIFT_ATR:
            raise RuntimeError(
                f"{symbol}: fresh price drift "
                f"{reference_drift:.2f} ATR exceeds "
                f"{MAX_REFERENCE_DRIFT_ATR:.2f} ATR"
            )

    risk_distance = atr_value * SL_ATR_MULTIPLIER

    if direction == "LONG":
        sl = entry - risk_distance
        tp1 = entry + (
            risk_distance * TP1_R_MULTIPLIER
        )
        tp2 = entry + (
            risk_distance * TP2_R_MULTIPLIER
        )
    else:
        sl = entry + risk_distance
        tp1 = entry - (
            risk_distance * TP1_R_MULTIPLIER
        )
        tp2 = entry - (
            risk_distance * TP2_R_MULTIPLIER
        )

    risk = abs(entry - sl)
    reward = abs(tp2 - entry)

    if risk <= 0:
        raise RuntimeError(f"{symbol}: zero risk")

    rr = reward / risk

    if rr < MIN_RR:
        raise RuntimeError(
            f"{symbol}: R:R {rr:.2f} below {MIN_RR:.2f}"
        )

    sizing = calculate_position_size(
        symbol,
        entry,
        sl,
    )

    return {
        "symbol": symbol,
        "direction": direction,

        # COMPLETE Phase 5 intelligence retained.
        "phase5_intelligence": candidate,

        # Fresh market truth.
        "fresh_market": market,

        # Executable construction.
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,

        "risk_distance": risk,
        "reward_distance": reward,
        "rr": rr,

        "position_size": sizing,

        "confidence": confidence,
        "reference_price": reference,
        "reference_drift_atr": reference_drift,

        "fresh_data_verified": True,
        "construction_method": "FRESH_PRICE_ATR",
        "entry_source": "FRESH_BINANCE_5M",
        "sl_source": "FRESH_ATR",
        "tp1_source": "RISK_MULTIPLE",
        "tp2_source": "RISK_MULTIPLE",
        "rr_source": "ACTUAL_ENTRY_SL_TP2",

        "status": "CONSTRUCTED",
        "phase": 6,
        "timestamp_utc": now(),
    }


# ------------------------------------------------------------
# MAIN PHASE 6
# ------------------------------------------------------------

def run_once():
    phase5_state, candidates = digest_phase5()

    constructed = []
    rejected = []

    print(
        f"PHASE 6 STARTING — DIGESTING "
        f"{len(candidates)} PHASE 5 INTELLIGENCE RECORDS",
        flush=True,
    )

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        symbol = str(
            candidate.get("symbol", "UNKNOWN")
        ).upper()

        print(
            f"PHASE 6 {index}/{len(candidates)} "
            f"DIGEST + REFRESH + CONSTRUCT {symbol}",
            flush=True,
        )

        try:
            market = fresh_market(symbol)

            trade = construct(
                candidate,
                market,
            )

            constructed.append(trade)

        except Exception as exc:
            rejected.append({
                "symbol": symbol,
                "phase": 6,
                "status": "REJECTED",
                "reason": str(exc),
                "timestamp_utc": now(),
            })

    constructed.sort(
        key=lambda x: (
            x.get("confidence", 0),
            x.get("rr", 0),
        ),
        reverse=True,
    )

    result = {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now(),

        "phase5_records_digest": len(candidates),
        "constructed": len(constructed),
        "rejected": len(rejected),

        "constructed_candidates": constructed,
        "rejected_candidates": rejected,

        "source": {
            "phase5_state": str(PHASE5_STATE),
            "phase5_completely_digested": True,
        },

        "ownership": {
            "entry": "PHASE_6",
            "sl": "PHASE_6",
            "tp1": "PHASE_6",
            "tp2": "PHASE_6",
            "rr": "PHASE_6",
            "position_size": "PHASE_6",
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "transmission_locked": True,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },
    }

    save(PHASE6_STATE, result)
    save(PHASE6_REPORT, result)

    print()
    print("=" * 78)
    print("CRYPTOMASTERX1 — PHASE 6 COMPLETE")
    print("=" * 78)
    print(f"Phase 5 intelligence digested : {len(candidates)}")
    print(f"Freshly evaluated              : {len(candidates)}")
    print(f"Trade-ready                    : {len(constructed)}")
    print(f"Rejected                       : {len(rejected)}")
    print()

    for i, item in enumerate(
        constructed,
        start=1,
    ):
        print(
            f"{i:2}. "
            f"{item['symbol']:<16} "
            f"{item['direction']:<6} "
            f"CONF:{item['confidence']:>6.2f} "
            f"ENTRY:{item['entry']} "
            f"SL:{item['sl']} "
            f"TP1:{item['tp1']} "
            f"TP2:{item['tp2']} "
            f"R:R:{item['rr']:.2f} "
            f"QTY:{item['position_size']['quantity_decimal']}"
        )

    print()
    print("Phase 6 owns Entry/SL/TP/R:R/Position Size.")
    print("Execution boundary: LOCKED")
    print("Order submission   : DISABLED")
    print("Withdrawals        : FORBIDDEN")
    print("=" * 78)

    return result


if __name__ == "__main__":
    import sys

    run_once()
