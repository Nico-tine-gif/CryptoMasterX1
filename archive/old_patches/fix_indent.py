import pathlib, re
path = pathlib.Path("phase5_market_intelligence.py")
text = path.read_text()

# Delete any stray _t lines and broken get_json duplicate
text = text.replace("_t.sleep(0.2)","")
text = text.replace("_t.sleep(0.4)","")
text = text.replace("import time as _t","")
text = re.sub(r"def get_json_orig.*","", text)
# Remove duplicate get_json definitions — keep only one
# Ensure fetch_klines is clean
clean_fetch = """
def fetch_klines(symbol, interval, limit=50):
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
    return []
"""
# replace old fetch_klines
text = re.sub(r"def fetch_klines\(.*?\n    return \[\]", clean_fetch.strip(), text, flags=re.DOTALL)

path.write_text(text)
print("cleaned")
