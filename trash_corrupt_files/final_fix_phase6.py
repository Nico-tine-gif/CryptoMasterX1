from pathlib import Path
path=Path("phase6_trade_intelligence.py")
code=path.read_text()

# Replace entire build_trade function with Phase5-aware version
new_func = '''
def build_trade(candidate, account_balance):
    # --- FIX: Phase5 structure aware ---
    symbol = candidate.get("symbol") or candidate.get("discovery",{}).get("symbol")
    if not symbol:
        return None

    # Direction from multiple possible places
    direction = candidate.get("direction")
    if not direction:
        direction = candidate.get("market_bias",{}).get("direction")
    if not direction:
        direction = candidate.get("dashboard",{}).get("direction")
    if not direction:
        direction = candidate.get("trade_construction",{}).get("direction")
    if not direction:
        # fallback SHORT as per your Phase5 bias
        direction = "SHORT"

    direction = str(direction).upper()
    candidate["direction"] = direction

    # Price
    live_price = candidate.get("current_price") or candidate.get("discovery",{}).get("lastPrice") or 0
    if live_price == 0:
        live_price = current_price(symbol)

    # ATR - try volatility field
    vol = candidate.get("volatility",{})
    atr_raw = None
    if isinstance(vol, dict):
        atr_raw = vol.get("atr_5m") or vol.get("atr") or vol.get("atr_14") or vol.get("atr_m5")
    if not atr_raw:
        atr_raw = candidate.get("atr_5m") or candidate.get("atr")
    if not atr_raw:
        # 1% fallback
        atr_raw = float(live_price) * 0.01
        if atr_raw == 0:
            atr_raw = 0.01
        print(f"[FIX] Using 1% ATR fallback {atr_raw} for {symbol}")

    atr_value = Decimal(str(atr_raw))
    # --- END FIX ---

    if atr_value <= 0:
        return None

    risk_distance = (
        atr_value * SL_ATR_MULTIPLIER
    )

    if direction == "LONG":
        entry = live_price
        sl = entry - risk_distance
        tp1 = entry + (risk_distance * TP1_R_MULTIPLIER)
        tp2 = entry + (risk_distance * TP2_R_MULTIPLIER)
    elif direction == "SHORT":
        entry = live_price
        sl = entry + risk_distance
        tp1 = entry - (risk_distance * TP1_R_MULTIPLIER)
        tp2 = entry - (risk_distance * TP2_R_MULTIPLIER)
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
'''

# Find and replace from def build_trade to sizing =
import re
pattern = r'def build_trade\(candidate, account_balance\):.*?sizing = calculate_position_size\(\s*symbol,'
code_replaced = re.sub(pattern, new_func, code, flags=re.DOTALL)

Path("phase6_trade_intelligence.py").write_text(code_replaced)
print("build_trade rebuilt for Phase5 structure")
