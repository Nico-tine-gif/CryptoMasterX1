import pathlib, re, textwrap

# === 1. FIX CONDUCTOR - 600s for phase5, 120s for others ===
path = pathlib.Path("conductor.py")
path.write_text("""#!/usr/bin/env python3
import subprocess, sys, time
print("=== CONDUCTOR ONCE MODE - FIXED ===")
while True:
    try:
        print("\\n>>> PHASE 4")
        subprocess.run([sys.executable, "phase4_market_discovery.py"], timeout=120)
        print(">>> PHASE 5 (65 markets - needs 600s)")
        subprocess.run([sys.executable, "phase5_market_intelligence.py"], timeout=600)
        print(">>> PHASE 6 ONCE")
        subprocess.run([sys.executable, "phase6_trade_quality.py","--once"], timeout=120)
        print(">>> PHASE 7 ONCE")
        subprocess.run([sys.executable, "phase7_entry_intelligence.py","--once"], timeout=120)
        print(">>> PHASE 8 ONCE")
        subprocess.run([sys.executable, "phase8_entry_validation.py","--once"], timeout=120)
        print("\\n=== Cycle DONE - sleep 60 ===")
        time.sleep(60)
    except subprocess.TimeoutExpired as e:
        print(f"TIMEOUT {e.cmd} after {e.timeout}s - will retry next cycle")
        time.sleep(5)
    except Exception as e:
        print(f"ERR {e}")
        time.sleep(5)
""")
print("fixed conductor.py")

# === 2. FIX PHASE5 ===
p5 = pathlib.Path("phase5_market_intelligence.py")
t = p5.read_text()

# Fix REQUEST_TIMEOUT
t = t.replace("REQUEST_TIMEOUT = 15", "REQUEST_TIMEOUT = 8")

# Fix get_json to use fallback domains
new_get_json = """def get_json(path, params=None):
    import random, time, requests
    bases=["https://api.binance.com","https://api1.binance.com","https://api2.binance.com","https://api3.binance.com","https://data-api.binance.vision"]
    random.shuffle(bases)
    for base in bases:
        try:
            url = f"{base}{path}"
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except Exception:
            time.sleep(0.2)
            continue
    return {}
"""

t = re.sub(r"def get_json\(path, params=None\):.*?return \{\}", new_get_json, t, flags=re.DOTALL)

# Fix fetch_klines completely
new_fetch = """def fetch_klines(symbol, interval, limit=50):
    import random, time, requests
    bases=["https://api.binance.com","https://api1.binance.com","https://api2.binance.com","https://api3.binance.com","https://data-api.binance.vision"]
    random.shuffle(bases)
    for base in bases:
        try:
            url=f"{base}/api/v3/klines"
            params={"symbol":symbol,"interval":interval,"limit":limit}
            r=requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code==200:
                return r.json()
        except Exception:
            time.sleep(0.3)
            continue
    return []
"""
t = re.sub(r"def fetch_klines\(symbol, interval, limit.*?\n    return \[\]", new_fetch.strip(), t, flags=re.DOTALL)

# Clean stray _t.sleep and import time as _t bugs
t = t.replace("import time as _t", "import time")
t = t.replace("_t.sleep", "time.sleep")

# Ensure scan loop has sleep between markets
t = re.sub(r"time\.sleep\(\s*0\.4\s*\)", "time.sleep(0.35)", t)

# Fix main while True to support --once properly
if "if '--once' in sys.argv" not in t:
    t = t.replace("while True:", "import sys\n    once = '--once' in sys.argv\n    while True:")

# Ensure final sleep block handles once
t = re.sub(r"print.*Next intelligence scan.*\n.*time\.sleep\(.*\)", "print('Next intelligence scan in 60 seconds...')\n            import sys\n            if '--once' in sys.argv:\n                print('ONCE MODE - EXIT'); break\n            time.sleep(60)", t)

p5.write_text(t)
print("fixed phase5")

# === 3. FIX PHASE6,7,8 ONCE LOGIC ===
for fname in ["phase6_trade_quality.py","phase7_entry_intelligence.py","phase8_entry_validation.py"]:
    fp = pathlib.Path(fname)
    if not fp.exists(): continue
    q = fp.read_text()
    # inject sys check at start of main
    if "ONCE MODE - EXIT" not in q:
        q = q.replace("while True:", "import sys\n    once = '--once' in sys.argv\n    while True:")
        # replace both sleep occurrences
        q = q.replace("time.sleep(REFRESH_SECONDS)", "import sys\n            if '--once' in sys.argv or once:\n                print('ONCE MODE - EXIT'); break\n            time.sleep(REFRESH_SECONDS)")
        # fallback generic
        q = re.sub(r"Next .*? scan in 60 seconds\.\.\.\n.*?time\.sleep\(60\)", "Next scan in 60 seconds...\n            import sys\n            if '--once' in sys.argv or once:\n                print('ONCE MODE - EXIT'); break\n            time.sleep(60)", q, flags=re.DOTALL)
    fp.write_text(q)
    print(f"fixed {fname}")

print("ALL FIXED")
