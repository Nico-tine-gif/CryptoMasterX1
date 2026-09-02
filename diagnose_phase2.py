#!/usr/bin/env python3
"""
Diagnose Phase 2 account binding issues
"""
import json
from pathlib import Path
from datetime import datetime

def diagnose():
    print("=" * 60)
    print("🔍 PHASE 2 DIAGNOSIS")
    print("=" * 60)
    
    # Check all relevant files
    files_to_check = [
        'state/account_binding.json',
        'state/machine_identity.json',
        'config/secure_credentials.json',
        'config/binance_config.json',
        'state/logging_config.json',
        'state/execution_boundary.json',
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"\n✅ {file_path} exists")
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                # Print key fields
                if 'account_binding' in file_path:
                    print(f"   Binding status: {data.get('binding_status', 'MISSING')}")
                    print(f"   Machine identity: {data.get('machine_identity', 'MISSING')}")
                    print(f"   API secret storage: {data.get('api_secret_storage', 'MISSING')}")
                    print(f"   API secret display: {data.get('api_secret_display', 'MISSING')}")
                    print(f"   Credential logging: {data.get('credential_logging', 'MISSING')}")
                elif 'machine_identity' in file_path:
                    print(f"   Machine ID: {data.get('machine_id', 'MISSING')[:16]}...")
                    print(f"   Binding status: {data.get('binding_status', 'MISSING')}")
                elif 'secure_credentials' in file_path:
                    print(f"   API Key: {data.get('api_key', 'MISSING')[:10]}...")
                    print(f"   Encryption: {data.get('encryption_method', 'MISSING')}")
            except Exception as e:
                print(f"   ❌ Error reading: {e}")
        else:
            print(f"\n❌ {file_path} NOT FOUND")
    
    # Check for plaintext secrets
    print("\n🔒 CHECKING FOR PLAINTEXT SECRETS:")
    for py_file in Path('.').glob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            if 'api_secret' in content.lower() and 'encrypted' not in content.lower():
                print(f"   ⚠️  {py_file} may contain plaintext secret handling")
        except:
            pass
    
    # Check the actual Phase 2 module
    phase2_files = list(Path('.').glob('*phase*2*.py')) + list(Path('.').glob('*account*binding*.py'))
    if phase2_files:
        print(f"\n📁 Phase 2 module files found:")
        for f in phase2_files:
            print(f"   - {f}")
            try:
                with open(f, 'r') as file:
                    content = file.read()
                # Look for validation logic
                if 'def run' in content or 'def check' in content:
                    print(f"     Contains validation logic")
                if 'api_secret_storage' in content:
                    # Find the validation criteria
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'api_secret_storage' in line:
                            print(f"     Line {i}: {line.strip()}")
                            # Print surrounding lines
                            for j in range(max(0, i-3), min(len(lines), i+3)):
                                print(f"       {j}: {lines[j].strip()}")
            except Exception as e:
                print(f"     Error reading: {e}")
    else:
        print("\n❌ No Phase 2 module files found")

if __name__ == "__main__":
    diagnose()
