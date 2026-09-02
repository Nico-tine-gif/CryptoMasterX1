import pathlib
p=pathlib.Path("phase5_market_intelligence.py").read_text()
# Replace any reading of phase4 file to support both old and new structure
if "phase4_market_discovery.json" in p:
    print("phase5 reads phase4 file - OK")
else:
    print("phase5 DOES NOT read phase4 file - broken!")
