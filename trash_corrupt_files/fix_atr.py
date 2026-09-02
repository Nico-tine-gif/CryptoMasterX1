from pathlib import Path
p=Path("phase6_trade_intelligence.py").read_text()

# Patch atr retrieval to fallback
old_atr = ' atr_value = Decimal(\n str(candidate["atr_5m"])\n )'
new_atr = ''' # --- FIX atr_5m fallback ---
    atr_raw = candidate.get("atr_5m") or candidate.get("atr") or candidate.get("atr_14") or candidate.get("volatility") or 0.01
    if atr_raw == 0 or atr_raw == 0.01:
        # use 1% of price as fallback
        atr_raw = float(candidate.get("price",0) or candidate.get("current_price",0) or 1) * 0.01
        if atr_raw == 0:
            atr_raw = 0.01
    atr_value = Decimal(str(atr_raw))
    # --- END FIX ---
'''

if "FIX atr_5m fallback" not in p:
    p=p.replace(old_atr, new_atr)
    Path("phase6_trade_intelligence.py").write_text(p)
    print("atr fix applied")
else:
    print("atr already fixed")

