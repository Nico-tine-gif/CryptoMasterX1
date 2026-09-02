import subprocess
from pathlib import Path

p = Path(__file__).parent / "full_system_stability_scan.py"
subprocess.run(["python3", str(p)])
