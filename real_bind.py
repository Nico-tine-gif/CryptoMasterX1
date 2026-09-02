import json, os
from pathlib import Path
BASE=Path.home()/"CryptoMasterX1"

print("Paste REAL Binance API Key:")
key=input("API_KEY: ").strip()
print("Paste REAL Binance API Secret:")
sec=input("API_SECRET: ").strip()

if len(key)<20 or len(sec)<20 or "your_actual" in key:
    print("❌ Still placeholder - paste real ones from Binance")
    exit(1)

# Write secure binding
( BASE/"state" ).mkdir(exist_ok=True)
binding={
    "api_key": key,
    "api_secret": sec,
    "BINANCE_API_KEY": key,
    "BINANCE_API_SECRET": sec,
    "withdrawals": False,
    "created_at": "real"
}
( BASE/"state"/"account_binding.json" ).write_text(json.dumps(binding, indent=2))
( BASE/".env" ).write_text(f"BINANCE_API_KEY={key}\nBINANCE_API_SECRET={sec}\nALLOW_LIVE=true\nPAPER_MODE=false\nORDER_SUBMISSION=true\nBOT_ARMED=true\n")

print("✅ REAL BINDING SAVED - Now test:")
from binance.client import Client
c=Client(key, sec)
print(c.get_account()['balances'][:3])
