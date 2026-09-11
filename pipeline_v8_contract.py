#!/usr/bin/env python3
"""
CryptoMasterX1 — Consolidated 8-Phase Pipeline Contract

IMPORTANT:
- Does NOT delete or modify existing phase files.
- Existing legacy phases remain available.
- This file defines the authoritative responsibilities and data flow.
- A candidate must move forward explicitly.
- No silent skipping.
- No phase may manufacture missing upstream information.
- Fresh market data is required before executable trade construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


PIPELINE_VERSION = "8-PHASE-CONSOLIDATED-V1"


# ============================================================
# GLOBAL SAFETY CONTRACT
# ============================================================

SAFETY = {
    "LIVE_EXECUTION": False,
    "BOT_ARMED": False,
    "ORDER_SUBMISSION": False,
    "WITHDRAWALS": False,
    "TRANSMISSION_LOCKED": True,
    "EXECUTION_AUTHORIZED": False,
}


# ============================================================
# PHASE DEFINITIONS
# ============================================================

PHASES = {

    1: {
        "name": "Machine Core",
        "responsibility": [
            "runtime health",
            "filesystem availability",
            "configuration integrity",
            "environment integrity",
            "pipeline startup",
        ],
        "must_not_do": [
            "market analysis",
            "trade construction",
            "order submission",
        ],
    },

    2: {
        "name": "Account Binding/Security",
        "responsibility": [
            "account identity",
            "API credential binding",
            "security restrictions",
            "withdrawal prohibition",
            "execution security state",
        ],
        "must_not_do": [
            "market selection",
            "trade analysis",
            "trade construction",
        ],
    },

    3: {
        "name": "Account Verification",
        "responsibility": [
            "verify Binance account",
            "verify account permissions",
            "verify connectivity",
            "verify usable trading state",
            "confirm security restrictions remain active",
        ],
        "must_not_do": [
            "select trades",
            "calculate trade levels",
            "submit orders",
        ],
    },

    4: {
        "name": "Market Discovery/Safety",
        "responsibility": [
            "discover tradable markets",
            "remove invalid markets",
            "liquidity filtering",
            "market-status filtering",
            "symbol eligibility",
        ],
        "must_not_do": [
            "final trade construction",
            "order submission",
        ],
    },

    5: {
        "name": "Market Intelligence",
        "responsibility": [
            "fresh market data",
            "multi-timeframe analysis",
            "trend/regime",
            "structure",
            "momentum",
            "pullback/reclaim",
            "RSI",
            "ATR/volatility",
            "support/resistance",
            "liquidity context",
            "market direction",
            "setup evidence",
        ],
        "must_not_do": [
            "submit orders",
            "pretend a trade is executable",
        ],
    },

    6: {
        "name": "Trade Intelligence + Fresh Construction",
        "responsibility": [
            "digest ALL Phase 5 intelligence",
            "determine whether the setup is coherent",
            "reject conflicting evidence",
            "refresh live market data",
            "verify direction against fresh data",
            "prevent stale-entry execution",
            "construct Entry",
            "construct SL",
            "construct TP1",
            "construct TP2",
            "calculate actual R:R",
            "calculate position size",
            "produce complete executable candidate",
        ],
        "must_not_do": [
            "ignore Phase 5 intelligence",
            "use stale Phase 5/6 prices as current price",
            "submit orders",
        ],
    },

    7: {
        "name": "Final Validation + Decision",
        "responsibility": [
            "validate complete Phase 6 candidate",
            "validate entry",
            "validate stop loss",
            "validate take profits",
            "validate R:R",
            "validate position size",
            "validate freshness",
            "validate direction",
            "validate risk limits",
            "final PASS or REJECT",
        ],
        "must_not_do": [
            "invent missing trade levels",
            "silently repair invalid trades",
            "submit orders",
        ],
    },

    8: {
        "name": "Execution + Lifecycle",
        "responsibility": [
            "receive only Phase 7 approved trades",
            "verify execution authorization",
            "submit orders only when globally authorized",
            "track order state",
            "manage open positions",
            "manage SL/TP lifecycle",
            "record fills",
            "record exits",
            "handle execution failures",
        ],
        "must_not_do": [
            "perform independent market analysis",
            "override Phase 7 risk decisions",
            "enable withdrawals",
            "bypass execution locks",
        ],
    },
}


# ============================================================
# CANDIDATE DATA CONTRACT
# ============================================================

@dataclass
class TradeCandidate:

    # Identity
    symbol: str
    direction: Optional[str] = None

    # Phase 4
    market_eligible: bool = False
    liquidity_ok: bool = False

    # Phase 5 intelligence
    intelligence: Dict[str, Any] = field(default_factory=dict)

    # Phase 6 fresh market state
    fresh_market: Dict[str, Any] = field(default_factory=dict)

    # Executable levels
    entry: Optional[float] = None
    sl: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None

    # Risk
    risk_distance: Optional[float] = None
    reward_distance: Optional[float] = None
    rr: Optional[float] = None
    position_size: Optional[float] = None

    # Quality
    confidence: Optional[float] = None
    quality_score: Optional[float] = None

    # Pipeline state
    phase: int = 4
    status: str = "DISCOVERED"

    # Integrity
    fresh_data_required: bool = True
    fresh_data_verified: bool = False
    validation_passed: bool = False

    # Audit
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, phase: int, status: str, note: str = ""):
        self.phase = phase
        self.status = status

        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "phase_name": PHASES[phase]["name"],
            "status": status,
            "note": note,
        })


# ============================================================
# CONTRACT VALIDATORS
# ============================================================

def require(condition: bool, message: str):
    """
    Hard contract failure.

    We deliberately DO NOT silently continue when required data
    is missing. Silent continuation is one of the main causes
    of unwanted pipeline behaviour.
    """
    if not condition:
        raise RuntimeError(f"PIPELINE CONTRACT FAILURE: {message}")


def validate_phase4(candidate: TradeCandidate):

    require(
        candidate.market_eligible,
        f"{candidate.symbol}: market is not eligible"
    )

    require(
        candidate.liquidity_ok,
        f"{candidate.symbol}: liquidity requirement failed"
    )


def validate_phase5(candidate: TradeCandidate):

    require(
        candidate.intelligence,
        f"{candidate.symbol}: Phase 5 produced no intelligence"
    )

    require(
        candidate.direction in ("LONG", "SHORT"),
        f"{candidate.symbol}: Phase 5 did not establish valid direction"
    )


def validate_phase6(candidate: TradeCandidate):

    require(
        candidate.fresh_market,
        f"{candidate.symbol}: fresh market data missing"
    )

    require(
        candidate.fresh_data_verified,
        f"{candidate.symbol}: fresh market data not verified"
    )

    require(
        candidate.entry is not None,
        f"{candidate.symbol}: Entry missing"
    )

    require(
        candidate.sl is not None,
        f"{candidate.symbol}: SL missing"
    )

    require(
        candidate.tp1 is not None,
        f"{candidate.symbol}: TP1 missing"
    )

    require(
        candidate.tp2 is not None,
        f"{candidate.symbol}: TP2 missing"
    )

    require(
        candidate.rr is not None and candidate.rr > 0,
        f"{candidate.symbol}: invalid R:R"
    )

    require(
        candidate.position_size is not None
        and candidate.position_size > 0,
        f"{candidate.symbol}: invalid position size"
    )


def validate_phase7(candidate: TradeCandidate):

    validate_phase6(candidate)

    require(
        candidate.direction in ("LONG", "SHORT"),
        f"{candidate.symbol}: invalid direction"
    )

    entry = candidate.entry
    sl = candidate.sl
    tp1 = candidate.tp1
    tp2 = candidate.tp2

    if candidate.direction == "LONG":
        require(sl < entry, f"{candidate.symbol}: LONG SL must be below Entry")
        require(tp1 > entry, f"{candidate.symbol}: LONG TP1 must be above Entry")
        require(tp2 > tp1, f"{candidate.symbol}: LONG TP2 must exceed TP1")

    elif candidate.direction == "SHORT":
        require(sl > entry, f"{candidate.symbol}: SHORT SL must be above Entry")
        require(tp1 < entry, f"{candidate.symbol}: SHORT TP1 must be below Entry")
        require(tp2 < tp1, f"{candidate.symbol}: SHORT TP2 must exceed TP1 in direction")

    risk = abs(entry - sl)
    reward = abs(tp2 - entry)

    require(risk > 0, f"{candidate.symbol}: zero risk distance")

    calculated_rr = reward / risk

    # Prevent a phase from reporting a fake R:R.
    require(
        abs(calculated_rr - candidate.rr) < 1e-9,
        f"{candidate.symbol}: reported R:R does not match actual levels"
    )


def validate_phase8(candidate: TradeCandidate):

    require(
        candidate.validation_passed,
        f"{candidate.symbol}: final validation not passed"
    )

    # GLOBAL EXECUTION SAFETY
    if not (
        SAFETY["LIVE_EXECUTION"]
        and SAFETY["BOT_ARMED"]
        and SAFETY["ORDER_SUBMISSION"]
        and SAFETY["EXECUTION_AUTHORIZED"]
        and SAFETY["TRANSMISSION_LOCKED"] is False
    ):
        # This is intentional.
        # The consolidated architecture can prepare a trade without
        # accidentally transmitting it.
        return False

    return True


# ============================================================
# PHASE TRANSITIONS
# ============================================================

def phase4(candidate: TradeCandidate):
    validate_phase4(candidate)
    candidate.record(
        4,
        "DISCOVERED",
        "Market passed discovery and safety eligibility."
    )
    return candidate


def phase5(candidate: TradeCandidate):
    """
    Phase 5 MUST produce intelligence.

    It does not merely pass a symbol forward.
    """
    validate_phase5(candidate)

    candidate.record(
        5,
        "INTELLIGENCE_COMPLETE",
        "All available market intelligence digested."
    )

    return candidate


def phase6(candidate: TradeCandidate):
    """
    CONSOLIDATED PHASE 6.

    This is where Phase 5 intelligence and fresh market data
    become one complete trade candidate.

    Existing Phase 5/6/7 scripts are NOT deleted.
    This contract simply defines the correct responsibility.
    """

    validate_phase5(candidate)

    # Fresh market data must be supplied by the implementation
    # before this phase is considered complete.
    require(
        candidate.fresh_market,
        f"{candidate.symbol}: fresh market refresh required"
    )

    candidate.fresh_data_verified = True

    # At this point the implementation must construct:
    #
    # entry
    # sl
    # tp1
    # tp2
    # rr
    # position_size
    #
    # We intentionally do not invent these values here.

    validate_phase6(candidate)

    candidate.record(
        6,
        "TRADE_CONSTRUCTED",
        "Phase 5 intelligence + fresh market data converted into "
        "complete trade candidate."
    )

    return candidate


def phase7(candidate: TradeCandidate):
    """
    Final independent safety gate.
    """

    validate_phase7(candidate)

    candidate.validation_passed = True

    candidate.record(
        7,
        "APPROVED",
        "Final validation passed."
    )

    return candidate


def phase8(candidate: TradeCandidate):
    """
    Execution + lifecycle.

    This phase can prepare execution without transmitting.
    """

    executable = validate_phase8(candidate)

    if not executable:
        candidate.record(
            8,
            "EXECUTION_LOCKED",
            "Trade is valid, but global execution authorization remains locked."
        )
        return candidate

    candidate.record(
        8,
        "EXECUTION_AUTHORIZED",
        "Trade passed execution authorization."
    )

    return candidate


# ============================================================
# PIPELINE AUDIT
# ============================================================

def print_contract():

    print()
    print("=" * 78)
    print("CRYPTOMASTERX1 — CONSOLIDATED 8-PHASE ARCHITECTURE")
    print("=" * 78)

    for number, phase in PHASES.items():

        print()
        print(f"PHASE {number} — {phase['name']}")
        print("-" * 78)

        for item in phase["responsibility"]:
            print(f"  + {item}")

        print("  FORBIDDEN:")
        for item in phase["must_not_do"]:
            print(f"  - {item}")

    print()
    print("=" * 78)
    print("GLOBAL EXECUTION STATE")
    print("=" * 78)

    for key, value in SAFETY.items():
        print(f"{key:24} = {value}")

    print()
    print("=" * 78)
    print("PIPELINE FLOW")
    print("=" * 78)

    print(
        "1 CORE"
        " -> 2 ACCOUNT SECURITY"
        " -> 3 ACCOUNT VERIFY"
        " -> 4 MARKET DISCOVERY"
        " -> 5 MARKET INTELLIGENCE"
        " -> 6 TRADE INTELLIGENCE + FRESH CONSTRUCTION"
        " -> 7 FINAL VALIDATION"
        " -> 8 EXECUTION + LIFECYCLE"
    )

    print()
    print("LEGACY FILES: PRESERVED")
    print("PIPELINE CONTRACT: CONSOLIDATED")
    print("SILENT PHASE SKIPPING: FORBIDDEN")
    print("STALE TRADE DATA: FORBIDDEN")
    print("WITHDRAWALS: FORBIDDEN")
    print("=" * 78)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print_contract()
