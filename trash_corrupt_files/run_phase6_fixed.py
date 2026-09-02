# Wrapper to run Phase6 with $21 override without editing file badly
import os
from pathlib import Path

# Load keys
for kf in [Path(".env.keys"), Path.home()/ "CryptoMasterX1"/ ".env.keys"]:
    if kf.exists():
        for line in kf.read_text().splitlines():
            if "=" in line and "BINANCE" in line:
                k,v=line.split("=",1)
                os.environ[k.strip()]=v.strip()
        break

# Monkey-patch balance before import
import phase6_trade_intelligence as p6
orig_main = p6.main

def patched_main():
    # Patch the get_balance function inside to return 21.03
    if hasattr(p6, 'get_account_balance'):
        p6.get_account_balance = lambda: 21.03
    # Also patch any function that reads balance
    # Force attribute
    p6.ACCOUNT_BALANCE = 21.03
    return orig_main()

patched_main()
