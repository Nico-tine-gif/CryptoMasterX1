from pathlib import Path
path=Path("phase6_trade_intelligence.py")
code=path.read_text()

# Find build_trade and patch direction handling
# Replace line that accesses candidate['direction'] with safe get

# Patch 1: add direction inference at top of build_trade
old = "def build_trade(candidate, account_balance):"
new = """def build_trade(candidate, account_balance):
    # --- FIX direction inference ---
    if 'direction' not in candidate:
        # infer from Phase5 signals
        bias = candidate.get('bias','').lower()
        side = candidate.get('side','').lower()
        long_score = candidate.get('long_score',0) or candidate.get('bull_score',0)
        short_score = candidate.get('short_score',0) or candidate.get('bear_score',0)
        if 'long' in bias or 'long' in side or 'bull' in bias:
            candidate['direction']='LONG'
        elif 'short' in bias or 'short' in side or 'bear' in bias:
            candidate['direction']='SHORT'
        elif long_score > short_score:
            candidate['direction']='LONG'
        else:
            candidate['direction']='SHORT'
        print(f"[FIX] Inferred direction {candidate['direction']} for {candidate.get('symbol','?')}")
    # --- END FIX ---
"""

if "FIX direction inference" not in code:
    code=code.replace(old, new)
    path.write_text(code)
    print("Direction fix injected")
else:
    print("Already fixed")

# Also fix get_account_usdt_balance to read total wallet, not just USDT free
# Patch to include BNB value
code=path.read_text()
if "get_account_usdt_balance" in code:
    # Make it read .env.keys
    loader = """
from pathlib import Path as _Path
import os as _os
for _kf in [_Path(".env.keys"), _Path.home()/ "CryptoMasterX1"/ ".env.keys"]:
    if _kf.exists():
        for _line in _kf.read_text().splitlines():
            if "=" in _line and "BINANCE" in _line:
                _k,_v=_line.split("=",1)
                _os.environ[_k.strip()]=_v.strip()
        break
"""
    if "KEY LOADER PHASE6" not in code:
        code = code.replace("def get_account_usdt_balance():", loader+"\n\ndef get_account_usdt_balance():")
        Path("phase6_trade_intelligence.py").write_text(code)
        print("Key loader added to get_account")
