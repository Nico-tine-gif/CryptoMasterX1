#!/usr/bin/env python3
"""
CryptoMasterX1 — PHASE 5
MARKET INTELLIGENCE ENGINE

PHASE 5 OWNER:
    Deep market intelligence / qualification.

PHASE 5 CONSUMES:
    Phase 4 fresh Binance Spot/USDT discovery universe.

PHASE 5 DETECTS:
    • Multi-timeframe trend/regime
    • Internal structure
    • Swing structure
    • BOS
    • CHoCH
    • Structure confluence
    • Internal Order Blocks
    • Swing Order Blocks
    • Order-block mitigation
    • Fair Value Gaps
    • FVG mitigation
    • Equal Highs / Equal Lows
    • Strong / Weak Highs / Lows
    • Premium / Discount / Equilibrium
    • ATR volatility
    • Momentum
    • RSI
    • EMA structure
    • Pullback / reclaim intelligence
    • Liquidity/activity context
    • Intelligence confidence
    • Bull / bear / neutral market bias
    • Intelligence qualification

PHASE 5 MUST NOT:
    • construct Entry
    • construct SL
    • construct TP1 / TP2
    • calculate risk
    • calculate reward
    • calculate R:R
    • calculate position size
    • submit orders
    • transmit orders
    • withdraw funds

IMPORTANT:
    Phase 5 produces intelligence for later phases.
    It does NOT become an execution phase.
"""

import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from datetime import datetime, timezone
from pathlib import Path

import requests


# ============================================================
# CORE
# ============================================================

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
REPORTS = ROOT / "reports"

STATE.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

PHASE4_STATE = STATE / "phase4_market_discovery.json"
PHASE5_STATE = STATE / "phase5_market_intelligence.json"

BINANCE = "https://api.binance.com"

# Fast/reliable feed configuration.
# Keep concurrency controlled to avoid Binance/API/network pressure.
REQUEST_CONNECT_TIMEOUT = 4
REQUEST_READ_TIMEOUT = 8
REQUEST_TIMEOUT = (
    REQUEST_CONNECT_TIMEOUT,
    REQUEST_READ_TIMEOUT,
)

MAX_WORKERS = 8
MAX_RETRIES = 3
RETRY_BACKOFF = 0.5

RETRY_STATUS_CODES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}

_thread_local = threading.local()


MIN_CONFIDENCE = 75.0

INTERNAL_PIVOT_LENGTH = 5
SWING_PIVOT_LENGTH = 50

ATR_PERIOD = 14
ATR_VOLATILITY_PERIOD = 200

RSI_PERIOD = 14

RSI_OVERBOUGHT = 75.0
RSI_OVERSOLD = 25.0

MAX_ORDER_BLOCKS = 100
DISPLAY_ORDER_BLOCKS = 20

FVG_AUTO_THRESHOLD = True
FVG_BODY_THRESHOLD = 0.50

EQ_SENSITIVITY = 0.15

PREMIUM_PERCENT = 0.05
EQUILIBRIUM_PERCENT = 0.05
DISCOUNT_PERCENT = 0.05

MAX_ANALYSIS_MARKETS = 100


# ============================================================
# TIME / I/O
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()



def get_session():
    """
    One requests.Session per worker thread.

    This gives us connection reuse/pooling without sharing a Session
    object across worker threads.
    """
    session = getattr(_thread_local, "session", None)

    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "CryptoMasterX1/Phase5",
            "Accept": "application/json",
            "Connection": "keep-alive",
        })
        _thread_local.session = session

    return session


def get_json(path, params=None):
    """
    Fast resilient Binance GET.

    Retries only transient HTTP/network failures.
    Does not hide permanent HTTP errors.
    """
    session = get_session()
    url = path

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.ok:
                return response.json()

            if response.status_code not in RETRY_STATUS_CODES:
                response.raise_for_status()

            last_error = requests.HTTPError(
                f"Binance HTTP {response.status_code}"
            )

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            last_error = exc

        except requests.RequestException as exc:
            last_error = exc
            break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF * (2 ** attempt))

    if last_error is not None:
        raise last_error

    raise RuntimeError("Binance request failed without an exception")


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


# ============================================================
# BINANCE DATA
# ============================================================


def fetch_klines(symbol, interval, limit=250):
    """
    Fetch fresh Binance Spot klines through the resilient pooled feed.
    """
    return get_json(
        f"{BINANCE}/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        },
    )


def candle_timestamp(candle):
    return int(candle[0])


def opens(candles):
    return [float(x[1]) for x in candles]


def highs(candles):
    return [float(x[2]) for x in candles]


def lows(candles):
    return [float(x[3]) for x in candles]


def closes(candles):
    return [float(x[4]) for x in candles]


def volumes(candles):
    return [float(x[5]) for x in candles]


def candle_body(candle):
    return abs(float(candle[4]) - float(candle[1]))


def candle_range(candle):
    return float(candle[2]) - float(candle[3])


def candle_bullish(candle):
    return float(candle[4]) > float(candle[1])


def candle_bearish(candle):
    return float(candle[4]) < float(candle[1])


# ============================================================
# INDICATORS
# ============================================================

def ema(values, period):
    if len(values) < period:
        return None

    value = sum(values[:period]) / period
    multiplier = 2.0 / (period + 1.0)

    for price in values[period:]:
        value = ((price - value) * multiplier) + value

    return value


def rsi(values, period=14):
    if len(values) <= period:
        return None

    gains = []
    losses = []

    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for index in range(period, len(gains)):
        avg_gain = (
            (avg_gain * (period - 1)) + gains[index]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1)) + losses[index]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100.0 - (100.0 / (1.0 + rs))


def true_ranges(candles):
    if len(candles) < 2:
        return []

    result = []

    for i in range(1, len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        previous_close = float(candles[i - 1][4])

        result.append(
            max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
        )

    return result


def atr(candles, period=14):
    trs = true_ranges(candles)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


def atr_average(candles, period=200):
    trs = true_ranges(candles)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


def normalized_atr(candles, period=14):
    value = atr(candles, period)

    if value is None:
        return None

    close = float(candles[-1][4])

    if close <= 0:
        return None

    return value / close


# ============================================================
# PIVOTS
# ============================================================

def detect_pivots(candles, length):
    """
    Confirmed pivot detector.

    A pivot is only accepted when enough candles exist on
    both sides. This prevents future-candle leakage.
    """

    if len(candles) < (length * 2 + 1):
        return [], []

    high_values = highs(candles)
    low_values = lows(candles)

    pivot_highs = []
    pivot_lows = []

    for i in range(length, len(candles) - length):

        current_high = high_values[i]
        current_low = low_values[i]

        left_highs = high_values[i - length:i]
        right_highs = high_values[i + 1:i + length + 1]

        left_lows = low_values[i - length:i]
        right_lows = low_values[i + 1:i + length + 1]

        if current_high > max(left_highs) and current_high >= max(right_highs):
            pivot_highs.append(
                {
                    "index": i,
                    "price": current_high,
                    "timestamp": candle_timestamp(candles[i]),
                }
            )

        if current_low < min(left_lows) and current_low <= min(right_lows):
            pivot_lows.append(
                {
                    "index": i,
                    "price": current_low,
                    "timestamp": candle_timestamp(candles[i]),
                }
            )

    return pivot_highs, pivot_lows


# ============================================================
# STRUCTURE
# ============================================================

def structure_events(candles, pivot_highs, pivot_lows):
    """
    Detect structural breaks from confirmed pivots.

    BOS:
        continuation through previous structural extreme.

    CHoCH:
        break against the previously established structural bias.
    """

    events = []

    highs_sorted = sorted(pivot_highs, key=lambda x: x["index"])
    lows_sorted = sorted(pivot_lows, key=lambda x: x["index"])

    pivot_sequence = []

    for item in highs_sorted:
        pivot_sequence.append(
            ("HIGH", item["index"], item["price"])
        )

    for item in lows_sorted:
        pivot_sequence.append(
            ("LOW", item["index"], item["price"])
        )

    pivot_sequence.sort(key=lambda x: x[1])

    bias = "NEUTRAL"

    last_high = None
    last_low = None

    used_high = set()
    used_low = set()

    close_values = closes(candles)

    for i in range(len(candles)):

        close = close_values[i]

        for item in highs_sorted:
            if item["index"] >= i:
                break

            if item["index"] not in used_high:
                if close > item["price"]:
                    previous_bias = bias

                    event_type = (
                        "BOS"
                        if previous_bias in ("BULL", "NEUTRAL")
                        else "CHoCH"
                    )

                    bias = "BULL"

                    events.append(
                        {
                            "type": event_type,
                            "direction": "BULL",
                            "index": i,
                            "broken_price": item["price"],
                            "pivot_index": item["index"],
                            "timestamp": candle_timestamp(candles[i]),
                        }
                    )

                    used_high.add(item["index"])

        for item in lows_sorted:
            if item["index"] >= i:
                break

            if item["index"] not in used_low:
                if close < item["price"]:
                    previous_bias = bias

                    event_type = (
                        "BOS"
                        if previous_bias in ("BEAR", "NEUTRAL")
                        else "CHoCH"
                    )

                    bias = "BEAR"

                    events.append(
                        {
                            "type": event_type,
                            "direction": "BEAR",
                            "index": i,
                            "broken_price": item["price"],
                            "pivot_index": item["index"],
                            "timestamp": candle_timestamp(candles[i]),
                        }
                    )

                    used_low.add(item["index"])

        if highs_sorted:
            prior = [
                x for x in highs_sorted
                if x["index"] < i
            ]
            if prior:
                last_high = prior[-1]

        if lows_sorted:
            prior = [
                x for x in lows_sorted
                if x["index"] < i
            ]
            if prior:
                last_low = prior[-1]

    return events, bias, last_high, last_low


# ============================================================
# ORDER BLOCKS
# ============================================================

def find_extreme_origin_candle(candles, break_index, direction, lookback=12):
    start = max(0, break_index - lookback)

    if direction == "BULL":
        candidates = [
            (i, candles[i])
            for i in range(start, break_index)
            if candle_bearish(candles[i])
        ]

        if not candidates:
            return None

        index, candle = min(
            candidates,
            key=lambda x: float(x[1][3]),
        )

    else:
        candidates = [
            (i, candles[i])
            for i in range(start, break_index)
            if candle_bullish(candles[i])
        ]

        if not candidates:
            return None

        index, candle = max(
            candidates,
            key=lambda x: float(x[1][2]),
        )

    return index, candle


def detect_order_blocks(candles, events, structure_name):
    blocks = []

    for event in events:

        origin = find_extreme_origin_candle(
            candles,
            event["index"],
            event["direction"],
        )

        if origin is None:
            continue

        origin_index, candle = origin

        high = float(candle[2])
        low = float(candle[3])

        if event["direction"] == "BULL":
            ob_type = "DEMAND"
        else:
            ob_type = "SUPPLY"

        blocks.append(
            {
                "structure": structure_name,
                "direction": event["direction"],
                "type": ob_type,
                "origin_index": origin_index,
                "origin_timestamp": candle_timestamp(candle),
                "top": high,
                "bottom": low,
                "break_index": event["index"],
                "break_timestamp": event["timestamp"],
                "mitigation_method": "CLOSE",
                "mitigated": False,
                "active": True,
            }
        )

    return blocks[-MAX_ORDER_BLOCKS:]


def mitigate_order_blocks(candles, blocks):
    result = []

    for block in blocks:

        mitigated = False

        for i in range(block["break_index"] + 1, len(candles)):
            candle = candles[i]

            close = float(candle[4])
            high = float(candle[2])
            low = float(candle[3])

            if block["direction"] == "BULL":
                if close <= block["bottom"]:
                    mitigated = True
                    break
            else:
                if close >= block["top"]:
                    mitigated = True
                    break

        item = dict(block)
        item["mitigated"] = mitigated
        item["active"] = not mitigated

        result.append(item)

    return result


# ============================================================
# FAIR VALUE GAPS
# ============================================================

def detect_fvgs(candles):
    gaps = []

    if len(candles) < 3:
        return gaps

    for i in range(2, len(candles)):

        first = candles[i - 2]
        middle = candles[i - 1]
        third = candles[i]

        first_high = float(first[2])
        first_low = float(first[3])

        third_high = float(third[2])
        third_low = float(third[3])

        body = candle_body(middle)
        rng = candle_range(middle)

        body_ratio = (
            body / rng
            if rng > 0
            else 0
        )

        if FVG_AUTO_THRESHOLD and body_ratio < FVG_BODY_THRESHOLD:
            continue

        # Bullish FVG:
        # current low > high two candles back
        if third_low > first_high:

            gaps.append(
                {
                    "direction": "BULL",
                    "top": third_low,
                    "bottom": first_high,
                    "index": i,
                    "timestamp": candle_timestamp(third),
                    "body_ratio": round(body_ratio, 4),
                    "mitigated": False,
                    "active": True,
                }
            )

        # Bearish FVG:
        # current high < low two candles back
        elif third_high < first_low:

            gaps.append(
                {
                    "direction": "BEAR",
                    "top": first_low,
                    "bottom": third_high,
                    "index": i,
                    "timestamp": candle_timestamp(third),
                    "body_ratio": round(body_ratio, 4),
                    "mitigated": False,
                    "active": True,
                }
            )

    return gaps


def mitigate_fvgs(candles, gaps):
    result = []

    for gap in gaps:

        mitigated = False

        for i in range(gap["index"] + 1, len(candles)):
            candle = candles[i]

            high = float(candle[2])
            low = float(candle[3])

            if gap["direction"] == "BULL":
                if low <= gap["bottom"]:
                    mitigated = True
                    break
            else:
                if high >= gap["top"]:
                    mitigated = True
                    break

        item = dict(gap)
        item["mitigated"] = mitigated
        item["active"] = not mitigated

        result.append(item)

    return result


# ============================================================
# EQUAL HIGH / LOW
# ============================================================

def detect_equal_levels(candles, pivot_highs, pivot_lows, atr_value):
    eq_highs = []
    eq_lows = []

    if atr_value is None or atr_value <= 0:
        return eq_highs, eq_lows

    threshold = atr_value * EQ_SENSITIVITY

    for i in range(1, len(pivot_highs)):
        a = pivot_highs[i - 1]
        b = pivot_highs[i]

        if abs(a["price"] - b["price"]) <= threshold:
            eq_highs.append(
                {
                    "type": "EQH",
                    "price": round(
                        (a["price"] + b["price"]) / 2,
                        12,
                    ),
                    "first_index": a["index"],
                    "second_index": b["index"],
                    "threshold": threshold,
                }
            )

    for i in range(1, len(pivot_lows)):
        a = pivot_lows[i - 1]
        b = pivot_lows[i]

        if abs(a["price"] - b["price"]) <= threshold:
            eq_lows.append(
                {
                    "type": "EQL",
                    "price": round(
                        (a["price"] + b["price"]) / 2,
                        12,
                    ),
                    "first_index": a["index"],
                    "second_index": b["index"],
                    "threshold": threshold,
                }
            )

    return eq_highs, eq_lows


# ============================================================
# STRONG / WEAK EXTREMES
# ============================================================

def classify_extremes(pivot_highs, pivot_lows, bias):
    strong_high = None
    weak_high = None
    strong_low = None
    weak_low = None

    if pivot_highs:
        latest_high = pivot_highs[-1]

        if bias == "BEAR":
            strong_high = latest_high
        else:
            weak_high = latest_high

    if pivot_lows:
        latest_low = pivot_lows[-1]

        if bias == "BULL":
            strong_low = latest_low
        else:
            weak_low = latest_low

    return {
        "strong_high": strong_high,
        "weak_high": weak_high,
        "strong_low": strong_low,
        "weak_low": weak_low,
    }


# ============================================================
# PREMIUM / DISCOUNT
# ============================================================

def premium_discount(candles, pivot_highs, pivot_lows):
    if not pivot_highs or not pivot_lows:
        return {
            "zone": "UNKNOWN",
            "range_high": None,
            "range_low": None,
            "equilibrium": None,
        }

    range_high = pivot_highs[-1]["price"]
    range_low = pivot_lows[-1]["price"]

    if range_high <= range_low:
        return {
            "zone": "UNKNOWN",
            "range_high": range_high,
            "range_low": range_low,
            "equilibrium": None,
        }

    current = float(candles[-1][4])

    total_range = range_high - range_low
    equilibrium = range_low + (total_range * 0.50)

    premium_start = range_high - (
        total_range * PREMIUM_PERCENT
    )

    discount_end = range_low + (
        total_range * DISCOUNT_PERCENT
    )

    equilibrium_low = equilibrium - (
        total_range * EQUILIBRIUM_PERCENT
    )

    equilibrium_high = equilibrium + (
        total_range * EQUILIBRIUM_PERCENT
    )

    if current >= premium_start:
        zone = "PREMIUM"

    elif current <= discount_end:
        zone = "DISCOUNT"

    elif equilibrium_low <= current <= equilibrium_high:
        zone = "EQUILIBRIUM"

    elif current > equilibrium:
        zone = "PREMIUM"

    else:
        zone = "DISCOUNT"

    return {
        "zone": zone,
        "current_price": current,
        "range_high": range_high,
        "range_low": range_low,
        "equilibrium": equilibrium,
        "premium_start": premium_start,
        "discount_end": discount_end,
        "equilibrium_low": equilibrium_low,
        "equilibrium_high": equilibrium_high,
    }


# ============================================================
# TREND / MOMENTUM
# ============================================================

def trend_score(values):
    if len(values) < 50:
        return 0.0

    e9 = ema(values, 9)
    e20 = ema(values, 20)
    e50 = ema(values, 50)

    if None in (e9, e20, e50):
        return 0.0

    score = 0.0

    score += 1.0 if e9 > e20 else -1.0
    score += 1.0 if e20 > e50 else -1.0
    score += 1.0 if values[-1] > e20 else -1.0

    return score / 3.0


def momentum_score(values):
    if len(values) < 20:
        return 0.0

    previous = values[-6]
    current = values[-1]

    if previous == 0:
        return 0.0

    pct = ((current - previous) / previous) * 100.0

    return max(-1.0, min(1.0, pct / 5.0))


def ema_context(values):
    return {
        "ema9": ema(values, 9),
        "ema20": ema(values, 20),
        "ema50": ema(values, 50),
    }


# ============================================================
# PULLBACK / RECLAIM
# ============================================================

def pullback_reclaim(values, direction):
    if len(values) < 15:
        return {
            "pullback": False,
            "reclaim": False,
        }

    recent = values[-12:]

    if direction == "BULL":
        peak = max(recent[:-2])
        current = values[-1]

        pullback = current < peak

        reclaim = (
            current > values[-2]
            and current > statistics.mean(recent[-5:])
        )

    elif direction == "BEAR":
        trough = min(recent[:-2])
        current = values[-1]

        pullback = current > trough

        reclaim = (
            current < values[-2]
            and current < statistics.mean(recent[-5:])
        )

    else:
        pullback = False
        reclaim = False

    return {
        "pullback": bool(pullback),
        "reclaim": bool(reclaim),
    }


# ============================================================
# FRESHNESS
# ============================================================

def validate_feed(candles):
    if not candles:
        return {
            "fresh": False,
            "reason": "NO_CANDLES",
        }

    timestamps = [
        candle_timestamp(x)
        for x in candles
    ]

    if timestamps != sorted(timestamps):
        return {
            "fresh": False,
            "reason": "TIMESTAMP_ORDER_INVALID",
        }

    if len(set(timestamps)) != len(timestamps):
        return {
            "fresh": False,
            "reason": "DUPLICATE_TIMESTAMPS",
        }

    latest = timestamps[-1]

    now_ms = int(
        datetime.now(timezone.utc).timestamp() * 1000
    )

    # Binance may return the currently forming candle.
    # We only require that the feed timestamp is not in the future.
    if latest > now_ms:
        return {
            "fresh": False,
            "reason": "FUTURE_CANDLE",
        }

    return {
        "fresh": True,
        "latest_timestamp": latest,
        "reason": "OK",
    }


# ============================================================
# CONFLUENCE
# ============================================================

def structure_confluence(
    internal_events,
    swing_events,
    direction,
    current_price,
):
    score = 0
    reasons = []

    recent_internal = [
        x for x in internal_events
        if x["direction"] == direction
    ]

    recent_swing = [
        x for x in swing_events
        if x["direction"] == direction
    ]

    if recent_internal:
        score += 1
        reasons.append("INTERNAL_STRUCTURE")

    if recent_swing:
        score += 2
        reasons.append("SWING_STRUCTURE")

    if recent_internal and recent_swing:
        score += 2
        reasons.append("MULTI_STRUCTURE_CONFLUENCE")

    return {
        "score": score,
        "max_score": 5,
        "qualified": score >= 2,
        "reasons": reasons,
        "current_price": current_price,
    }


# ============================================================
# SYMBOL INTELLIGENCE
# ============================================================

def analyze_symbol(symbol, discovery_record=None):
    print(f"INTELLIGENCE {symbol}", flush=True)

    h1 = fetch_klines(symbol, "1h", 250)
    m15 = fetch_klines(symbol, "15m", 250)
    m5 = fetch_klines(symbol, "5m", 250)

    feed_h1 = validate_feed(h1)
    feed_m15 = validate_feed(m15)
    feed_m5 = validate_feed(m5)

    if not (
        feed_h1["fresh"]
        and feed_m15["fresh"]
        and feed_m5["fresh"]
    ):
        return {
            "symbol": symbol,
            "timestamp_utc": now_utc(),
            "qualified": False,
            "data_fresh": False,
            "feed_health": {
                "h1": feed_h1,
                "m15": feed_m15,
                "m5": feed_m5,
            },
            "phase5_owner": "MARKET_INTELLIGENCE",
        }

    h1c = closes(h1)
    m15c = closes(m15)
    m5c = closes(m5)

    current_price = m5c[-1]

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    h1_trend = trend_score(h1c)
    m15_trend = trend_score(m15c)
    m5_trend = trend_score(m5c)

    h1_direction = (
        "BULL" if h1_trend > 0
        else "BEAR" if h1_trend < 0
        else "NEUTRAL"
    )

    m15_direction = (
        "BULL" if m15_trend > 0
        else "BEAR" if m15_trend < 0
        else "NEUTRAL"
    )

    m5_direction = (
        "BULL" if m5_trend > 0
        else "BEAR" if m5_trend < 0
        else "NEUTRAL"
    )

    # --------------------------------------------------------
    # Structure
    # --------------------------------------------------------

    internal_highs, internal_lows = detect_pivots(
        m5,
        INTERNAL_PIVOT_LENGTH,
    )

    swing_highs, swing_lows = detect_pivots(
        m15,
        SWING_PIVOT_LENGTH,
    )

    internal_events, internal_bias, _, _ = structure_events(
        m5,
        internal_highs,
        internal_lows,
    )

    swing_events, swing_bias, _, _ = structure_events(
        m15,
        swing_highs,
        swing_lows,
    )

    # --------------------------------------------------------
    # Order Blocks
    # --------------------------------------------------------

    internal_obs = detect_order_blocks(
        m5,
        internal_events,
        "INTERNAL",
    )

    swing_obs = detect_order_blocks(
        m15,
        swing_events,
        "SWING",
    )

    internal_obs = mitigate_order_blocks(
        m5,
        internal_obs,
    )

    swing_obs = mitigate_order_blocks(
        m15,
        swing_obs,
    )

    active_internal_obs = [
        x for x in internal_obs
        if x["active"]
    ]

    active_swing_obs = [
        x for x in swing_obs
        if x["active"]
    ]

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    fvgs = detect_fvgs(m5)
    fvgs = mitigate_fvgs(m5, fvgs)

    active_fvgs = [
        x for x in fvgs
        if x["active"]
    ]

    # --------------------------------------------------------
    # Equal Highs / Lows
    # --------------------------------------------------------

    atr5 = atr(m5, ATR_PERIOD)

    eq_highs, eq_lows = detect_equal_levels(
        m5,
        internal_highs,
        internal_lows,
        atr5,
    )

    # --------------------------------------------------------
    # Strong / Weak
    # --------------------------------------------------------

    extremes = classify_extremes(
        swing_highs,
        swing_lows,
        swing_bias,
    )

    # --------------------------------------------------------
    # Premium / Discount
    # --------------------------------------------------------

    pd_zone = premium_discount(
        m15,
        swing_highs,
        swing_lows,
    )

    # --------------------------------------------------------
    # Momentum / RSI / ATR
    # --------------------------------------------------------

    momentum = (
        momentum_score(h1c)
        + momentum_score(m15c)
        + momentum_score(m5c)
    ) / 3.0

    rsi5 = rsi(m5c, RSI_PERIOD)

    atr5_average = atr_average(
        m5,
        ATR_VOLATILITY_PERIOD,
    )

    volatility_ratio = (
        atr5 / atr5_average
        if atr5 is not None
        and atr5_average
        and atr5_average > 0
        else None
    )

    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

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

    structure_direction = (
        "BULL"
        if direction == "LONG"
        else "BEAR"
        if direction == "SHORT"
        else "NEUTRAL"
    )

    # --------------------------------------------------------
    # Structure confluence
    # --------------------------------------------------------

    confluence = structure_confluence(
        internal_events,
        swing_events,
        structure_direction,
        current_price,
    )

    # --------------------------------------------------------
    # Pullback / reclaim
    # --------------------------------------------------------

    pullback = pullback_reclaim(
        m5c,
        structure_direction,
    )

    # --------------------------------------------------------
    # Intelligence confidence
    # --------------------------------------------------------

    confidence = 50.0

    confidence += abs(direction_score) * 20.0
    confidence += abs(momentum) * 10.0

    if internal_bias == structure_direction:
        confidence += 5.0

    if swing_bias == structure_direction:
        confidence += 10.0

    if confluence["qualified"]:
        confidence += 5.0

    if pullback["pullback"]:
        confidence += 2.5

    if pullback["reclaim"]:
        confidence += 2.5

    if rsi5 is not None:

        if direction == "LONG" and rsi5 >= RSI_OVERBOUGHT:
            confidence -= 10.0

        if direction == "SHORT" and rsi5 <= RSI_OVERSOLD:
            confidence -= 10.0

    confidence = max(
        0.0,
        min(100.0, confidence),
    )

    qualified = (
        direction in ("LONG", "SHORT")
        and confidence >= MIN_CONFIDENCE
        and confluence["qualified"]
        and feed_h1["fresh"]
        and feed_m15["fresh"]
        and feed_m5["fresh"]
    )

    # --------------------------------------------------------
    # Final intelligence record
    # --------------------------------------------------------

    return {
        "symbol": symbol,
        "timestamp_utc": now_utc(),
        "data_source": "BINANCE_SPOT_REST",
        "data_fresh": True,

        "discovery": discovery_record or {},

        "market_bias": {
            "direction": direction,
            "h1": h1_direction,
            "m15": m15_direction,
            "m5": m5_direction,
            "h1_score": round(h1_trend, 4),
            "m15_score": round(m15_trend, 4),
            "m5_score": round(m5_trend, 4),
        },

        "structure": {
            "internal": {
                "pivot_length": INTERNAL_PIVOT_LENGTH,
                "bias": internal_bias,
                "pivot_highs": internal_highs[-20:],
                "pivot_lows": internal_lows[-20:],
                "events": internal_events[-20:],
                "bull_events": [
                    x for x in internal_events
                    if x["direction"] == "BULL"
                ][-10:],
                "bear_events": [
                    x for x in internal_events
                    if x["direction"] == "BEAR"
                ][-10:],
            },

            "swing": {
                "pivot_length": SWING_PIVOT_LENGTH,
                "bias": swing_bias,
                "pivot_highs": swing_highs[-20:],
                "pivot_lows": swing_lows[-20:],
                "events": swing_events[-20:],
                "bull_events": [
                    x for x in swing_events
                    if x["direction"] == "BULL"
                ][-10:],
                "bear_events": [
                    x for x in swing_events
                    if x["direction"] == "BEAR"
                ][-10:],
            },

            "confluence": confluence,
        },

        "order_blocks": {
            "internal": internal_obs[-DISPLAY_ORDER_BLOCKS:],
            "swing": swing_obs[-DISPLAY_ORDER_BLOCKS:],
            "active_internal": len(active_internal_obs),
            "active_swing": len(active_swing_obs),
            "total_active": (
                len(active_internal_obs)
                + len(active_swing_obs)
            ),
            "mitigation_method": "CLOSE",
        },

        "fair_value_gaps": {
            "active": active_fvgs[-DISPLAY_ORDER_BLOCKS:],
            "active_count": len(active_fvgs),
            "total_detected": len(fvgs),
            "auto_threshold": FVG_AUTO_THRESHOLD,
            "body_threshold": FVG_BODY_THRESHOLD,
        },

        "equal_levels": {
            "equal_highs": eq_highs[-20:],
            "equal_lows": eq_lows[-20:],
            "sensitivity": EQ_SENSITIVITY,
        },

        "strong_weak": extremes,

        "premium_discount": pd_zone,

        "volatility": {
            "atr_5m": atr5,
            "atr_average_200": atr5_average,
            "atr_ratio": volatility_ratio,
        },

        "momentum": round(momentum, 4),

        "rsi": {
            "period": RSI_PERIOD,
            "5m": round(rsi5, 4)
            if rsi5 is not None
            else None,
        },

        "ema": {
            "h1": ema_context(h1c),
            "m15": ema_context(m15c),
            "m5": ema_context(m5c),
        },

        "pullback_reclaim": pullback,

        "current_price": current_price,

        "intelligence": {
            "confidence": round(confidence, 2),
            "qualified": qualified,
            "minimum_confidence": MIN_CONFIDENCE,
            "classification": (
                "QUALIFIED"
                if qualified
                else "REJECTED"
            ),
        },

        "feed_health": {
            "h1": feed_h1,
            "m15": feed_m15,
            "m5": feed_m5,
        },

        "dashboard": {
            "swing_bias": swing_bias,
            "internal_bias": internal_bias,
            "active_ob_count": (
                len(active_internal_obs)
                + len(active_swing_obs)
            ),
            "active_fvg_count": len(active_fvgs),
            "last_signal": (
                swing_events[-1]["type"]
                if swing_events
                else internal_events[-1]["type"]
                if internal_events
                else "NONE"
            ),
            "direction": direction,
            "confidence": round(confidence, 2),
        },

        "phase5_owner": "MARKET_INTELLIGENCE",

        # HARD CONSTRUCTION BOUNDARY
        "trade_construction": {
            "entry": None,
            "sl": None,
            "tp1": None,
            "tp2": None,
            "risk": None,
            "reward": None,
            "rr": None,
            "position_size": None,
        },

        "execution_boundary": {
            "execution_authorized": False,
            "live_execution": False,
            "bot_armed": False,
            "order_submission": False,
            "withdrawals": False,
            "transmission": "LOCKED",
        },
    }


# ============================================================
# PHASE 4 CONTRACT
# ============================================================

def get_phase4_markets():
    data = load_json(PHASE4_STATE)

    markets = (
        data
        .get("discovery", {})
        .get("markets", [])
    )

    result = []

    for item in markets:
        if not isinstance(item, dict):
            continue

        symbol = item.get("symbol")

        if not symbol:
            continue

        result.append(item)

    unique = {}

    for item in result:
        unique[item["symbol"]] = item

    return list(unique.values())[:MAX_ANALYSIS_MARKETS]


# ============================================================
# MAIN
# ============================================================


def main():
    print("=" * 70)
    print("CMX1 — PHASE 5 MARKET INTELLIGENCE")
    print("=" * 70)

    try:
        markets = get_phase4_markets()
    except Exception as exc:
        print(f"PHASE 4 CONTRACT ERROR: {exc}")
        raise SystemExit(1)

    print(f"Phase 4 markets received : {len(markets)}")
    print(f"Parallel workers         : {MAX_WORKERS}")
    print(f"Network retries          : {MAX_RETRIES}")
    print()

    results = []
    qualified = []
    errors = []

    scan_started = time.monotonic()

    # --------------------------------------------------------
    # Concurrent intelligence scan
    # --------------------------------------------------------

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                analyze_symbol,
                discovery_record["symbol"],
                discovery_record,
            ): discovery_record["symbol"]
            for discovery_record in markets
        }

        for future in as_completed(futures):
            symbol = futures[future]

            try:
                result = future.result()
                results.append(result)

                if result.get("intelligence", {}).get("qualified"):
                    qualified.append(result)

            except Exception as exc:
                errors.append(
                    {
                        "symbol": symbol,
                        "error": str(exc),
                        "timestamp_utc": now_utc(),
                    }
                )

                print(
                    f"INTELLIGENCE ERROR {symbol}: {exc}",
                    flush=True,
                )

    elapsed = time.monotonic() - scan_started

    # Stable ordering for state/report reproducibility.
    results.sort(key=lambda x: x.get("symbol", ""))
    qualified.sort(
        key=lambda x: x.get("intelligence", {}).get(
            "confidence",
            0.0,
        ),
        reverse=True,
    )
    errors.sort(key=lambda x: x.get("symbol", ""))

    # --------------------------------------------------------
    # Coverage / feed-health contract
    # --------------------------------------------------------

    markets_received = len(markets)
    markets_analyzed = len(results)
    error_count = len(errors)

    coverage = (
        (markets_analyzed / markets_received) * 100.0
        if markets_received
        else 0.0
    )

    scan_complete = (
        markets_received > 0
        and markets_analyzed == markets_received
        and error_count == 0
    )

    scan_status = (
        "COMPLETE"
        if scan_complete
        else "INCOMPLETE"
    )

    # --------------------------------------------------------
    # Dashboard summary
    # --------------------------------------------------------

    long_candidates = [
        x for x in qualified
        if x.get("market_bias", {}).get("direction") == "LONG"
    ]

    short_candidates = [
        x for x in qualified
        if x.get("market_bias", {}).get("direction") == "SHORT"
    ]

    output = {
        "phase": 5,
        "phase_name": "MARKET_INTELLIGENCE",
        "timestamp_utc": now_utc(),
        "data_source": "BINANCE_SPOT_REST",
        "source_phase": 4,

        "markets_received": markets_received,
        "markets_analyzed": markets_analyzed,
        "qualified_candidates": len(qualified),
        "long_candidates": len(long_candidates),
        "short_candidates": len(short_candidates),

        "results": results,
        "qualified": qualified,
        "errors": errors,

        "feed_performance": {
            "scan_status": scan_status,
            "scan_complete": scan_complete,
            "coverage_percent": round(coverage, 2),
            "elapsed_seconds": round(elapsed, 3),
            "max_workers": MAX_WORKERS,
            "request_retries": MAX_RETRIES,
            "connect_timeout_seconds": REQUEST_CONNECT_TIMEOUT,
            "read_timeout_seconds": REQUEST_READ_TIMEOUT,
            "failed_markets": error_count,
        },

        "detectors": {
            "internal_structure": True,
            "swing_structure": True,
            "bos": True,
            "choch": True,
            "structure_confluence": True,
            "internal_order_blocks": True,
            "swing_order_blocks": True,
            "order_block_mitigation": True,
            "fair_value_gaps": True,
            "fvg_mitigation": True,
            "equal_highs": True,
            "equal_lows": True,
            "strong_weak_high_low": True,
            "premium_discount_equilibrium": True,
            "atr_volatility": True,
            "momentum": True,
            "rsi": True,
            "ema_context": True,
            "pullback_reclaim": True,
            "feed_freshness": True,
        },

        "configuration": {
            "internal_pivot_length": INTERNAL_PIVOT_LENGTH,
            "swing_pivot_length": SWING_PIVOT_LENGTH,
            "atr_period": ATR_PERIOD,
            "atr_volatility_period": ATR_VOLATILITY_PERIOD,
            "rsi_period": RSI_PERIOD,
            "min_confidence": MIN_CONFIDENCE,
            "max_order_blocks": MAX_ORDER_BLOCKS,
            "display_order_blocks": DISPLAY_ORDER_BLOCKS,
            "fvg_auto_threshold": FVG_AUTO_THRESHOLD,
            "fvg_body_threshold": FVG_BODY_THRESHOLD,
            "eq_sensitivity": EQ_SENSITIVITY,
            "max_analysis_markets": MAX_ANALYSIS_MARKETS,
            "max_workers": MAX_WORKERS,
            "max_retries": MAX_RETRIES,
        },

        "ownership": {
            "phase4": "MARKET_DISCOVERY",
            "phase5": "MARKET_INTELLIGENCE",
            "phase6": "TRADE_QUALITY",
            "phase7": "ENTRY_INTELLIGENCE",
            "phase8": "ENTRY_VALIDATION",
            "phase9": "DECISION_GATE",
            "phase10": "EXECUTION_AND_LIFECYCLE",
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
            "order_transmission",
            "withdrawal",
        ],

        "execution_boundary": {
            "execution_authorized": False,
            "live_execution": False,
            "bot_armed": False,
            "order_submission": False,
            "withdrawals": False,
            "transmission": "LOCKED",
        },
    }

    save_json(
        PHASE5_STATE,
        output,
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    report_path = (
        REPORTS / "phase5_market_intelligence.txt"
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as report:
        report.write("CMX1 — PHASE 5 MARKET INTELLIGENCE\n")
        report.write("=" * 60 + "\n")
        report.write(
            f"Timestamp UTC       : {output['timestamp_utc']}\n"
        )
        report.write(
            f"Markets received    : {markets_received}\n"
        )
        report.write(
            f"Markets analyzed    : {markets_analyzed}\n"
        )
        report.write(
            f"Qualified           : {len(qualified)}\n"
        )
        report.write(
            f"Long candidates     : {len(long_candidates)}\n"
        )
        report.write(
            f"Short candidates    : {len(short_candidates)}\n"
        )
        report.write(
            f"Errors              : {error_count}\n"
        )
        report.write(
            f"Coverage            : {coverage:.2f}%\n"
        )
        report.write(
            f"Scan status         : {scan_status}\n"
        )
        report.write(
            f"Elapsed seconds     : {elapsed:.3f}\n"
        )
        report.write(
            f"Parallel workers    : {MAX_WORKERS}\n"
        )

        if not scan_complete:
            report.write(
                "\nWARNING: INCOMPLETE MARKET COVERAGE — "
                "DOWNSTREAM USE MUST NOT TREAT THIS SCAN AS COMPLETE.\n"
            )

        report.write("\nQUALIFIED INTELLIGENCE\n")

        for item in qualified:
            report.write(
                f"{item['symbol']:<15} "
                f"{item['market_bias']['direction']:<7} "
                f"CONF={item['intelligence']['confidence']:>5.1f} "
                f"SWING={item['structure']['swing']['bias']:<7} "
                f"INTERNAL={item['structure']['internal']['bias']:<7} "
                f"OB={item['dashboard']['active_ob_count']:<3} "
                f"FVG={item['dashboard']['active_fvg_count']:<3}\n"
            )

        if errors:
            report.write("\nFAILED MARKETS\n")

            for item in errors:
                report.write(
                    f"{item['symbol']:<15} "
                    f"{item['error']}\n"
                )

        report.write("\nEXECUTION BOUNDARY\n")
        report.write("EXECUTION_AUTHORIZED : FALSE\n")
        report.write("LIVE_EXECUTION       : FALSE\n")
        report.write("BOT_ARMED            : FALSE\n")
        report.write("ORDER_SUBMISSION     : FALSE\n")
        report.write("WITHDRAWALS          : FALSE\n")
        report.write("TRANSMISSION         : LOCKED\n")

    print()
    print("=" * 70)
    print("PHASE 5 INTELLIGENCE COMPLETE")
    print("=" * 70)
    print(f"Markets received : {markets_received}")
    print(f"Markets analyzed : {markets_analyzed}")
    print(f"Qualified        : {len(qualified)}")
    print(f"Long             : {len(long_candidates)}")
    print(f"Short            : {len(short_candidates)}")
    print(f"Errors           : {error_count}")
    print(f"Coverage         : {coverage:.2f}%")
    print(f"Scan status      : {scan_status}")
    print(f"Elapsed          : {elapsed:.3f}s")
    print()
    print(f"State  : {PHASE5_STATE}")
    print(f"Report : {report_path}")
    print()
    print("EXECUTION_AUTHORIZED : FALSE")
    print("LIVE_EXECUTION       : FALSE")
    print("BOT_ARMED            : FALSE")
    print("ORDER_SUBMISSION     : FALSE")
    print("WITHDRAWALS          : FALSE")
    print("TRANSMISSION         : LOCKED")


if __name__ == "__main__":
    main()