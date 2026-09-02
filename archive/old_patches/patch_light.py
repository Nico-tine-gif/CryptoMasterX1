import pathlib
p=pathlib.Path("phase5_market_intelligence.py").read_text()
p=p.replace("limit=100","limit=50")
# add sleep
if "time.sleep(0.3)" not in p:
    p=p.replace("def scan():","import time as _t\ndef scan():")
    p=p.replace("results = []","results = []\n _t.sleep(0.2)")
    # add sleep inside loop after each symbol
    p=p.replace("MONITORED[symbol] = record","MONITORED[symbol] = record\n _t.sleep(0.4)")
pathlib.Path("phase5_market_intelligence.py").write_text(p)
print("LIGHT PATCHED")
