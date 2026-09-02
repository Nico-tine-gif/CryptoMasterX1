from pathlib import Path
p=Path("phase6_trade_intelligence.py").read_text()
# Make live_price Decimal too
p=p.replace(
    "    live_price = candidate.get(\"current_price\") or candidate.get(\"discovery\",{}).get(\"lastPrice\") or 0",
    "    live_price_raw = candidate.get(\"current_price\") or candidate.get(\"discovery\",{}).get(\"lastPrice\") or 0\n    live_price = Decimal(str(live_price_raw)) if live_price_raw else Decimal(str(current_price(symbol)))"
)
# Also ensure entry/sl are Decimal - they already are if live_price is Decimal
# Fix current_price fallback
p=p.replace(
    "    if live_price == 0:",
    "    if live_price == 0:\n        live_price = Decimal(str(current_price(symbol)))"
)
# Remove duplicate check if present
Path("phase6_trade_intelligence.py").write_text(p)
print("Decimal fix applied")
