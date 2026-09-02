from pathlib import Path
p=Path("phase6_trade_intelligence.py").read_text()
print(p[p.find("ORDER SUBMISSION"):p.find("ORDER SUBMISSION")+500])
