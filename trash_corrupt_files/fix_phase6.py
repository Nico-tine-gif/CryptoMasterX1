from pathlib import Path
p = Path("phase6_trade_intelligence.py").read_text()
# The bug is at line 293 - make it safe
p = p.replace('candidate["atr_5m"]', 'candidate.get("atr_5m", candidate.get("atr", 0))')
p = p.replace("candidate['atr_5m']", "candidate.get('atr_5m', candidate.get('atr', 0))")
# also fix account balance read to use env keys
if "BINANCE_API credentials unavailable" in p or "ACCOUNT BALANCE READ UNAVAILABLE" in p:
    # inject key loader at top
    if "load_dotenv" not in p:
        p = p.replace("import os", "import os\nfrom pathlib import Path\n# load .env.keys\n_kf=Path('.env.keys')\nif _kf.exists():\n    for _l in _kf.read_text().splitlines():\n        if '=' in _l:\n            _k,_v=_l.split('=',1)\n            os.environ[_k.strip()]=_v.strip()\n")
Path("phase6_trade_intelligence.py").write_text(p)
print("Phase6 fixed")
