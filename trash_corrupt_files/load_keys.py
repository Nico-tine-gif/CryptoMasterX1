from pathlib import Path
import os
env_path = Path(".env.keys")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            os.environ[k.strip()]=v.strip()
print("keys loaded into env")
