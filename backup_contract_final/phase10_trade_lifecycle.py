import json
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_10"
VERSION = "10.0-CLEAN"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE9_STATE = STATE_DIR / "phase9_decision_gate.json"
PHASE10_STATE = STATE_DIR / "phase10_trade_lifecycle.json"
PHASE10_REPORT = REPORT_DIR / "phase10_trade_lifecycle_report.json"

REFRESH_SECONDS = 60
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"

# ============================================================
# HARD EXECUTION BOUNDARY
# ============================================================

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, default=str)
    )


def load_phase9():
    # Try main state
    if PHASE9_STATE.exists():
        try:
            state = json.loads(PHASE9_STATE.read_text())
            gate = state.get("decision_gate", state)
            candidates = gate.get("qualified_candidates", [])
            if isinstance(candidates, list) and len(candidates) > 0:
                return candidates
        except Exception:
            pass

    # Fallback - your real file
    fallback = STATE_DIR / "phase9_decision_gate.json"
    if fallback.exists():
        try:
            state = json.loads(fallback.read_text())
            gate = state.get("decision_gate", state)
            candidates = gate.get("qualified_candidates", [])
            return candidates if isinstance(candidates, list) else []
        except Exception:
            pass

    return []
    state = json.loads(PHASE9_STATE.read_text())

    gate = state.get("decision_gate", {})

    candidates = gate.get(
        "qualified_candidates",
        []
    )

    if not isinstance(candidates, list):
        candidates = []

    return candidates


def get_market_price(symbol):
    try:
        request = Request(
            f"{BINANCE_URL}?symbol={symbol}",
            headers={
                "User-Agent":
                    "CryptoMasterX1-Phase10/1.0"
            },
        )

        with urlopen(request, timeout=10) as response:
            data = json.loads(
                response.read().decode()
            )

        price = float(data["price"])

        if price <= 0:
            raise ValueError(
                "Invalid market price"
            )

        return price, "OK", None

    except Exception as exc:
        return None, "ERROR", str(exc)


def monitor_trade(candidate, market_price):
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

        "market_price": market_price,

        "lifecycle_status": "MONITORING",
        "event": "NONE",

        "closed": False,
        "exit_reason": None,
        "realized_r": None,

        "source_phase": "PHASE_9",
        "timestamp_utc": now_utc(),
    }

    if market_price is None:
        result["lifecycle_status"] = (
            "PRICE_UNAVAILABLE"
        )
        result["event"] = "NO_MARKET_PRICE"
        return result

    try:
        entry = float(entry)
        sl = float(sl)
        tp1 = float(tp1)
        tp2 = float(tp2)
        price = float(market_price)

    except (TypeError, ValueError):
        result["lifecycle_status"] = (
            "INVALID_LEVELS"
        )
        result["event"] = "INVALID_LEVEL_DATA"
        return result

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    if direction == "LONG":

        if price <= sl:
            result["lifecycle_status"] = "CLOSED_LOSS"
            result["event"] = "SL_HIT"
            result["closed"] = True
            result["exit_reason"] = "STOP_LOSS"

        elif price >= tp2:
            result["lifecycle_status"] = "CLOSED_WIN"
            result["event"] = "TP2_HIT"
            result["closed"] = True
            result["exit_reason"] = "TAKE_PROFIT_2"

        elif price >= tp1:
            result["lifecycle_status"] = "TP1_REACHED"
            result["event"] = "TP1_HIT"

        elif price >= entry:
            result["lifecycle_status"] = (
                "MONITORING_PROFIT"
            )
            result["event"] = "ABOVE_ENTRY"

        else:
            result["lifecycle_status"] = (
                "MONITORING_PULLBACK"
            )
            result["event"] = "BELOW_ENTRY"

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    elif direction == "SHORT":

        if price >= sl:
            result["lifecycle_status"] = "CLOSED_LOSS"
            result["event"] = "SL_HIT"
            result["closed"] = True
            result["exit_reason"] = "STOP_LOSS"

        elif price <= tp2:
            result["lifecycle_status"] = "CLOSED_WIN"
            result["event"] = "TP2_HIT"
            result["closed"] = True
            result["exit_reason"] = "TAKE_PROFIT_2"

        elif price <= tp1:
            result["lifecycle_status"] = "TP1_REACHED"
            result["event"] = "TP1_HIT"

        elif price <= entry:
            result["lifecycle_status"] = (
                "MONITORING_PROFIT"
            )
            result["event"] = "BELOW_ENTRY"

        else:
            result["lifecycle_status"] = (
                "MONITORING_PULLBACK"
            )
            result["event"] = "ABOVE_ENTRY"

    else:
        result["lifecycle_status"] = (
            "INVALID_DIRECTION"
        )
        result["event"] = "INVALID_DIRECTION"

    return result


def scan():

    candidates = load_phase9()

    results = []
    monitoring = []
    closed = []
    price_errors = 0

    started = time.time()

    print(
        f"PHASE 10 STARTING — "
        f"{len(candidates)} PHASE 9 QUALIFIED CANDIDATES",
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
            f"PHASE 10 MONITORING "
            f"{index}/{len(candidates)} "
            f"{symbol}",
            flush=True,
        )

        price, price_status, price_error = (
            get_market_price(symbol)
        )

        if price is None:
            price_errors += 1

        result = monitor_trade(
            candidate,
            price,
        )

        result["price_status"] = price_status
        result["price_error"] = price_error

        results.append(result)

        if result["closed"]:
            closed.append(result)
        else:
            monitoring.append(result)

    elapsed = round(
        time.time() - started,
        2,
    )

    return {
        "phase9_candidates": len(candidates),
        "evaluated": len(results),
        "monitoring": len(monitoring),
        "closed": len(closed),
        "price_errors": price_errors,
        "scan_seconds": elapsed,
        "monitoring_candidates": monitoring,
        "closed_candidates": closed,
        "all_results": results,
    }


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

        "lifecycle": {
            "phase9_candidates":
                result["phase9_candidates"],

            "evaluated":
                result["evaluated"],

            "monitoring":
                result["monitoring"],

            "closed":
                result["closed"],

            "price_errors":
                result["price_errors"],

            "scan_seconds":
                result["scan_seconds"],

            "monitoring_candidates":
                result["monitoring_candidates"],

            "closed_candidates":
                result["closed_candidates"],

            "all_results":
                result["all_results"],
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


def display(
    result,
    cycle,
):

    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — "
        "PHASE 10 TRADE LIFECYCLE / MONITORING"
    )
    print("=" * 78)

    print(
        f"Cycle                    : {cycle}"
    )
    print(
        f"UTC                      : {now_utc()}"
    )
    print(
        f"Phase 9 qualified input  : "
        f"{result['phase9_candidates']}"
    )
    print(
        f"Evaluated                : "
        f"{result['evaluated']}"
    )
    print(
        f"Monitoring               : "
        f"{result['monitoring']}"
    )
    print(
        f"Closed                   : "
        f"{result['closed']}"
    )
    print(
        f"Price errors             : "
        f"{result['price_errors']}"
    )

    print()
    print("LIFECYCLE STATUS")
    print("-" * 78)

    if not result["all_results"]:
        print("None")

    else:

        for index, item in enumerate(
            result["all_results"],
            start=1,
        ):

            price = item.get(
                "market_price"
            )

            if price is None:
                price_text = "UNAVAILABLE"
            else:
                price_text = str(price)

            print(
                f"{index:2}. "
                f"{item['symbol']:<16} "
                f"{item['direction']:<6} "
                f"PRICE: {price_text:<14} "
                f"STATUS: "
                f"{item['lifecycle_status']:<22} "
                f"EVENT: {item['event']}"
            )

    print()
    print("=" * 78)
    print(
        "PHASE 10 TRADE LIFECYCLE / "
        "MONITORING COMPLETE"
    )
    print("=" * 78)

    print()
    print(f"Execution boundary: {'UNLOCKED' if EXECUTION_AUTHORIZED else 'LOCKED'}")
    print(f"Order submission   : {'ENABLED' if ORDER_SUBMISSION else 'DISABLED'}")
    print(f"Bot armed          : {'YES' if BOT_ARMED else 'NO'}")
    print(f"Live execution     : {str(LIVE_EXECUTION).upper()}")

def main():

    cycle = 0

    while True:

        cycle += 1

        try:

            result = scan()

            state = build_state(
                result,
                cycle,
                "RUNNING",
            )

            # Phase 10 writes ONLY its own files.
            save_json(
                PHASE10_STATE,
                state,
            )

            save_json(
                PHASE10_REPORT,
                state,
            )

            display(
                result,
                cycle,
            )

            print(
                f"\nNext Phase 10 scan in "
                f"{REFRESH_SECONDS} seconds...",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )

        except KeyboardInterrupt:

            if PHASE10_STATE.exists():

                existing = json.loads(
                    PHASE10_STATE.read_text()
                )

                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                save_json(
                    PHASE10_STATE,
                    existing,
                )

            print(
                "\nPHASE 10 STOPPED.",
                flush=True,
            )

            break

        except Exception as exc:

            print(
                f"PHASE 10 ERROR: {exc}",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )


if __name__ == "__main__":
    main()
