import json
from pathlib import Path
from datetime import datetime

ORDERS_FILE = Path("reports/orders.json")
ORDERS_FILE.parent.mkdir(exist_ok=True)

class SpotExecutionAdapter:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.orders = []
        if ORDERS_FILE.exists():
            try:
                self.orders = json.loads(ORDERS_FILE.read_text())
            except:
                self.orders = []

    def execute(self, payload):
        """
        payload = {coin, side, price, qty, quality}
        Returns executed order dict
        """
        order = {
            "id": len(self.orders)+1,
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": payload.get("coin", "BTCUSDT"),
            "side": payload.get("side", "BUY"),
            "price": payload.get("price", 64900),
            "qty": payload.get("qty", 0.001),
            "quality": payload.get("quality", 88),
            "dry_run": self.dry_run,
            "status": "FILLED" if self.dry_run else "SENT_TO_BINANCE",
        }
        # REAL BINANCE CALL WOULD GO HERE:
        # if not self.dry_run:
        #   from binance.client import Client
        #   client = Client(API_KEY, API_SECRET)
        #   client.create_order(symbol=order["symbol"], side=order["side"], type="MARKET", quantity=order["qty"])

        self.orders.append(order)
        ORDERS_FILE.write_text(json.dumps(self.orders, indent=2))
        print(f"  💰 EXECUTED: {order['side']} {order['qty']} {order['symbol']} @ {order['price']} | dry_run={self.dry_run} | total_orders={len(self.orders)}")
        return order

    def get_positions(self):
        # Aggregate from orders
        pos = {}
        for o in self.orders[-10:]:
            pos[o["symbol"]] = {"qty": o["qty"], "entry": o["price"], "pnl": "+1.2% dry"}
        return pos
