#!/usr/bin/env python3
"""
CryptoMasterX1 — Binance-Wide Account-Aware Position Sizing
VERSION: 1.0-CLEAN

PURPOSE
-------
Converts Phase 9 qualified setups into validated Binance SPOT
position-sizing records.

IMPORTANT SAFETY BOUNDARY
-------------------------
This module:
    - DOES NOT submit orders
    - DOES NOT arm the bot
    - DOES NOT unlock Phase 10
    - DOES NOT enable live execution
    - DOES NOT withdraw
    - DOES NOT deposit
    - DOES NOT transfer funds
    - DOES NOT use Binance Futures endpoints

It only prepares and validates a quantity for a qualified setup.

CURRENT EXECUTION PRODUCT
-------------------------
Binance SPOT.

The architecture is deliberately product-aware so Futures-specific
/fapi endpoints cannot silently enter the Spot execution path.
"""

import json
import math
import time
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ============================================================
# PROJECT
# ============================================================

PROJECT = "CryptoMasterX1"
VERSION = "1.0-CLEAN"
PHASE = "POSITION_SIZING"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE9_STATE = STATE_DIR / "phase9_decision_gate.json"

SIZING_STATE = STATE_DIR / "position_sizing.json"
SIZING_REPORT = REPORT_DIR / "position_sizing_report.json"

# ============================================================
# BINANCE PRODUCT BOUNDARY
# ============================================================

BINANCE_SPOT_BASE = "https://api.binance.com"

# Explicitly Spot only.
BINANCE_PRODUCT = "SPOT"

# Futures endpoints are intentionally forbidden.
FORBIDDEN_PREFIXES = (
    "/fapi/",
    "/dapi/",
)

# ============================================================
# RISK POLICY
# ============================================================
#
# IMPORTANT:
# This is sizing preparation only.
# It does NOT authorize execution.
#
# Keep the risk percentage configurable.
#
# 0.50% = 0.005
# 1.00% = 0.010
#
# Change this only after deliberately selecting the desired
# risk policy.
# ============================================================

RISK_PER_TRADE = 0.005

# Optional maximum notional exposure.
# None means no additional notional cap here.
MAX_POSITION_NOTIONAL = None

# Do not calculate a position if the stop is invalid.
MIN_STOP_DISTANCE = Decimal("0")

# ============================================================
# HARD EXECUTION BOUNDARY
# ============================================================

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False

WITHDRAWALS = False
DEPOSITS = False
TRANSFERS = False


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, default=str)
    )


def decimal(value):
    return Decimal(str(value))


def floor_to_step(value, step):
    """
    Binance quantity rounding:
    always round DOWN to the exchange step size.
    """
    value = decimal(value)
    step = decimal(step)

    if step <= 0:
        raise ValueError("Invalid step size")

    units = (value / step).to_integral_value(
        rounding=ROUND_DOWN
    )

    return units * step


def decimal_string(value):
    """
    Clean Decimal representation for JSON.
    """
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


# ============================================================
# BINANCE HTTP
# ============================================================

def binance_get(path, params=None):
    """
    Public Binance REST request.

    This function refuses Futures endpoints.
    """

    if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        raise RuntimeError(
            f"BLOCKED: Futures endpoint forbidden: {path}"
        )

    if not path.startswith("/api/"):
        raise RuntimeError(
            f"BLOCKED: Non-Spot API path rejected: {path}"
        )

    url = BINANCE_SPOT_BASE + path

    if params:
        query = "&".join(
            f"{k}={v}"
            for k, v in params.items()
        )
        url += "?" + query

    request = Request(
        url,
        headers={
            "User-Agent": "CryptoMasterX1-Spot-Sizing/1.0"
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(
                response.read().decode()
            )

    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Binance HTTP {exc.code}: {body}"
        )

    except URLError as exc:
        raise RuntimeError(
            f"Binance network error: {exc}"
        )


# ============================================================
# SPOT EXCHANGE INFO
# ============================================================

def get_symbol_filters(symbol):
    """
    Reads Binance Spot exchangeInfo and extracts the
    quantity/notional filters for the requested symbol.
    """

    data = binance_get(
        "/api/v3/exchangeInfo",
        {"symbol": symbol},
    )

    symbols = data.get("symbols", [])

    if not symbols:
        raise RuntimeError(
            f"Symbol not found on Binance Spot: {symbol}"
        )

    info = symbols[0]

    if info.get("status") != "TRADING":
        raise RuntimeError(
            f"{symbol} is not currently TRADING"
        )

    filters = {
        item.get("filterType"): item
        for item in info.get("filters", [])
    }

    lot_filter = filters.get("LOT_SIZE")
    min_notional_filter = filters.get("MIN_NOTIONAL")
    notional_filter = filters.get("NOTIONAL")

    if not lot_filter:
        raise RuntimeError(
            f"{symbol}: Binance LOT_SIZE filter missing"
        )

    min_qty = decimal(
        lot_filter.get("minQty", "0")
    )

    max_qty = decimal(
        lot_filter.get("maxQty", "0")
    )

    step_size = decimal(
        lot_filter.get("stepSize", "0")
    )

    min_notional = Decimal("0")

    if min_notional_filter:
        min_notional = decimal(
            min_notional_filter.get(
                "minNotional",
                "0",
            )
        )

    if notional_filter:
        min_notional = max(
            min_notional,
            decimal(
                notional_filter.get(
                    "minNotional",
                    "0",
                )
            ),
        )

    return {
        "status": info.get("status"),
        "base_asset": info.get("baseAsset"),
        "quote_asset": info.get("quoteAsset"),
        "min_qty": min_qty,
        "max_qty": max_qty,
        "step_size": step_size,
        "min_notional": min_notional,
    }


# ============================================================
# SPOT ACCOUNT EQUITY
# ============================================================

def get_spot_usdt_balance():
    """
    Uses Binance SPOT account endpoint.

    This is deliberately NOT:
        /fapi/v2/balance
        /fapi/v2/positionRisk

    No Futures endpoint is used.
    """

    data = binance_get(
        "/api/v3/account"
    )

    balances = data.get("balances", [])

    for item in balances:
        if item.get("asset") == "USDT":
            free = decimal(
                item.get("free", "0")
            )
            locked = decimal(
                item.get("locked", "0")
            )

            return {
                "asset": "USDT",
                "free": free,
                "locked": locked,
                "total": free + locked,
            }

    return {
        "asset": "USDT",
        "free": Decimal("0"),
        "locked": Decimal("0"),
        "total": Decimal("0"),
    }


# ============================================================
# POSITION SIZING
# ============================================================

def size_candidate(candidate, account):
    """
    Converts one qualified Phase 9 candidate into a
    validated Spot quantity.

    No order is submitted.
    """

    symbol = candidate.get("symbol")
    direction = candidate.get("direction")

    entry = candidate.get("entry")
    sl = candidate.get("sl")
    tp1 = candidate.get("tp1")
    tp2 = candidate.get("tp2")

    result = {
        "symbol": symbol,
        "direction": direction,
        "confidence": candidate.get("confidence"),
        "rr": candidate.get("rr"),

        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,

        "risk_per_trade": RISK_PER_TRADE,

        "account_equity_usdt": None,
        "risk_amount_usdt": None,

        "stop_distance": None,
        "stop_distance_pct": None,

        "raw_quantity": None,
        "quantity": None,
        "notional_usdt": None,

        "min_qty": None,
        "step_size": None,
        "min_notional": None,

        "sizing_status": "REJECTED",
        "reasons": [],
    }

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not symbol:
        result["reasons"].append("MISSING_SYMBOL")
        return result

    if direction not in ("LONG", "SHORT"):
        result["reasons"].append("INVALID_DIRECTION")
        return result

    try:
        entry_d = decimal(entry)
        sl_d = decimal(sl)
    except Exception:
        result["reasons"].append("INVALID_ENTRY_OR_SL")
        return result

    if entry_d <= 0 or sl_d <= 0:
        result["reasons"].append("NON_POSITIVE_PRICE")
        return result

    # --------------------------------------------------------
    # Stop distance
    # --------------------------------------------------------

    if direction == "LONG":
        if sl_d >= entry_d:
            result["reasons"].append(
                "LONG_STOP_NOT_BELOW_ENTRY"
            )
            return result

        stop_distance = entry_d - sl_d

    else:
        if sl_d <= entry_d:
            result["reasons"].append(
                "SHORT_STOP_NOT_ABOVE_ENTRY"
            )
            return result

        stop_distance = sl_d - entry_d

    if stop_distance <= MIN_STOP_DISTANCE:
        result["reasons"].append(
            "INVALID_STOP_DISTANCE"
        )
        return result

    # --------------------------------------------------------
    # Account equity
    # --------------------------------------------------------

    equity = account["total"]
    free_balance = account["free"]

    result["account_equity_usdt"] = decimal_string(
        equity
    )

    if equity <= 0:
        result["reasons"].append(
            "NO_USDT_EQUITY"
        )
        return result

    if free_balance <= 0:
        result["reasons"].append(
            "NO_FREE_USDT_BALANCE"
        )
        return result

    # --------------------------------------------------------
    # Risk amount
    # --------------------------------------------------------

    risk_amount = equity * decimal(
        RISK_PER_TRADE
    )

    if risk_amount <= 0:
        result["reasons"].append(
            "INVALID_RISK_AMOUNT"
        )
        return result

    # --------------------------------------------------------
    # Raw quantity
    # --------------------------------------------------------

    raw_quantity = risk_amount / stop_distance

    if raw_quantity <= 0:
        result["reasons"].append(
            "INVALID_RAW_QUANTITY"
        )
        return result

    # --------------------------------------------------------
    # Binance Spot filters
    # --------------------------------------------------------

    try:
        filters = get_symbol_filters(symbol)
    except Exception as exc:
        result["reasons"].append(
            "EXCHANGE_FILTER_ERROR"
        )
        result["filter_error"] = str(exc)
        return result

    min_qty = filters["min_qty"]
    max_qty = filters["max_qty"]
    step_size = filters["step_size"]
    min_notional = filters["min_notional"]

    result["min_qty"] = decimal_string(min_qty)
    result["step_size"] = decimal_string(step_size)
    result["min_notional"] = decimal_string(
        min_notional
    )

    # --------------------------------------------------------
    # Step-size compliant quantity
    # --------------------------------------------------------

    quantity = floor_to_step(
        raw_quantity,
        step_size,
    )

    # Never exceed maximum exchange quantity.
    if max_qty > 0 and quantity > max_qty:
        quantity = floor_to_step(
            max_qty,
            step_size,
        )

    notional = quantity * entry_d

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if quantity < min_qty:
        result["reasons"].append(
            "QUANTITY_BELOW_MIN_QTY"
        )

    if min_notional > 0 and notional < min_notional:
        result["reasons"].append(
            "NOTIONAL_BELOW_MIN_NOTIONAL"
        )

    if free_balance > 0 and notional > free_balance:
        result["reasons"].append(
            "INSUFFICIENT_FREE_USDT"
        )

    if (
        MAX_POSITION_NOTIONAL is not None
        and notional >
        decimal(MAX_POSITION_NOTIONAL)
    ):
        result["reasons"].append(
            "MAX_POSITION_NOTIONAL_EXCEEDED"
        )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    result["risk_amount_usdt"] = decimal_string(
        risk_amount
    )

    result["stop_distance"] = decimal_string(
        stop_distance
    )

    result["stop_distance_pct"] = decimal_string(
        (stop_distance / entry_d) * Decimal("100")
    )

    result["raw_quantity"] = decimal_string(
        raw_quantity
    )

    result["quantity"] = decimal_string(
        quantity
    )

    result["notional_usdt"] = decimal_string(
        notional
    )

    if result["reasons"]:
        result["sizing_status"] = "REJECTED"
    else:
        result["sizing_status"] = "SIZED"

    return result


# ============================================================
# PHASE 9 LOADER
# ============================================================

def load_phase9():
    if not PHASE9_STATE.exists():
        raise RuntimeError(
            "Phase 9 state file not found"
        )

    state = json.loads(
        PHASE9_STATE.read_text()
    )

    gate = state.get(
        "decision_gate",
        {},
    )

    candidates = gate.get(
        "qualified_candidates",
        [],
    )

    if not isinstance(candidates, list):
        raise RuntimeError(
            "Phase 9 qualified_candidates is not a list"
        )

    return candidates


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — BINANCE SPOT POSITION SIZING"
    )
    print("=" * 78)

    print(f"Product               : {BINANCE_PRODUCT}")
    print(f"Risk per trade        : {RISK_PER_TRADE * 100:.3f}%")
    print(
        f"Execution authorized  : {EXECUTION_AUTHORIZED}"
    )
    print(
        f"Order submission      : {ORDER_SUBMISSION}"
    )
    print(
        f"Bot armed             : {BOT_ARMED}"
    )
    print(
        f"Live execution        : {LIVE_EXECUTION}"
    )

    # --------------------------------------------------------
    # Hard safety assertion
    # --------------------------------------------------------

    if EXECUTION_AUTHORIZED:
        raise RuntimeError(
            "SAFETY FAILURE: execution must remain disabled"
        )

    if ORDER_SUBMISSION:
        raise RuntimeError(
            "SAFETY FAILURE: order submission must remain disabled"
        )

    if BOT_ARMED:
        raise RuntimeError(
            "SAFETY FAILURE: bot must remain disarmed"
        )

    if LIVE_EXECUTION:
        raise RuntimeError(
            "SAFETY FAILURE: live execution must remain false"
        )

    print()
    print(
        "Execution boundary: LOCKED"
    )

    # --------------------------------------------------------
    # Load candidates
    # --------------------------------------------------------

    candidates = load_phase9()

    print(
        f"Phase 9 qualified candidates: "
        f"{len(candidates)}"
    )

    # --------------------------------------------------------
    # Read Spot account
    # --------------------------------------------------------

    print()
    print(
        "Reading Binance SPOT USDT account..."
    )

    account = get_spot_usdt_balance()

    print(
        f"Spot USDT free            : "
        f"{account['free']}"
    )

    print(
        f"Spot USDT locked          : "
        f"{account['locked']}"
    )

    print(
        f"Spot USDT total           : "
        f"{account['total']}"
    )

    # --------------------------------------------------------
    # Size candidates
    # --------------------------------------------------------

    sized = []
    rejected = []

    started = time.time()

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        symbol = candidate.get(
            "symbol",
            "UNKNOWN",
        )

        print(
            f"SIZING {index}/{len(candidates)} "
            f"{symbol}",
            flush=True,
        )

        result = size_candidate(
            candidate,
            account,
        )

        if result["sizing_status"] == "SIZED":
            sized.append(result)
        else:
            rejected.append(result)

    elapsed = round(
        time.time() - started,
        2,
    )

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    state = {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),

        "status": "SIZING_COMPLETE",

        "product": {
            "name": "BINANCE",
            "market": "SPOT",
            "futures_allowed": False,
        },

        "risk_policy": {
            "risk_per_trade": RISK_PER_TRADE,
            "max_position_notional":
                MAX_POSITION_NOTIONAL,
        },

        "input": {
            "source_phase": "PHASE_9",
            "phase9_candidates":
                len(candidates),
        },

        "results": {
            "evaluated":
                len(candidates),
            "sized":
                len(sized),
            "rejected":
                len(rejected),
            "scan_seconds":
                elapsed,
            "sized_candidates":
                sized,
            "rejected_candidates":
                rejected,
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

    save_json(
        SIZING_STATE,
        state,
    )

    save_json(
        SIZING_REPORT,
        state,
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print(
        "POSITION SIZING COMPLETE"
    )
    print("=" * 78)

    print(
        f"Evaluated : {len(candidates)}"
    )

    print(
        f"Sized    : {len(sized)}"
    )

    print(
        f"Rejected : {len(rejected)}"
    )

    print()

    if sized:
        print(
            "SIZED CANDIDATES"
        )
        print("-" * 78)

        for item in sized:
            print(
                f"{item['symbol']:<16} "
                f"{item['direction']:<6} "
                f"ENTRY: {item['entry']:<14} "
                f"SL: {item['sl']:<14} "
                f"QTY: {item['quantity']:<18} "
                f"NOTIONAL: {item['notional_usdt']}"
            )

    if rejected:
        print()
        print(
            "REJECTED CANDIDATES"
        )
        print("-" * 78)

        for item in rejected:
            print(
                f"{item['symbol']:<16} "
                f"{item['sizing_status']:<10} "
                f"{','.join(item['reasons'])}"
            )

    print()
    print("=" * 78)
    print(
        "BINANCE SPOT POSITION SIZING — READ-ONLY COMPLETE"
    )
    print("=" * 78)

    print()
    print(
        "Execution boundary: LOCKED"
    )
    print(
        "Order submission  : DISABLED"
    )
    print(
        "Bot armed         : NO"
    )
    print(
        "Live execution    : FALSE"
    )

    print()
    print(
        f"State saved: {SIZING_STATE}"
    )


if __name__ == "__main__":
    main()
