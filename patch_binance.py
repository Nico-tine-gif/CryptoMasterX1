import pathlib, json, textwrap
# rewrite phase files with correct Client usage
template = """
from binance.client import Client
import time, json, pathlib
bind=json.loads(pathlib.Path("state/account_binding.json").read_text())
client=Client(bind["api_key"], bind["api_secret"])
try:
    srv=client.get_server_time()['serverTime']
    diff=srv-int(time.time()*1000)
    client=Client(bind["api_key"], bind["api_secret"])
    client.timestamp_offset=diff
    # increase recv window
    client.RECV_WINDOW=60000
except Exception as e:
    print(f"time sync warning: {e}")
"""

# patch all phase10 files + phase3
for fname in pathlib.Path(".").glob("phase*.py"):
    txt=fname.read_text()
    if "from binance.client import Client" in txt:
        # remove old bad Client(..., {"recvWindow"
        txt=txt.replace('{"recvWindow": 60000}', '').replace('{"recvWindow": 60000, "timeOffset": diff}', '').replace('{"recvWindow": 60000, "timeOffset": 25000000})', '')
        txt=txt.replace('Client(bind["api_key"], bind["api_secret"], )', 'Client(bind["api_key"], bind["api_secret"])')
        txt=txt.replace('Client(bind["api_key"], bind["api_secret"], {', 'Client(bind["api_key"], bind["api_secret"]) # {')
        # add offset after first Client creation if not present
        if "timestamp_offset" not in txt and "Client(bind" in txt:
            txt=txt.replace('client=Client(bind["api_key"], bind["api_secret"])', 'client=Client(bind["api_key"], bind["api_secret"])\n try:\n import time\n srv=client.get_server_time()["serverTime"]\n client.timestamp_offset=srv-int(time.time()*1000)\n client.RECV_WINDOW=60000\n except: pass', 1)
        fname.write_text(txt)
        print(f"patched {fname}")

print("done patching")
