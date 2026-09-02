from pathlib import Path
p=Path("master_pipeline.py").read_text()
# Force LIVE
p=p.replace("LIVE_EXECUTION = False","LIVE_EXECUTION = True")
p=p.replace("PAPER_MODE = True","PAPER_MODE = False")
p=p.replace('LIVE_EXECUTION = os.getenv("LIVE","false").lower()=="true"','LIVE_EXECUTION = True')
p=p.replace('PAPER_MODE = os.getenv("PAPER","true").lower()=="true"','PAPER_MODE = False')
Path("master_pipeline.py").write_text(p)
print("Master armed LIVE")
