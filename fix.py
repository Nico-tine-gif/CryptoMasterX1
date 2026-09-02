import os
from pathlib import Path

print("1. Checking .env files...")
for f in ['.env', '.env.keys']:
    p = Path(f)
    if p.exists():
        print(f"\n{f}:")
        for line in p.read_text().split('\n'):
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                if 'SECRET' in key:
                    print(f"  {key}=HIDDEN")
                else:
                    print(f"  {key}={val}")

print("\n2. Fixing ARMED bug in phase6...")
p6 = Path('phase6_trade_intelligence.py')
if p6.exists():
    content = p6.read_text()
    content = content.replace('{ARMED if LIVE_EXECUTION else LOCKED}', "{'ARMED' if LIVE_EXECUTION else 'LOCKED'}")
    p6.write_text(content)
    print("Fixed phase6")

print("\n3. Adding dotenv to master_pipeline.py...")
mp = Path('master_pipeline.py')
if mp.exists():
    content = mp.read_text()
    if 'load_dotenv' not in content:
        content = 'from dotenv import load_dotenv\nload_dotenv()\n\n' + content
        mp.write_text(content)
        print("Added dotenv loading")

print("\n4. Testing API connection...")
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
print(f"API Key: {api_key[:10] if api_key else 'MISSING'}...")
print(f"API Secret: {api_secret[:10] if api_secret else 'MISSING'}...")

if api_key and api_secret:
    try:
        from binance.client import Client
        client = Client(api_key, api_secret)
        account = client.get_account()
        print("API connection successful!")
        for b in account['balances']:
            if b['asset'] == 'USDT':
                print(f"USDT Balance: {b['free']}")
    except Exception as e:
        print(f"Connection error: {e}")
