import pathlib
p=pathlib.Path("phase5_market_intelligence.py").read_text()

# Patch: use fallback URLs
old="def get_json(path, params=None):"
new="""def get_json(path, params=None):
    import random
    bases=["https://api.binance.com","https://api1.binance.com","https://api2.binance.com","https://api3.binance.com","https://data-api.binance.vision"]
    random.shuffle(bases)
    for base in bases:
        try:
            url = f"{base}{path}"
            response = __import__('requests').get(url, params=params, timeout=10)
            if response.status_code==200:
                return response.json()
        except Exception:
            continue
    # last try original
    import requests
    response = requests.get(f"https://api.binance.com{path}", params=params, timeout=15)
    return response.json()
def get_json_orig(path, params=None):"""

if old in p and "def get_json_orig" not in p:
    p=p.replace(old,new,1)
    pathlib.Path("phase5_market_intelligence.py").write_text(p)
    print("PATCHED")
else:
    print("Already patched or pattern not found")
