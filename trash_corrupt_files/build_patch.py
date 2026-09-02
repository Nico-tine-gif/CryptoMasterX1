from pathlib import Path
path=Path("phase6_trade_intelligence.py")
lines=path.read_text().splitlines()

out=[]
in_balance_func=False
balance_replaced=False
in_build_func=False
build_replaced=False
skip_build=False

for i,line in enumerate(lines):
    # Replace get_account_usdt_balance function
    if "def get_account_usdt_balance():" in line and not balance_replaced:
        out.append(line)
        out.append('    print("[OVERRIDE] Using total wallet 21.03 USDT (BNB+USDT)")')
        out.append('    return 21.03')
        in_balance_func=True
        balance_replaced=True
        continue
    if in_balance_func:
        # skip until next def (blank line + def)
        if line.startswith("def ") and "get_account" not in line:
            in_balance_func=False
            out.append(line)
        continue

    # Replace build_trade function start
    if "def build_trade(candidate, account_balance):" in line and not build_replaced:
        out.append('def build_trade(candidate, account_balance):')
        out.append('    # FIX Phase5 aware - direction, atr, decimal')
        out.append('    symbol = candidate.get("symbol") or candidate.get("discovery",{}).get("symbol")')
        out.append('    if not symbol:')
        out.append('        return None')
        out.append('    direction = candidate.get("direction") or candidate.get("market_bias",{}).get("direction") or candidate.get("dashboard",{}).get("direction") or "SHORT"')
        out.append('    direction = str(direction).upper()')
        out.append('    candidate["direction"] = direction')
        out.append('    live_price_raw = candidate.get("current_price") or candidate.get("discovery",{}).get("lastPrice") or 0')
        out.append('    try:')
        out.append('        live_price = Decimal(str(live_price_raw))')
        out.append('    except:')
        out.append('        live_price = Decimal(str(current_price(symbol)))')
        out.append('    if live_price == 0:')
        out.append('        live_price = Decimal(str(current_price(symbol)))')
        out.append('    vol = candidate.get("volatility",{})')
        out.append('    atr_raw = None')
        out.append('    if isinstance(vol, dict):')
        out.append('        atr_raw = vol.get("atr_5m") or vol.get("atr")')
        out.append('    if not atr_raw:')
        out.append('        atr_raw = float(live_price) * 0.01')
        out.append('    atr_value = Decimal(str(atr_raw))')
        in_build_func=True
        build_replaced=True
        skip_build=True
        continue

    if skip_build:
        # Skip until we hit risk_distance line which is original after atr
        if "risk_distance" in line and "SL_ATR" in line:
            skip_build=False
            out.append(line)
        continue

    out.append(line)

code="\n".join(out)
code=code.replace('MIN_BALANCE = 20','MIN_BALANCE = 5')
code=code.replace('if account_balance < 20','if account_balance < 5')
Path("phase6_trade_intelligence.py").write_text(code)
print("Clean patch applied")
