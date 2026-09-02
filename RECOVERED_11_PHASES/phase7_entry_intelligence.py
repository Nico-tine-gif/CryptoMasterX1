import json
import time
import math
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone


PROJECT = "CryptoMasterX1"
PHASE = "PHASE_7"
VERSION = "7.1-REAL-CONSTRUCTION"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE6_STATE = STATE_DIR / "phase6_trade_quality.json"
PHASE7_STATE = STATE_DIR / "phase7_entry_intelligence.json"
PHASE7_REPORT = REPORT_DIR / "phase7_entry_intelligence_report.json"

REFRESH_SECONDS = 60

# ------------------------------------------------------------------
# TRADE-CONSTRUCTION PARAMETERS
# ------------------------------------------------------------------

INTERVAL = "5m"
KLINE_LIMIT = 120

ATR_PERIOD = 14
EMA_FAST = 9
EMA_SLOW = 20

MIN_CONFIDENCE = 75.0
MIN_RR = 1.50

# Stop distance is based on fresh ATR.
SL_ATR_MULTIPLIER = 1.20

# TP1 and TP2 are constructed from actual risk.
TP1_R_MULTIPLIER = 1.50
TP2_R_MULTIPLIER = 2.50

# Anti-chase protection.
MAX_ENTRY_EXTENSION_ATR = 1.50

# Reject if fresh market price moved too far from
# the analytical candidate's reference price when available.
MAX_REFERENCE_DRIFT_ATR = 2.50

REQUEST_TIMEOUT = 15


# ------------------------------------------------------------------
# HARD EXECUTION SAFETY BOUNDARY
# ------------------------------------------------------------------

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False

WITHDRAWALS = False
DEPOSITS = False
TRANSFERS = False


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


# ------------------------------------------------------------------
# PHASE 6 INPUT
# ------------------------------------------------------------------

def load_phase6():
    if not PHASE6_STATE.exists():
        raise FileNotFoundError(
            f"Phase 6 state not found: {PHASE6_STATE}"
        )

    state = json.loads(PHASE6_STATE.read_text())

    quality = state.get("quality", {})
    approved = quality.get("approved", [])

    if not isinstance(approved, list):
        approved = []

    # Compatibility fallback only.
    if not approved:
        intelligence = state.get("intelligence", {})
        approved = intelligence.get("approved", [])

    if not isinstance(approved, list):
        approved = []

    return approved


# ------------------------------------------------------------------
# NUMERIC HELPERS
# ------------------------------------------------------------------

def number(value, default=0.0):
    try:
        value = float(value)
        if math.isfinite(value):
            return value
    except (TypeError, ValueError):
        pass

    return default


def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2.0 / (period + 1.0)

    value = sum(values[:period]) / period

    for price in values[period:]:
        value = (
            (price - value) * multiplier
            + value
        )

    return value


def true_ranges(candles):
    trs = []

    previous_close = None

    for candle in candles:
        high = candle["high"]
        low = candle["low"]
        close = candle["close"]

        if previous_close is None:
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )

        trs.append(tr)
        previous_close = close

    return trs


def atr(candles, period=ATR_PERIOD):
    trs = true_ranges(candles)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


# ------------------------------------------------------------------
# FRESH BINANCE MARKET FEED
# ------------------------------------------------------------------

def fetch_klines(symbol):
    params = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": KLINE_LIMIT,
        }
    )

    url = (
        "https://api.binance.com/api/v3/klines?"
        + params
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CryptoMasterX1/7.1",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)

    if not isinstance(data, list) or not data:
        raise RuntimeError(
            f"No klines returned for {symbol}"
        )

    candles = []

    for row in data:
        if len(row) < 7:
            continue

        candles.append(
            {
                "open_time": int(row[0]),
                "open": number(row[1]),
                "high": number(row[2]),
                "low": number(row[3]),
                "close": number(row[4]),
                "volume": number(row[5]),
                "close_time": int(row[6]),
            }
        )

    if len(candles) < max(
        ATR_PERIOD + 2,
        EMA_SLOW + 2,
    ):
        raise RuntimeError(
            f"Insufficient fresh candles for {symbol}"
        )

    return candles


# ------------------------------------------------------------------
# FRESH MARKET ANALYSIS USED ONLY BY PHASE 7
# ------------------------------------------------------------------

def analyze_fresh_market(symbol):
    candles = fetch_klines(symbol)

    # Ignore the currently forming candle for structural calculations.
    closed = candles[:-1]

    if len(closed) < EMA_SLOW + ATR_PERIOD:
        raise RuntimeError(
            f"Insufficient closed candles for {symbol}"
        )

    closes = [
        candle["close"]
        for candle in closed
    ]

    current_price = candles[-1]["close"]

    fast_ema = ema(
        closes,
        EMA_FAST,
    )

    slow_ema = ema(
        closes,
        EMA_SLOW,
    )

    fresh_atr = atr(
        closed,
        ATR_PERIOD,
    )

    if fresh_atr is None or fresh_atr <= 0:
        raise RuntimeError(
            f"Invalid ATR for {symbol}"
        )

    recent = closed[-20:]

    recent_high = max(
        candle["high"]
        for candle in recent
    )

    recent_low = min(
        candle["low"]
        for candle in recent
    )

    if fast_ema is None or slow_ema is None:
        raise RuntimeError(
            f"Invalid EMA structure for {symbol}"
        )

    if current_price > fast_ema > slow_ema:
        fresh_direction = "LONG"
    elif current_price < fast_ema < slow_ema:
        fresh_direction = "SHORT"
    else:
        fresh_direction = "NEUTRAL"

    extension_atr = (
        abs(current_price - fast_ema)
        / fresh_atr
    )

    return {
        "symbol": symbol,
        "price": current_price,
        "ema_fast": fast_ema,
        "ema_slow": slow_ema,
        "atr": fresh_atr,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "fresh_direction": fresh_direction,
        "extension_atr": extension_atr,
        "feed_candle_close_time": candles[-1]["close_time"],
        "feed_checked_utc": now_utc(),
    }


# ------------------------------------------------------------------
# PHASE 7 — ACTUAL TRADE CONSTRUCTION
# ------------------------------------------------------------------

def construct_trade(candidate, market):
    symbol = candidate.get("symbol")
    # --------------------------------------------------------------
    # PHASE 6 CONTRACT
    #
    # Direction is owned by market_bias.direction.
    # Phase-5 confidence is preserved by Phase 6 under
    # phase6_quality.phase5_confidence.
    # --------------------------------------------------------------
    market_bias = candidate.get(
        "market_bias",
        {},
    )

    analytical_direction = market_bias.get(
        "direction",
        candidate.get("direction"),
    )

    phase6_quality = candidate.get(
        "phase6_quality",
        {},
    )

    confidence = number(
        phase6_quality.get(
            "phase5_confidence",
            candidate.get(
                "phase6_confidence",
                candidate.get("confidence", 0),
            ),
        )
    )

    reasons = []

    if not symbol:
        reasons.append("MISSING_SYMBOL")

    if analytical_direction not in (
        "LONG",
        "SHORT",
    ):
        reasons.append(
            "INVALID_ANALYTICAL_DIRECTION"
        )

    if confidence < MIN_CONFIDENCE:
        reasons.append(
            "CONFIDENCE_BELOW_GATE"
        )

    fresh_direction = market["fresh_direction"]

    if fresh_direction == "NEUTRAL":
        reasons.append(
            "FRESH_MARKET_DIRECTION_NEUTRAL"
        )

    if (
        analytical_direction
        != fresh_direction
    ):
        reasons.append(
            "DIRECTION_CHANGED_ON_FRESH_FEED"
        )

    extension_atr = market["extension_atr"]

    if extension_atr > MAX_ENTRY_EXTENSION_ATR:
        reasons.append(
            "ANTI_CHASE_EXTENSION_TOO_HIGH"
        )

    # --------------------------------------------------------------
    # IMPORTANT:
    # Phase 5/6 trade levels are NEVER used.
    #
    # Entry, SL, TP1 and TP2 are constructed here from the
    # current fresh market price and fresh ATR.
    # --------------------------------------------------------------

    entry = market["price"]
    fresh_atr = market["atr"]

    risk_distance = (
        fresh_atr
        * SL_ATR_MULTIPLIER
    )

    if risk_distance <= 0:
        reasons.append(
            "INVALID_RISK_DISTANCE"
        )

    if analytical_direction == "LONG":
        sl = entry - risk_distance

        tp1 = (
            entry
            + risk_distance
            * TP1_R_MULTIPLIER
        )

        tp2 = (
            entry
            + risk_distance
            * TP2_R_MULTIPLIER
        )

    elif analytical_direction == "SHORT":
        sl = entry + risk_distance

        tp1 = (
            entry
            - risk_distance
            * TP1_R_MULTIPLIER
        )

        tp2 = (
            entry
            - risk_distance
            * TP2_R_MULTIPLIER
        )

    else:
        sl = None
        tp1 = None
        tp2 = None

    if (
        sl is None
        or tp1 is None
        or tp2 is None
    ):
        reasons.append(
            "TRADE_LEVEL_CONSTRUCTION_FAILED"
        )
        rr = 0.0
    else:
        risk = abs(entry - sl)
        reward = abs(tp2 - entry)

        if risk <= 0:
            rr = 0.0
            reasons.append(
                "ZERO_RISK"
            )
        else:
            rr = reward / risk

    if rr < MIN_RR:
        reasons.append(
            "RR_BELOW_GATE"
        )

    # Structural sanity.
    if analytical_direction == "LONG":
        if not (
            sl < entry < tp1 <= tp2
        ):
            reasons.append(
                "INVALID_LONG_PRICE_STRUCTURE"
            )

    elif analytical_direction == "SHORT":
        if not (
            tp2 <= tp1 < entry < sl
        ):
            reasons.append(
                "INVALID_SHORT_PRICE_STRUCTURE"
            )

    ready = not reasons

    return {
        "symbol": symbol,
        "direction": analytical_direction,
        "confidence": confidence,
        "phase6_quality_score": number(
            candidate.get(
                "phase6_quality",
                {},
            ).get("score")
        ),

        # These are NEW Phase 7 authoritative values.
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,

        "entry_ready": ready,
        "qualified": ready,
        "reasons": reasons,

        "source_phase": "PHASE_7",

        "construction": {
            "method": "FRESH_PRICE_ATR_CONSTRUCTION",
            "entry_source": "FRESH_BINANCE_5M_PRICE",
            "sl_source": "FRESH_ATR",
            "tp1_source": "RISK_MULTIPLE",
            "tp2_source": "RISK_MULTIPLE",
            "rr_source": "ACTUAL_ENTRY_SL_TP2",
        },

        "fresh_market": market,

        # Preserve analytical context.
        "rsi_5m": candidate.get(
            "rsi_5m",
            candidate.get("rsi", {}).get("5m")
            if isinstance(candidate.get("rsi"), dict)
            else None,
        ),
        "extension_atr": extension_atr,
        "h1_trend": candidate.get(
            "h1_trend",
            candidate.get("market_bias", {}).get("h1")
            if isinstance(candidate.get("market_bias"), dict)
            else None,
        ),
        "m15_trend": candidate.get(
            "m15_trend",
            candidate.get("market_bias", {}).get("m15")
            if isinstance(candidate.get("market_bias"), dict)
            else None,
        ),
        "m5_trend": candidate.get(
            "m5_trend",
            candidate.get("market_bias", {}).get("m5")
            if isinstance(candidate.get("market_bias"), dict)
            else None,
        ),
        "analytical_direction": analytical_direction,

        # ----------------------------------------------------------
        # FRESH-FEED EVIDENCE
        #
        # Phase 7 constructed this trade from the fresh Binance
        # market snapshot. Expose the evidence on the candidate so
        # downstream Phase 8 validation can independently verify
        # that construction was based on fresh market data.
        # ----------------------------------------------------------
        "fresh_direction": market.get(
            "fresh_direction"
        ),
        "feed_checked_utc": market.get(
            "feed_checked_utc"
        ),
        "feed_candle_close_time": market.get(
            "feed_candle_close_time"
        ),
    }


# ------------------------------------------------------------------
# PHASE 7 SCAN
# ------------------------------------------------------------------

def scan():
    candidates = load_phase6()

    results = []
    ready = []
    rejected = []

    started = time.time()

    print(
        f"PHASE 7 STARTING — "
        f"{len(candidates)} PHASE 6 APPROVED CANDIDATES",
        flush=True,
    )

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        symbol = candidate.get(
            "symbol",
            "UNKNOWN",
        )

        print(
            f"PHASE 7 FRESH CONSTRUCTION "
            f"{index}/{len(candidates)} "
            f"{symbol}",
            flush=True,
        )

        try:
            # Fresh Binance feed is mandatory.
            market = analyze_fresh_market(
                symbol
            )

            result = construct_trade(
                candidate,
                market,
            )

            results.append(result)

            if result["entry_ready"]:
                ready.append(result)
            else:
                rejected.append(result)

        except Exception as exc:
            failed = {
                "symbol": symbol,
                "entry_ready": False,
                "qualified": False,
                "reasons": [
                    f"FRESH_FEED_ERROR: {exc}"
                ],
                "source_phase": "PHASE_7",
            }

            # Every Phase 6 candidate must appear in the
            # evaluated population, including fresh-feed failures.
            results.append(failed)
            rejected.append(failed)

    ready.sort(
        key=lambda x: (
            number(x.get("confidence")),
            number(x.get("rr")),
        ),
        reverse=True,
    )

    elapsed = round(
        time.time() - started,
        2,
    )

    return {
        "phase6_candidates": len(candidates),
        "evaluated": len(results),
        "entry_ready": len(ready),
        "rejected": len(rejected),
        "scan_seconds": elapsed,
        "ready": ready,
        "rejected_candidates": rejected,
        "all_results": results,
    }


# ------------------------------------------------------------------
# STATE
# ------------------------------------------------------------------

def build_state(
    result,
    cycle,
    status="RUNNING",
):
    return {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "cycle": cycle,
        "status": status,

        "intelligence": {
            "phase6_candidates":
                result["phase6_candidates"],

            "evaluated":
                result["evaluated"],

            "entry_ready":
                result["entry_ready"],

            "rejected":
                result["rejected"],

            "scan_seconds":
                result["scan_seconds"],

            "ready":
                result["ready"],

            "rejected_candidates":
                result["rejected_candidates"],

            "all_results":
                result["all_results"],
        },

        "construction_contract": {
            "phase5_trade_levels_used": False,
            "phase6_trade_levels_used": False,
            "fresh_market_feed_required": True,
            "entry_constructed_here": True,
            "sl_constructed_here": True,
            "tp1_constructed_here": True,
            "tp2_constructed_here": True,
            "rr_calculated_here": True,
        },

        "gates": {
            "minimum_confidence":
                MIN_CONFIDENCE,

            "minimum_rr":
                MIN_RR,

            "anti_chase_max_extension_atr":
                MAX_ENTRY_EXTENSION_ATR,

            "fresh_direction_required":
                True,

            "fresh_feed_required":
                True,
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },
    }


# ------------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------------

def display(result, cycle):
    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — "
        "PHASE 7 TRADE CONSTRUCTION"
    )
    print("=" * 78)

    print(
        f"Cycle                    : {cycle}"
    )

    print(
        f"UTC                      : {now_utc()}"
    )

    print(
        "Phase 6 approved input   : "
        f"{result['phase6_candidates']}"
    )

    print(
        f"Freshly evaluated       : "
        f"{result['evaluated']}"
    )

    print(
        f"Trade-ready              : "
        f"{result['entry_ready']}"
    )

    print(
        f"Rejected                 : "
        f"{result['rejected']}"
    )

    print()
    print(
        "CONSTRUCTED TRADE CANDIDATES"
    )
    print("-" * 78)

    if not result["ready"]:
        print("None")

    else:
        for index, item in enumerate(
            result["ready"],
            start=1,
        ):
            print(
                f"{index:2}. "
                f"{item['symbol']:<16} "
                f"{item['direction']:<6} "
                f"CONF: {item['confidence']:.2f} "
                f"ENTRY: {item['entry']} "
                f"SL: {item['sl']} "
                f"TP1: {item['tp1']} "
                f"TP2: {item['tp2']} "
                f"R:R: {item['rr']:.2f}"
            )

    print()
    print("=" * 78)
    print(
        "PHASE 7 TRADE CONSTRUCTION COMPLETE"
    )
    print("=" * 78)

    print()
    print(
        "Phase 5 levels used : NO"
    )
    print(
        "Phase 6 levels used : NO"
    )
    print(
        "Fresh market feed  : REQUIRED"
    )
    print(
        "Entry constructed   : YES"
    )
    print(
        "SL constructed      : YES"
    )
    print(
        "TP1 constructed     : YES"
    )
    print(
        "TP2 constructed     : YES"
    )
    print(
        "R:R calculated      : YES"
    )

    print()
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
    print(
        "Withdrawals        : FORBIDDEN"
    )


# ------------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------------

def main():
    cycle = 0

    import sys

    once = "--once" in sys.argv

    while True:
        cycle += 1

        try:
            result = scan()

            state = build_state(
                result,
                cycle,
                "RUNNING",
            )

            save_json(
                PHASE7_STATE,
                state,
            )

            save_json(
                PHASE7_REPORT,
                state,
            )

            display(
                result,
                cycle,
            )

            if once:
                break

            print(
                f"\nNext Phase 7 scan in "
                f"{REFRESH_SECONDS} seconds...",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )

        except KeyboardInterrupt:
            if PHASE7_STATE.exists():
                try:
                    existing = json.loads(
                        PHASE7_STATE.read_text()
                    )
                except Exception:
                    existing = {}

                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                existing[
                    "execution_boundary"
                ] = {
                    "execution_authorized": False,
                    "order_submission": False,
                    "bot_armed": False,
                    "live_execution": False,
                    "withdrawals": False,
                    "deposits": False,
                    "transfers": False,
                }

                save_json(
                    PHASE7_STATE,
                    existing,
                )

            print(
                "\nPHASE 7 STOPPED — "
                "EXECUTION REMAINS LOCKED"
            )

            break

        except Exception as exc:
            print(
                f"PHASE 7 ERROR: {exc}",
                flush=True,
            )

            if once:
                raise

            time.sleep(
                REFRESH_SECONDS
            )


if __name__ == "__main__":
    main()
