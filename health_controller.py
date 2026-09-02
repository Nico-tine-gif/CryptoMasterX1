import os
import requests
def run_health_check_or_block():
    try:
        r=requests.get("https://api.binance.com/api/v3/ping",timeout=5)
        api_ok=r.status_code==200
    except: api_ok=False
    print(f"=== HEALTH CONTROLLER ===\n API: {'HEALTHY' if api_ok else 'FAIL'}")
    if not api_ok: return False,"SAFE_STOP"
    return True,"CONTINUE"
