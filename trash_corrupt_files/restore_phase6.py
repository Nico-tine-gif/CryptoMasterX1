from pathlib import Path
import textwrap
p = Path("phase6_trade_intelligence.py").read_text()

# Fix the unterminated string - remove our bad injection
p = p.replace("# --- OVERRIDE FOR $21 ACCOUNT ---\n              account_balance = 21.03", "# OVERRIDE_PLACEHOLDER")
p = p.replace('account_balance = 21.03  # from your screenshot balance_available = True\nprint(f"[OVERRIDE] Using total Spot PNL value: {account_balance} USDT for sizing")', 'account_balance = 21.03')
p = p.replace('# --- END OVERRIDE ---', '')
p = p.replace('# OVERRIDE_PLACEHOLDER', '')

# Clean any broken line
lines=[]
for line in p.splitlines():
    if 'Reading account balance...' in line and line.count('"')%2==1:
        # fix unterminated
        line = line.replace('"', '').strip() + '")'
        line = '    print("Reading account balance...")'
    lines.append(line)
p="\n".join(lines)

Path("phase6_trade_intelligence.py").write_text(p)
print("Restored")
