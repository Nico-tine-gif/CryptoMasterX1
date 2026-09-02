import json
from pathlib import Path
data=json.loads(Path("state/phase5_market_intelligence.json").read_text())
# find candidates list
for k,v in data.items():
    print(k, type(v), len(v) if hasattr(v,'__len__') else '')
    if isinstance(v, list) and v:
        print("Sample keys:", list(v[0].keys()) if isinstance(v[0],dict) else v[0])
        import pprint
        pprint.pprint(v[0])
        break
    if isinstance(v, dict) and v:
        first=list(v.values())[0]
        if isinstance(first, dict):
            print("Sample dict value keys:", list(first.keys())[:20])
            import pprint
            pprint.pprint(first)
            break
