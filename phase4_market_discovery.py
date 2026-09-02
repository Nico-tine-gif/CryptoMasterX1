import os
#!/usr/bin/env python3
"""
CryptoMasterX1 — PHASE 4
MARKET DISCOVERY

OWNER:
    Discovery of the fresh Binance Spot/USDT universe.

RESPONSIBILITIES:
    - Discover currently tradable Spot/USDT symbols
    - Collect current 24h market statistics
    - Apply liquidity / activity filters
    - Classify bullish / bearish candidates
    - Produce the qualified universe consumed by Phase 5

PHASE 4 DOES NOT:
    - detect BOS / CHoCH
    - detect Order Blocks
    - detect FVG
    - construct entries
    - construct SL / TP
    - calculate position size
    - submit orders
    - withdraw funds
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
REPORT_DIR = ROOT / "reports"

STATE_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

BINANCE = "https://api.binance.com"

TIMEOUT = 15

MIN_QUOTE_VOLUME = 5_000_000.0
MIN_24H_TRADES = 10_000
MIN_ABS_CHANGE_PERCENT = 1.0
MAX_DISCOVERY_MARKETS = 200


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


def get_all_usdt():
    data = get_json(f"{BINANCE}/api/v3/exchangeInfo")

    symbols = []

    for item in data.get("symbols", []):
        symbol = item.get("symbol")
        status = item.get("status")
        quote_asset = item.get("quoteAsset")
        permissions = item.get("permissions", [])

        if (
            symbol
            and symbol.endswith("USDT")
            and status == "TRADING"
            and quote_asset == "USDT"
        ):
            # Spot permission when Binance provides permission metadata.
            if permissions and "SPOT" not in permissions:
                continue

            symbols.append(symbol)

    return sorted(set(symbols))


def get_24h():
    return get_json(f"{BINANCE}/api/v3/ticker/24hr")


def qualify_ticker(ticker):
    try:
        symbol = ticker["symbol"]
        volume = float(ticker["quoteVolume"])
        change = float(ticker["priceChangePercent"])
        trades = int(ticker["count"])
        last_price = float(ticker["lastPrice"])

        if volume < MIN_QUOTE_VOLUME:
            return None

        if trades < MIN_24H_TRADES:
            return None

        if abs(change) < MIN_ABS_CHANGE_PERCENT:
            return None

        if last_price <= 0:
            return None

        # Discovery quality is intentionally simple.
        # Detailed intelligence belongs to Phase 5.
        quality = 60.0

        quality += min(abs(change) * 2.0, 20.0)
        quality += min(volume / 50_000_000.0 * 10.0, 10.0)
        quality += min(trades / 100_000.0 * 10.0, 10.0)

        quality = min(100.0, quality)

        side = "BULL" if change > 0 else "BEAR"

        return {
            "symbol": symbol,
            "side": side,
            "priceChangePercent": round(change, 4),
            "quoteVolume24h": round(volume, 2),
            "trades24h": trades,
            "lastPrice": last_price,
            "quality": round(quality, 2),
        }

    except (KeyError, TypeError, ValueError):
        return None


def main():
    print("=" * 70)
    print("CMX1 — PHASE 4 MARKET DISCOVERY")
    print("=" * 70)

    try:
        eligible_symbols = get_all_usdt()
        tickers = get_24h()
    except Exception as exc:
        print(f"DISCOVERY ERROR: {exc}")
        raise SystemExit(1)

    eligible_set = set(eligible_symbols)

    qualified = []

    for ticker in tickers:
        if ticker.get("symbol") not in eligible_set:
            continue

        item = qualify_ticker(ticker)

        if item is not None:
            qualified.append(item)

    qualified.sort(
        key=lambda x: (
            x["quality"],
            x["quoteVolume24h"],
            abs(x["priceChangePercent"]),
        ),
        reverse=True,
    )

    qualified = qualified[:MAX_DISCOVERY_MARKETS]

    bulls = [
        item for item in qualified
        if item["side"] == "BULL"
    ]

    bears = [
        item for item in qualified
        if item["side"] == "BEAR"
    ]

    # Stable Phase 5 contract.
    markets = [
        {
            "symbol": item["symbol"],
            "priceChangePercent": item["priceChangePercent"],
            "quality": item["quality"],
            "quoteVolume24h": item["quoteVolume24h"],
            "trades24h": item["trades24h"],
            "lastPrice": item["lastPrice"],
            "discovery_side": item["side"],
        }
        for item in qualified
    ]

    output = {
        "phase": 4,
        "phase_name": "MARKET_DISCOVERY",
        "timestamp_utc": now_utc(),
        "data_source": "BINANCE_SPOT_REST",

        "eligible_markets": len(eligible_symbols),
        "qualified_markets": len(qualified),

        "discovery": {
            "markets": markets,
            "qualified_markets": len(markets),
            "eligible_markets": len(eligible_symbols),
        },

        "safe_bulls": bulls,
        "safe_bears": bears,

        "filters": {
            "min_quote_volume_24h": MIN_QUOTE_VOLUME,
            "min_trades_24h": MIN_24H_TRADES,
            "min_abs_price_change_percent": MIN_ABS_CHANGE_PERCENT,
            "max_discovery_markets": MAX_DISCOVERY_MARKETS,
        },

        "ownership": {
            "market_discovery": "PHASE_4",
            "market_intelligence": "PHASE_5",
            "trade_quality": "PHASE_6",
            "entry_intelligence": "PHASE_7",
            "entry_validation": "PHASE_8",
            "decision_gate": "PHASE_9",
            "execution_lifecycle": "PHASE_10",
        },

        "execution_boundary": {
            "execution_authorized": os.getenv("ALLOW_LIVE","false").lower()=="true",
            "live_execution": False,
            "bot_armed": False,
            "order_submission": False,
            "withdrawals": False,
            "transmission": "UNUNLOCKED",
        },
    }

    state_path = STATE_DIR / "phase4_market_discovery.json"
    state_path.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Eligible Spot USDT markets : {len(eligible_symbols)}")
    print(f"Qualified markets          : {len(qualified)}")
    print(f"Bull candidates             : {len(bulls)}")
    print(f"Bear candidates             : {len(bears)}")
    print(f"State saved                 : {state_path}")

    print()
    print("TOP BULLISH")
    for index, item in enumerate(bulls[:10], 1):
        print(
            f"{index:>2}. {item['symbol']:<14} "
            f"{item['priceChangePercent']:+7.2f}% "
            f"Q={item['quality']:.1f}"
        )

    print()
    print("TOP BEARISH")
    for index, item in enumerate(bears[:10], 1):
        print(
            f"{index:>2}. {item['symbol']:<14} "
            f"{item['priceChangePercent']:+7.2f}% "
            f"Q={item['quality']:.1f}"
        )


if __name__ == "__main__":
    main()
