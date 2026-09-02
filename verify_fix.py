#!/usr/bin/env python3
"""Verify all fixes"""
import json
from pathlib import Path

state_dir = Path('state')
config_dir = Path('config')

print("=" * 60)
print("🔍 FINAL VERIFICATION")
print("=" * 60)

# Phase 2 checks
print("\n📋 PHASE 2 - ACCOUNT BINDING:")
checks = {
    'Machine Identity': (state_dir / 'machine_identity.json').exists(),
    'Secure Credentials': (config_dir / 'secure_credentials.json').exists(),
    'Logging Config': (state_dir / 'logging_config.json').exists(),
    'Binding Record': (state_dir / 'account_binding.json').exists(),
}

if (config_dir / 'binance_config.json').exists():
    with open(config_dir / 'binance_config.json', 'r') as f:
        config = json.load(f)
    checks['No Plaintext Secret'] = 'api_secret' not in config
else:
    checks['No Plaintext Secret'] = True

all_pass = True
for check, passed in checks.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {check}: {status}")
    if not passed:
        all_pass = False

# Phase 3 checks
print("\n📋 PHASE 3 - EXECUTION BOUNDARY:")
boundary_file = state_dir / 'execution_boundary.json'
if boundary_file.exists():
    with open(boundary_file, 'r') as f:
        boundary = json.load(f)
    
    phase3_checks = {
        'Account Binding': boundary.get('account_binding') == 'BOUND',
        'Execution Authorization': boundary.get('execution_authorization') == 'AUTHORIZED',
        'Bot Armed': boundary.get('bot_armed', False),
        'Order Submission': boundary.get('order_submission') == 'ENABLED',
        'Transmission': boundary.get('transmission') == 'OPEN',
    }
    
    for check, passed in phase3_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check}: {status}")
        if not passed:
            all_pass = False
    
    # Safety checks
    safety = boundary.get('safety_checks', {})
    print("\n  Safety Limits:")
    print(f"    Max Order: {safety.get('max_order_size', 0) * 100}%")
    print(f"    Max Daily Loss: {safety.get('max_daily_loss', 0) * 100}%")
    print(f"    Kill Switch: {'ACTIVE' if safety.get('kill_switch_active') else 'INACTIVE'}")
else:
    print("  ❌ Execution boundary not found")
    all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("✅ SYSTEM READY")
    print("🔒 All security checks passed")
    print("⚠️  Real trading enabled - use caution")
else:
    print("❌ SYSTEM NOT READY")
    print("🔧 Some checks still failing")
print("=" * 60)
