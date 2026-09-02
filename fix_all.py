from pathlib import Path

print('=== FIXING ALL ISSUES ===')

# 1. Fix phase10_trade_lifecycle.py
p = Path('phase10_trade_lifecycle.py')
if p.exists():
    content = p.read_text()
    
    # Add rounding helpers if not present
    if 'round_step_size' not in content:
        helper = '''

def round_step_size(quantity, step_size):
    from decimal import Decimal
    step = Decimal(str(step_size))
    qty = Decimal(str(quantity))
    return float((qty // step) * step)

def get_symbol_filters(symbol):
    try:
        info = client.get_symbol_info(symbol)
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                return {'stepSize': float(f['stepSize'])}
    except:
        pass
    return None
'''
        # Find where to insert (after all imports)
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                insert_pos = i + 1
        
        content = '\n'.join(lines[:insert_pos]) + helper + '\n'.join(lines[insert_pos:])
        print('1. Added rounding helpers')
    
    # Add rounding to order execution
    if 'round_step_size(qty' not in content:
        old = 'order=client.order_market_buy(symbol=sym, quantity=qty)'
        new = '''filters = get_symbol_filters(sym)
if filters:
    qty = round_step_size(qty, filters['stepSize'])
order=client.order_market_buy(symbol=sym, quantity=qty)'''
        content = content.replace(old, new)
        print('2. Added LOT_SIZE rounding to orders')
    
    # Enable live trading
    content = content.replace('LIVE=False', 'LIVE=True')
    content = content.replace('PAPER=True', 'PAPER=False')
    content = content.replace('ORDERS=False', 'ORDERS=True')
    
    p.write_text(content)
    print('3. Updated phase10 flags to LIVE')

# 2. Update master_pipeline.py
p = Path('master_pipeline.py')
if p.exists():
    content = p.read_text()
    content = content.replace('LIVE=False', 'LIVE=True')
    content = content.replace('PAPER=True', 'PAPER=False')
    content = content.replace('ARMED=False', 'ARMED=True')
    content = content.replace('ORDERS=False', 'ORDERS=True')
    p.write_text(content)
    print('4. Updated master_pipeline.py flags')

print()
print('=== ALL FIXES COMPLETE ===')
print('Flags: LIVE=True, PAPER=False, ARMED=True, ORDERS=True')
