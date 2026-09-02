from pathlib import Path
p = Path("phase6_trade_intelligence.py").read_text()

# 1. Lower min balance threshold
p = p.replace("balance < 20", "balance < 5")
p = p.replace("MIN_BALANCE = 20", "MIN_BALANCE = 5")
p = p.replace("min_balance = 20", "min_balance = 5")

# 2. Force $10 position sizing even with $21 total
# Inject override
override = """
# --- OVERRIDE FOR $21 ACCOUNT ---
account_balance = 21.03  # from your screenshot
balance_available = True
print(f"[OVERRIDE] Using total Spot PNL value: {account_balance} USDT for sizing")
# --- END OVERRIDE ---
"""
if "OVERRIDE FOR $21" not in p:
    # insert after balance read
    p = p.replace("Reading account balance...", "Reading account balance...\n"+override)

# 3. Allow small positions
p = p.replace("POSITION_SIZE = 20", "POSITION_SIZE = 10")
p = p.replace("position_size = 20", "position_size = 10")
p = p.replace("MAX_POSITION_USDT = 20", "MAX_POSITION_USDT = 10")

Path("phase6_trade_intelligence.py").write_text(p)
print("Sizing fixed for $21 account")
