from account_binding import get_client
#!/usr/bin/env python3

"""
CryptoMasterX1
PHASE 6 — TRADE VERIFICATION + FINAL CONSTRUCTION

OWNER:
    Final trade construction.

PHASE 6 owns:
    Entry
    SL
    TP1
    TP2
    Risk
    Reward
    R:R
    Account-aware position size
    Exchange quantity-step validation

PHASE 6 DOES NOT:
    - submit orders
    - arm execution
    - enable live trading
    - withdraw funds
"""

import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"

PHASE5_STATE = STATE / "phase5_market_intelligence.json"
PHASE6_STATE = STATE / "phase6_trade_intelligence.json"

BINANCE = "https://api.binance.com"
TIMEOUT = 15

# Trade construction
SL_ATR_MULTIPLIER = Decimal("1.20")
TP1_R_MULTIPLIER = Decimal("1.50")
TP2_R_MULTIPLIER = Decimal("2.50")

# Account risk
RISK_PER_TRADE = Decimal("0.005")
MIN_RR = Decimal("1.50")

# Safety boundary
EXECUTION_AUTHORIZED = False
BOT_ARMED = False
LIVE_EXECUTION = False
ORDER_SUBMISSION = False
WITHDRAWALS = False


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def get_json(path, params=None):
    response = requests.get(
        path,
        params=params,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def current_price(symbol):
    data = get_json(
        f"{BINANCE}/api/v3/ticker/price",
        {"symbol": symbol},
    )

    return Decimal(str(data["price"]))


def exchange_symbol_info(symbol):
    data = get_json(
        f"{BINANCE}/api/v3/exchangeInfo",
        {"symbol": symbol},
    )

    symbols = data.get("symbols", [])

    if not symbols:
        raise ValueError(f"No exchange information for {symbol}")

    return symbols[0]


def get_filter(symbol_info, filter_type):
    for item in symbol_info.get("filters", []):
        if item.get("filterType") == filter_type:
            return item

    return None


def floor_step(value, step):
    if step <= 0:
        return value

    return (
        value / step
    ).to_integral_value(
        rounding=ROUND_DOWN
    ) * step


def get_account_usdt_balance():
    """
    Reads the Binance Spot account balance.

    This function only reads account state.
    It does NOT submit an order.
    """

    # Account endpoint requires authenticated credentials.
    # If credentials are not configured, sizing falls back to
    # an explicit NOT_AVAILABLE state rather than inventing
    # an account balance.

    try:

        client = get_client()

        account = client.get_account()

        for balance in account.get("balances", []):
            if balance.get("asset") == "USDT":
                return Decimal(str(balance.get("free", "0")))

    except Exception as exc:
        print(
            f"ACCOUNT BALANCE READ UNAVAILABLE: {exc}",
            flush=True,
        )

    return None


def calculate_position_size(
    symbol,
    entry,
    sl,
    account_balance,
):
    """
    Calculate quantity from account risk.

    Risk capital =
        account balance × RISK_PER_TRADE

    Quantity =
        risk capital / price distance to SL

    Quantity is then reduced to Binance LOT_SIZE step size.

    No order is submitted.
    """

    if account_balance is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "ACCOUNT_BALANCE_UNAVAILABLE",
            "quantity": None,
        }

    if account_balance <= 0:
        return {
            "status": "REJECTED",
            "reason": "NON_POSITIVE_ACCOUNT_BALANCE",
            "quantity": None,
        }

    risk_distance = abs(entry - sl)

    if risk_distance <= 0:
        return {
            "status": "REJECTED",
            "reason": "ZERO_STOP_DISTANCE",
            "quantity": None,
        }

    risk_capital = account_balance * RISK_PER_TRADE

    raw_quantity = risk_capital / risk_distance

    info = exchange_symbol_info(symbol)

    lot_filter = get_filter(info, "LOT_SIZE")
    min_notional_filter = get_filter(info, "MIN_NOTIONAL")
    notional_filter = get_filter(info, "NOTIONAL")

    if lot_filter is None:
        return {
            "status": "REJECTED",
            "reason": "LOT_SIZE_FILTER_UNAVAILABLE",
            "quantity": None,
        }

    step_size = Decimal(str(lot_filter["stepSize"]))
    min_qty = Decimal(str(lot_filter["minQty"]))
    max_qty = Decimal(str(lot_filter["maxQty"]))

    quantity = floor_step(raw_quantity, step_size)

    if quantity < min_qty:
        return {
            "status": "REJECTED",
            "reason": "QUANTITY_BELOW_MINIMUM",
            "quantity": float(quantity),
            "min_quantity": float(min_qty),
        }

    if quantity > max_qty:
        quantity = max_qty

    notional = quantity * entry

    minimum_notional = Decimal("0")

    if min_notional_filter:
        minimum_notional = Decimal(
            str(min_notional_filter.get("minNotional", "0"))
        )

    if notional_filter:
        minimum_notional = max(
            minimum_notional,
            Decimal(
                str(
                    notional_filter.get(
                        "minNotional",
                        "0",
                    )
                )
            ),
        )

    if notional < minimum_notional:
        return {
            "status": "REJECTED",
            "reason": "NOTIONAL_BELOW_MINIMUM",
            "quantity": float(quantity),
            "notional": float(notional),
            "minimum_notional": float(minimum_notional),
        }

    return {
        "status": "VALID",
        "reason": "POSITION_SIZE_VALID",
        "quantity": float(quantity),
        "raw_quantity": float(raw_quantity),
        "risk_capital": float(risk_capital),
        "risk_per_trade": float(RISK_PER_TRADE),
        "risk_distance": float(risk_distance),
        "notional": float(notional),
        "step_size": float(step_size),
        "min_quantity": float(min_qty),
        "max_quantity": float(max_qty),
        "minimum_notional": float(minimum_notional),
    }


def build_trade(candidate, account_balance):
    symbol = candidate["symbol"]
    direction = candidate.get("direction")

    live_price = current_price(symbol)

    atr_value = Decimal(
        str(candidate["atr_5m"])
    )

    if atr_value <= 0:
        return None

    risk_distance = (
        atr_value * SL_ATR_MULTIPLIER
    )

    if direction == "LONG":

        entry = live_price
        sl = entry - risk_distance
        tp1 = entry + (
            risk_distance * TP1_R_MULTIPLIER
        )
        tp2 = entry + (
            risk_distance * TP2_R_MULTIPLIER
        )

    elif direction == "SHORT":

        entry = live_price
        sl = entry + risk_distance
        tp1 = entry - (
            risk_distance * TP1_R_MULTIPLIER
        )
        tp2 = entry - (
            risk_distance * TP2_R_MULTIPLIER
        )

    else:
        return None

    risk = abs(entry - sl)
    reward = abs(tp2 - entry)

    if risk <= 0:
        return None

    rr = reward / risk

    if rr < MIN_RR:
        return None

    sizing = calculate_position_size(
        symbol,
        entry,
        sl,
        account_balance,
    )

    return {
        "symbol": symbol,
        "direction": direction,

        "constructed_at_utc": now_utc(),

        "market_data_source":
            "BINANCE_SPOT_REST",

        "price_refreshed_before_construction":
            True,

        "entry": float(entry),
        "sl": float(sl),
        "tp1": float(tp1),
        "tp2": float(tp2),

        "risk": float(risk),
        "reward": float(reward),
        "rr": float(rr),

        "risk_per_trade":
            float(RISK_PER_TRADE),

        "account_balance_usdt":
            float(account_balance)
            if account_balance is not None
            else None,

        "position_size":
            sizing.get("quantity"),

        "position_sizing":
            sizing,

        "phase5_confidence":
            candidate.get("confidence"),

        "phase6_owner":
            "TRADE_VERIFICATION_FINAL_CONSTRUCTION",

        "execution_authorized":
            EXECUTION_AUTHORIZED,

        "order_submission":
            ORDER_SUBMISSION,
    }


def main():
    STATE.mkdir(exist_ok=True)

    source = load_json(PHASE5_STATE)

    candidates = source.get("qualified", [])

    print(
        f"PHASE 5 candidates : {len(candidates)}",
        flush=True,
    )

    print(
        "Reading account balance...",
        flush=True,
    )

    account_balance = get_account_usdt_balance()

    if account_balance is None:
        print(
            "Account balance: UNAVAILABLE",
            flush=True,
        )
    else:
        print(
            f"Account balance: {account_balance} USDT",
            flush=True,
        )

    constructed = []
    sizing_valid = 0
    sizing_unavailable = 0
    sizing_rejected = 0

    for candidate in candidates:

        try:
            trade = build_trade(
                candidate,
                account_balance,
            )

            if trade is None:
                continue

            constructed.append(trade)

            status = trade[
                "position_sizing"
            ].get("status")

            if status == "VALID":
                sizing_valid += 1

            elif status == "UNAVAILABLE":
                sizing_unavailable += 1

            else:
                sizing_rejected += 1

        except Exception as exc:

            print(
                f"CONSTRUCTION ERROR "
                f"{candidate.get('symbol')}: {exc}",
                flush=True,
            )

    output = {
        "phase": 6,

        "phase_name":
            "TRADE VERIFICATION + FINAL CONSTRUCTION",

        "timestamp_utc":
            now_utc(),

        "phase5_candidates":
            len(candidates),

        "constructed_trades":
            len(constructed),

        "position_sizing_valid":
            sizing_valid,

        "position_sizing_unavailable":
            sizing_unavailable,

        "position_sizing_rejected":
            sizing_rejected,

        "account_balance_available":
            account_balance is not None,

        "risk_per_trade":
            float(RISK_PER_TRADE),

        "minimum_rr":
            float(MIN_RR),

        "trades":
            constructed,

        "ownership": {
            "trade_intelligence":
                "PHASE_5",

            "final_construction":
                "PHASE_6",

            "execution":
                "PHASE_7",

            "lifecycle":
                "PHASE_8",
        },

        "execution_boundary": {
            "execution_authorized":
                EXECUTION_AUTHORIZED,

            "bot_armed":
                BOT_ARMED,

            "live_execution":
                LIVE_EXECUTION,

            "order_submission":
                ORDER_SUBMISSION,

            "withdrawals":
                WITHDRAWALS,
        },
    }

    save_json(
        PHASE6_STATE,
        output,
    )

    print()
    print(
        "PHASE 6 — TRADE VERIFICATION "
        "+ FINAL CONSTRUCTION"
    )

    print(
        f"Phase 5 candidates : "
        f"{len(candidates)}"
    )

    print(
        f"Constructed trades : "
        f"{len(constructed)}"
    )

    print(
        f"Position sizes VALID: "
        f"{sizing_valid}"
    )

    print(
        f"Sizing unavailable  : "
        f"{sizing_unavailable}"
    )

    print(
        f"Sizing rejected     : "
        f"{sizing_rejected}"
    )

    print(
        f"State saved         : "
        f"{PHASE6_STATE}"
    )

    print(
        "ORDER SUBMISSION    : LOCKED"
    )

    print(
        "WITHDRAWALS         : FORBIDDEN"
    )


if __name__ == "__main__":
    main()
