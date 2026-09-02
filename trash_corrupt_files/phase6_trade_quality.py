#!/usr/bin/env python3
"""
CryptoMasterX1 — PHASE 6
TRADE QUALITY ENGINE

OWNER:
    Trade-quality qualification of Phase 5 intelligence.

CONSUMES:
    Phase 5 MARKET_INTELLIGENCE state.

PHASE 6 DOES:
    • Validate Phase 5 completion/coverage
    • Validate intelligence records
    • Evaluate multi-timeframe alignment
    • Evaluate structure alignment
    • Evaluate structure confluence
    • Evaluate momentum
    • Evaluate RSI condition
    • Evaluate pullback/reclaim quality
    • Evaluate active OB/FVG context
    • Evaluate premium/discount context
    • Evaluate volatility context
    • Produce a quality score
    • Approve/reject candidates for Phase 7

PHASE 6 MUST NOT:
    • construct Entry
    • construct SL
    • construct TP1 / TP2
    • calculate Risk
    • calculate Reward
    • calculate R:R
    • calculate Position Size
    • submit orders
    • transmit orders
    • withdraw funds
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# CORE
# ============================================================

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_6"
VERSION = "6.1-QUALITY"

REFRESH_SECONDS = 60

MIN_PHASE5_CONFIDENCE = 75.0
MIN_QUALITY_SCORE = 70.0

ROOT = Path(__file__).resolve().parent

STATE_DIR = ROOT / "state"
REPORT_DIR = ROOT / "reports"

PHASE5_STATE = STATE_DIR / "phase5_market_intelligence.json"
STATE_FILE = STATE_DIR / "phase6_trade_quality.json"
REPORT_FILE = REPORT_DIR / "phase6_trade_quality_report.json"

STATE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# TIME / I/O
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    temp = path.with_suffix(path.suffix + ".tmp")

    with temp.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    temp.replace(path)


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# PHASE 5 CONTRACT
# ============================================================

def load_phase5():
    state = load_json(PHASE5_STATE)

    if not isinstance(state, dict):
        raise RuntimeError(
            "Phase 5 state file missing or invalid."
        )

    return state


def get_phase5_candidates(state):
    """
    Verified Phase 5 contract:
        state["qualified"] -> list of qualified intelligence records
    """

    status = state.get("scan_status")

    if status is not None and status != "COMPLETE":
        raise RuntimeError(
            f"Phase 5 scan is not complete: {status}"
        )

    coverage = number(
        state.get("coverage"),
        100.0,
    )

    if coverage < 100.0:
        raise RuntimeError(
            f"Phase 5 coverage incomplete: {coverage:.2f}%"
        )

    errors = state.get("errors", [])

    if not isinstance(errors, list):
        raise RuntimeError(
            "Phase 5 error collection is invalid."
        )

    # A complete scan with errors must not silently pass as
    # complete-quality input.
    if errors:
        raise RuntimeError(
            f"Phase 5 contains {len(errors)} errors."
        )

    candidates = state.get("qualified", [])

    if not isinstance(candidates, list):
        raise RuntimeError(
            "Phase 5 qualified candidate list is invalid."
        )

    return [
        item
        for item in candidates
        if isinstance(item, dict)
    ]


# ============================================================
# QUALITY HELPERS
# ============================================================

def direction_alignment(item):
    direction = item.get(
        "market_bias",
        {},
    ).get(
        "direction",
        "NEUTRAL",
    )

    h1 = item.get(
        "market_bias",
        {},
    ).get(
        "h1",
        "NEUTRAL",
    )

    m15 = item.get(
        "market_bias",
        {},
    ).get(
        "m15",
        "NEUTRAL",
    )

    m5 = item.get(
        "market_bias",
        {},
    ).get(
        "m5",
        "NEUTRAL",
    )

    expected = (
        "BULL"
        if direction == "LONG"
        else "BEAR"
        if direction == "SHORT"
        else "NEUTRAL"
    )

    aligned = sum(
        x == expected
        for x in (h1, m15, m5)
    )

    return {
        "direction": direction,
        "h1": h1,
        "m15": m15,
        "m5": m5,
        "aligned_timeframes": aligned,
        "score": (aligned / 3.0) * 20.0,
    }


def structure_quality(item, expected):
    structure = item.get(
        "structure",
        {},
    )

    internal = structure.get(
        "internal",
        {},
    )

    swing = structure.get(
        "swing",
        {},
    )

    internal_bias = internal.get(
        "bias",
        "NEUTRAL",
    )

    swing_bias = swing.get(
        "bias",
        "NEUTRAL",
    )

    confluence = structure.get(
        "confluence",
        {},
    )

    score = 0.0
    reasons = []

    if internal_bias == expected:
        score += 10.0
        reasons.append("INTERNAL_STRUCTURE_ALIGNED")

    if swing_bias == expected:
        score += 15.0
        reasons.append("SWING_STRUCTURE_ALIGNED")

    if (
        internal_bias == expected
        and swing_bias == expected
    ):
        score += 10.0
        reasons.append("STRUCTURE_CONFLUENCE")

    if confluence.get("qualified"):
        score += 5.0
        reasons.append("CONFLUENCE_QUALIFIED")

    return {
        "score": min(score, 40.0),
        "internal_bias": internal_bias,
        "swing_bias": swing_bias,
        "confluence_qualified": bool(
            confluence.get("qualified")
        ),
        "reasons": reasons,
    }


def momentum_quality(item, expected):
    momentum = number(
        item.get("momentum"),
        0.0,
    )

    score = 0.0

    if expected == "BULL":
        if momentum > 0:
            score = min(
                10.0,
                momentum * 10.0,
            )
    elif expected == "BEAR":
        if momentum < 0:
            score = min(
                10.0,
                abs(momentum) * 10.0,
            )

    return {
        "momentum": momentum,
        "score": round(score, 2),
    }


def rsi_quality(item, direction):
    rsi_data = item.get(
        "rsi",
        {},
    )

    value = rsi_data.get("5m")

    if value is None:
        return {
            "rsi": None,
            "score": 0.0,
            "status": "UNKNOWN",
        }

    value = number(value)

    # Phase 6 evaluates RSI quality only.
    # It does not create an entry condition.
    if direction == "LONG":
        if value >= 75:
            return {
                "rsi": value,
                "score": 0.0,
                "status": "OVERBOUGHT_RISK",
            }

        if 45 <= value < 70:
            return {
                "rsi": value,
                "score": 5.0,
                "status": "HEALTHY_LONG_ZONE",
            }

    if direction == "SHORT":
        if value <= 25:
            return {
                "rsi": value,
                "score": 0.0,
                "status": "OVERSOLD_RISK",
            }

        if 30 < value <= 55:
            return {
                "rsi": value,
                "score": 5.0,
                "status": "HEALTHY_SHORT_ZONE",
            }

    return {
        "rsi": value,
        "score": 2.0,
        "status": "NEUTRAL",
    }


def pullback_quality(item, expected):
    data = item.get(
        "pullback_reclaim",
        {},
    )

    pullback = bool(
        data.get("pullback")
    )

    reclaim = bool(
        data.get("reclaim")
    )

    score = 0.0

    if pullback:
        score += 5.0

    if reclaim:
        score += 5.0

    return {
        "pullback": pullback,
        "reclaim": reclaim,
        "score": score,
    }


def liquidity_context_quality(item):
    """
    Phase 5 does not expose a standalone numeric liquidity
    score in every record. Therefore this phase only uses
    active structural liquidity/context when present.
    """

    equal_levels = item.get(
        "equal_levels",
        {},
    )

    eq_highs = equal_levels.get(
        "equal_highs",
        [],
    )

    eq_lows = equal_levels.get(
        "equal_lows",
        [],
    )

    score = 0.0

    if eq_highs or eq_lows:
        score += 5.0

    return {
        "equal_highs": len(eq_highs),
        "equal_lows": len(eq_lows),
        "score": score,
    }


def zone_quality(item, direction):
    pd = item.get(
        "premium_discount",
        {},
    )

    zone = pd.get(
        "zone",
        "UNKNOWN",
    )

    score = 0.0

    if direction == "LONG":
        if zone == "DISCOUNT":
            score = 5.0
        elif zone == "EQUILIBRIUM":
            score = 2.0

    elif direction == "SHORT":
        if zone == "PREMIUM":
            score = 5.0
        elif zone == "EQUILIBRIUM":
            score = 2.0

    return {
        "zone": zone,
        "score": score,
    }


def volatility_quality(item):
    volatility = item.get(
        "volatility",
        {},
    )

    ratio = volatility.get(
        "atr_ratio"
    )

    if ratio is None:
        return {
            "atr_ratio": None,
            "score": 0.0,
            "status": "UNKNOWN",
        }

    ratio = number(ratio)

    if 0.5 <= ratio <= 2.5:
        score = 5.0
        status = "HEALTHY"
    elif ratio > 2.5:
        score = 1.0
        status = "EXTENDED"
    else:
        score = 2.0
        status = "LOW_VOLATILITY"

    return {
        "atr_ratio": ratio,
        "score": score,
        "status": status,
    }


# ============================================================
# CANDIDATE EVALUATION
# ============================================================

def evaluate_candidate(item):
    symbol = item.get(
        "symbol",
        "UNKNOWN",
    )

    intelligence = item.get(
        "intelligence",
        {},
    )

    confidence = number(
        intelligence.get("confidence"),
        0.0,
    )

    direction = item.get(
        "market_bias",
        {},
    ).get(
        "direction",
        "NEUTRAL",
    )

    if direction not in ("LONG", "SHORT"):
        return {
            "symbol": symbol,
            "phase6_decision": "REJECTED",
            "quality_score": 0.0,
            "phase6_reasons": [
                "INVALID_DIRECTION"
            ],
        }

    expected = (
        "BULL"
        if direction == "LONG"
        else "BEAR"
    )

    alignment = direction_alignment(item)

    structure = structure_quality(
        item,
        expected,
    )

    momentum = momentum_quality(
        item,
        expected,
    )

    rsi_data = rsi_quality(
        item,
        direction,
    )

    pullback = pullback_quality(
        item,
        expected,
    )

    liquidity = liquidity_context_quality(
        item
    )

    zone = zone_quality(
        item,
        direction,
    )

    volatility = volatility_quality(
        item
    )

    # Phase 5 confidence is carried forward but not
    # double-counted as a complete trade signal.
    confidence_component = min(
        max(
            (confidence - MIN_PHASE5_CONFIDENCE)
            / 25.0,
            0.0,
        ),
        1.0,
    ) * 10.0

    quality_score = (
        alignment["score"]
        + structure["score"]
        + momentum["score"]
        + rsi_data["score"]
        + pullback["score"]
        + liquidity["score"]
        + zone["score"]
        + volatility["score"]
        + confidence_component
    )

    quality_score = min(
        100.0,
        max(
            0.0,
            quality_score,
        ),
    )

    reasons = []

    if alignment["aligned_timeframes"] == 3:
        reasons.append("FULL_MTF_ALIGNMENT")
    elif alignment["aligned_timeframes"] == 2:
        reasons.append("PARTIAL_MTF_ALIGNMENT")

    reasons.extend(
        structure["reasons"]
    )

    if momentum["score"] > 0:
        reasons.append("DIRECTIONAL_MOMENTUM")

    if pullback["pullback"]:
        reasons.append("PULLBACK_PRESENT")

    if pullback["reclaim"]:
        reasons.append("RECLAIM_PRESENT")

    if zone["zone"] in (
        "PREMIUM",
        "DISCOUNT",
        "EQUILIBRIUM",
    ):
        reasons.append(
            f"ZONE_{zone['zone']}"
        )

    if rsi_data["status"] in (
        "OVERBOUGHT_RISK",
        "OVERSOLD_RISK",
    ):
        reasons.append(
            rsi_data["status"]
        )

    approved = (
        confidence >= MIN_PHASE5_CONFIDENCE
        and quality_score >= MIN_QUALITY_SCORE
        and alignment["aligned_timeframes"] >= 2
        and structure["confluence_qualified"]
    )

    if not approved:
        if confidence < MIN_PHASE5_CONFIDENCE:
            reasons.append("LOW_PHASE5_CONFIDENCE")

        if quality_score < MIN_QUALITY_SCORE:
            reasons.append("QUALITY_SCORE_BELOW_THRESHOLD")

        if alignment["aligned_timeframes"] < 2:
            reasons.append("INSUFFICIENT_MTF_ALIGNMENT")

        if not structure["confluence_qualified"]:
            reasons.append("STRUCTURE_CONFLUENCE_FAILED")

    result = dict(item)

    result["phase6_decision"] = (
        "APPROVED"
        if approved
        else "REJECTED"
    )

    result["phase6_quality"] = {
        "score": round(
            quality_score,
            2,
        ),
        "minimum_score": MIN_QUALITY_SCORE,
        "phase5_confidence": round(
            confidence,
            2,
        ),
        "components": {
            "mtf_alignment": alignment,
            "structure": structure,
            "momentum": momentum,
            "rsi": rsi_data,
            "pullback_reclaim": pullback,
            "liquidity_context": liquidity,
            "premium_discount": zone,
            "volatility": volatility,
            "confidence_component": round(
                confidence_component,
                2,
            ),
        },
    }

    result["phase6_reasons"] = reasons

    # HARD REMOVE TRADE-CONSTRUCTION FIELDS.
    forbidden = (
        "entry",
        "sl",
        "tp1",
        "tp2",
        "risk",
        "reward",
        "rr",
        "position_size",
        "phase6_rr",
    )

    for key in forbidden:
        result.pop(key, None)

    return result


# ============================================================
# SCAN
# ============================================================

def scan():
    phase5 = load_phase5()

    candidates = get_phase5_candidates(
        phase5
    )

    approved = []
    rejected = []

    print(
        f"PHASE 6 STARTING — "
        f"{len(candidates)} PHASE 5 QUALIFIED CANDIDATES",
        flush=True,
    )

    for index, item in enumerate(
        candidates,
        start=1,
    ):
        symbol = item.get(
            "symbol",
            "UNKNOWN",
        )

        print(
            f"PHASE 6 QUALITY "
            f"{index}/{len(candidates)} "
            f"{symbol}",
            flush=True,
        )

        try:
            result = evaluate_candidate(
                item
            )

            if (
                result["phase6_decision"]
                == "APPROVED"
            ):
                approved.append(result)
            else:
                rejected.append(result)

        except Exception as exc:
            rejected.append(
                {
                    "symbol": symbol,
                    "phase6_decision": "REJECTED",
                    "quality_score": 0.0,
                    "phase6_reasons": [
                        f"PHASE6_ERROR:{exc}"
                    ],
                }
            )

    approved.sort(
        key=lambda x: number(
            x.get(
                "phase6_quality",
                {},
            ).get(
                "score",
                0.0,
            )
        ),
        reverse=True,
    )

    rejected.sort(
        key=lambda x: number(
            x.get(
                "phase6_quality",
                {},
            ).get(
                "score",
                0.0,
            )
        ),
        reverse=True,
    )

    longs = [
        x
        for x in approved
        if x.get(
            "market_bias",
            {},
        ).get(
            "direction"
        ) == "LONG"
    ]

    shorts = [
        x
        for x in approved
        if x.get(
            "market_bias",
            {},
        ).get(
            "direction"
        ) == "SHORT"
    ]

    return {
        "phase5_candidates": len(candidates),
        "approved_candidates": len(approved),
        "rejected_candidates": len(rejected),
        "long_candidates": len(longs),
        "short_candidates": len(shorts),
        "approved": approved,
        "rejected": rejected,
    }


# ============================================================
# STATE
# ============================================================

def build_state(
    result,
    phase5,
    cycle,
    status="COMPLETE",
):
    return {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "cycle": cycle,
        "status": status,

        "source": {
            "phase": 5,
            "phase_name": "MARKET_INTELLIGENCE",
            "timestamp_utc": phase5.get(
                "timestamp_utc"
            ),
            "markets_received": phase5.get(
                "markets_received",
                0,
            ),
            "markets_analyzed": phase5.get(
                "markets_analyzed",
                0,
            ),
            "coverage": phase5.get(
                "coverage",
                0.0,
            ),
            "scan_status": phase5.get(
                "scan_status",
                "UNKNOWN",
            ),
            "errors": len(
                phase5.get(
                    "errors",
                    [],
                )
            ),
        },

        "quality": {
            "phase5_candidates":
                result["phase5_candidates"],
            "approved_candidates":
                result["approved_candidates"],
            "rejected_candidates":
                result["rejected_candidates"],
            "long_candidates":
                result["long_candidates"],
            "short_candidates":
                result["short_candidates"],
            "minimum_quality_score":
                MIN_QUALITY_SCORE,
            "approved":
                result["approved"],
            "rejected":
                result["rejected"],
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
            "transmission": "LOCKED",
        },

        "forbidden_in_phase6": [
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
    }


# ============================================================
# DISPLAY
# ============================================================

def display(result, cycle):
    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — PHASE 6 TRADE QUALITY"
    )
    print("=" * 78)

    print(
        f"Cycle                    : {cycle}"
    )

    print(
        f"UTC                      : {now_utc()}"
    )

    print(
        f"Phase 5 candidates       : "
        f"{result['phase5_candidates']}"
    )

    print(
        f"Approved                 : "
        f"{result['approved_candidates']}"
    )

    print(
        f"Rejected                 : "
        f"{result['rejected_candidates']}"
    )

    print(
        f"Approved LONG            : "
        f"{result['long_candidates']}"
    )

    print(
        f"Approved SHORT           : "
        f"{result['short_candidates']}"
    )

    print()
    print(
        "APPROVED TRADE-QUALITY CANDIDATES"
    )
    print("-" * 78)

    if not result["approved"]:
        print("None")

    for rank, item in enumerate(
        result["approved"],
        start=1,
    ):
        quality = item.get(
            "phase6_quality",
            {},
        )

        print(
            f"{rank:>2}. "
            f"{item.get('symbol', 'UNKNOWN'):<16} "
            f"{item.get('market_bias', {}).get('direction', ''):<6} "
            f"QUALITY:{number(quality.get('score')):>6.2f} "
            f"CONF:{number(quality.get('phase5_confidence')):>6.2f}"
        )

    print()
    print(
        "TRADE CONSTRUCTION"
    )
    print(
        "Entry / SL / TP / Risk / Reward / R:R / Position Size"
    )
    print(
        "ALL UNCONSTRUCTED — OWNED BY DOWNSTREAM PHASES"
    )

    print()
    print("=" * 78)
    print(
        "PHASE 6 QUALITY DECISION COMPLETE"
    )
    print("=" * 78)

    print(
        "EXECUTION_AUTHORIZED : FALSE"
    )
    print(
        "LIVE_EXECUTION       : FALSE"
    )
    print(
        "BOT_ARMED            : FALSE"
    )
    print(
        "ORDER_SUBMISSION     : FALSE"
    )
    print(
        "WITHDRAWALS          : FALSE"
    )
    print(
        "TRANSMISSION         : LOCKED"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    once = "--once" in sys.argv
    cycle = 0

    while True:
        cycle += 1

        try:
            phase5 = load_phase5()
            result = scan()

            state = build_state(
                result,
                phase5,
                cycle,
                "COMPLETE",
            )

            save_json(
                STATE_FILE,
                state,
            )

            save_json(
                REPORT_FILE,
                state,
            )

            display(
                result,
                cycle,
            )

        except KeyboardInterrupt:
            existing = load_json(
                STATE_FILE
            ) or {}

            if "quality" in existing:
                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                save_json(
                    STATE_FILE,
                    existing,
                )

            print(
                "\nPHASE 6 STOPPED."
            )
            break

        except Exception as exc:
            print(
                f"\nPHASE 6 ERROR: {exc}",
                flush=True,
            )

            error_state = {
                "project": PROJECT,
                "phase": PHASE,
                "version": VERSION,
                "timestamp_utc": now_utc(),
                "cycle": cycle,
                "status": "ERROR",
                "error": str(exc),

                "execution_boundary": {
                    "execution_authorized": False,
                    "order_submission": False,
                    "bot_armed": False,
                    "live_execution": False,
                    "withdrawals": False,
                    "transmission": "LOCKED",
                },
            }

            save_json(
                STATE_FILE,
                error_state,
            )

            if once:
                break

            time.sleep(
                REFRESH_SECONDS
            )
            continue

        if once:
            print(
                "\nONCE MODE - EXIT"
            )
            break

        print()
        print(
            f"Next Phase 6 scan in "
            f"{REFRESH_SECONDS} seconds...",
            flush=True,
        )

        try:
            time.sleep(
                REFRESH_SECONDS
            )
        except KeyboardInterrupt:
            existing = load_json(
                STATE_FILE
            ) or {}

            if "quality" in existing:
                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                save_json(
                    STATE_FILE,
                    existing,
                )

            print(
                "\nPHASE 6 STOPPED."
            )
            break


if __name__ == "__main__":
    main()
