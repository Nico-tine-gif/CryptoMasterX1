import json
from pathlib import Path
data=json.loads(Path("state/phase5_market_intelligence.json").read_text())
for r in data['results'][:3]:
    if r.get('intelligence',{}).get('qualified'):
        print("QUALIFIED", r['symbol'])
        print("trade_construction:", r.get('trade_construction'))
        print("volatility:", r.get('volatility'))
        print("dashboard:", r.get('dashboard'))
        print("---")
