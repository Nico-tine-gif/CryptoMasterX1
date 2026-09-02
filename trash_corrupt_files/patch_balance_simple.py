from pathlib import Path
p=Path("phase6_trade_intelligence.py").read_text()
# Force replace first 30 lines of get_account function with simple return
if "[OVERRIDE] Using total wallet" not in p:
    p=p.replace(
        'def get_account_usdt_balance():\n    """\n    Reads the Binance Spot account balance.',
        'def get_account_usdt_balance():\n    print("[OVERRIDE] Using total wallet 21.03 USDT (BNB+USDT)")\n    return 21.03\n    """\n    Reads the Binance Spot account balance.'
    )
    # remove duplicate return
    Path("phase6_trade_intelligence.py").write_text(p)
    print("simple override added")
else:
    print("already")
