from pathlib import Path
import os
path = Path("phase6_trade_intelligence.py")
text = path.read_text()

# Ensure loader at very top of file
loader = """
from pathlib import Path as _Path
import os as _os
# --- CMX1 KEY LOADER ---
for _kf in [_Path(".env.keys"), _Path.home()/ "CryptoMasterX1"/ ".env.keys"]:
    if _kf.exists():
        for _line in _kf.read_text().splitlines():
            if "=" in _line and "BINANCE" in _line:
                _k,_v=_line.split("=",1)
                _os.environ[_k.strip()]=_v.strip()
                print(f"[KEY LOADER] Loaded {_k.strip()} from {_kf}")
        break
# --- END LOADER ---
"""

if "KEY LOADER" not in text:
    # put after imports
    lines = text.splitlines()
    # find first import
    insert_at = 0
    for i,l in enumerate(lines):
        if l.startswith("import") or l.startswith("from"):
            insert_at = i+1
    lines.insert(insert_at, loader)
    text = "\n".join(lines)
    path.write_text(text)
    print("Injected loader")
else:
    print("Loader already present")

# Also check what Phase6 does to read keys
print("--- checking key read ---")
if "BINANCE_API_KEY" in text:
    print("uses BINANCE_API_KEY")
    # show snippet
    for i,line in enumerate(text.splitlines()):
        if "BINANCE_API_KEY" in line:
            print(f"{i}: {line}")
else:
    print("NO BINANCE_API_KEY found in file!")
