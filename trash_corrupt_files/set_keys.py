import getpass, json, pathlib
k=getpass.getpass("Paste NEW API Key (hidden): ")
s=getpass.getpass("Paste NEW API Secret (hidden): ")
pathlib.Path("state").mkdir(exist_ok=True)
pathlib.Path("state/account_binding.json").write_text(json.dumps({"api_key":k[:8]+"...","bound":True}))
open(".env.keys","w").write(f"BINANCE_API_KEY={k}\nBINANCE_API_SECRET={s}\n")
print("Keys saved to .env.keys - not in logs")
