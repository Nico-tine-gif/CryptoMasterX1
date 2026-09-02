import pathlib
path = pathlib.Path("phase5_market_intelligence.py")
p = path.read_text()

# Fix fetch_klines to use fallback domains + lighter limit
old_def = "def fetch_klines(symbol, interval, limit):"
if old_def in p:
    new_def = """def fetch_klines(symbol, interval, limit=50):
    import random, time, requests
    bases=["https://api.binance.com","https://api1.binance.com","https://api2.binance.com","https://api3.binance.com","https://data-api.binance.vision"]
    random.shuffle(bases)
    for base in bases:
        try:
            url=f"{base}/api/v3/klines"
            params={"symbol":symbol,"interval":interval,"limit":limit}
            r=requests.get(url, params=params, timeout=8)
            if r.status_code==200:
                return r.json()
        except Exception:
            time.sleep(0.2)
            continue
    return []"""
    # replace old function (capture until next def)
    import re
    p = re.sub(r"def fetch_klines\(symbol, interval, limit\):.*?return \[\]", new_def, p, flags=re.DOTALL)

# Fix phase6/7/8 once mode clean
for fname in ["phase6_trade_quality.py","phase7_entry_intelligence.py","phase8_entry_validation.py"]:
    fp = pathlib.Path(fname)
    if not fp.exists(): continue
    q = fp.read_text()
    # ensure once exits after one report
    if "ONCE MODE" not in q:
        q = q.replace("Next Phase 6 scan in 60 seconds...", "Next Phase 6 scan in 60 seconds...\nimport sys\nif '--once' in sys.argv:\n    print('ONCE MODE - EXIT'); sys.exit(0)")
        q = q.replace("Next Phase 7 scan in 60 seconds...", "Next Phase 7 scan in 60 seconds...\nimport sys\nif '--once' in sys.argv:\n    print('ONCE MODE - EXIT'); sys.exit(0)")
        q = q.replace("Next Phase 8 scan in 60 seconds...", "Next Phase 8 scan in 60 seconds...\nimport sys\nif '--once' in sys.argv:\n    print('ONCE MODE - EXIT'); sys.exit(0)")
        q = q.replace("Next intelligence scan in 60 seconds...", "Next intelligence scan in 60 seconds...\nimport sys\nif '--once' in sys.argv:\n    print('ONCE MODE - EXIT'); sys.exit(0)")
        fp.write_text(q)

path.write_text(p)
print("FIXED")
