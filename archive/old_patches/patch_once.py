import pathlib
for fname in ["phase6_trade_quality.py","phase7_entry_intelligence.py","phase8_entry_validation.py"]:
    path=pathlib.Path(fname)
    if not path.exists():
        print(f"Missing {fname}")
        continue
    p=path.read_text()
    p=p.replace("time.sleep(60)","import sys; print('ONCE MODE - EXIT'); sys.exit(0) if '--once' in sys.argv else __import__('time').sleep(60)")
    path.write_text(p)
    print(f"Patched {fname}")
