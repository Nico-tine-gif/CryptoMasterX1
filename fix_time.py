import pathlib
for name in ["phase3_account_verify.py","phase10_trade_lifecycle.py","phase10_pre_execution_gate.py","phase10_monitoring.py"]:
    p=pathlib.Path(name)
    if not p.exists(): continue
    t=p.read_text()
    # add time offset logic
    if "timeOffset" not in t:
        t=t.replace("Client(bind[", "Client(bind[\"api_key\"], bind[\"api_secret\"], {\"recvWindow\": 60000, \"timeOffset\": 25000000})\n    _orig=Client(bind[")
        # simpler: patch all Client() calls
    # better brute force replace
    t=t.replace("Client(bind[\"api_key\"], bind[\"api_secret\"])", "Client(bind[\"api_key\"], bind[\"api_secret\"], {\"recvWindow\": 60000})")
    t=t.replace("Client(api_key, api_secret)", "Client(api_key, api_secret, {\"recvWindow\": 60000})")
    # ensure timestamp sync
    if "client.get_server_time" not in t:
        t=t.replace("client=Client", "import time\nclient=Client")
    p.write_text(t)
    print(f"patched {name}")

# direct test
from binance.client import Client
import json, pathlib
bind=json.loads(pathlib.Path("state/account_binding.json").read_text())
client=Client(bind["api_key"], bind["api_secret"], {"recvWindow": 60000})
# force time sync
diff=client.get_server_time()['serverTime'] - client.get_system_time()
print(f"time diff ms: {diff}")
client = Client(bind["api_key"], bind["api_secret"], {"recvWindow": 60000, "timeOffset": diff})
print(client.get_account())
print("SUCCESS - API works now")
