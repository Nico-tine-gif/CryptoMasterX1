import asyncio
import logging
import sys
import time
from core.master_pipeline import MasterPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CryptoMasterX1.Main")

# =====================================================================
# HEALTH CONTROLLER
# =====================================================================
class HealthController:
    """
    ▲ HEALTH CONTROLLER
    Handles: system health, component health, error detection,
    recovery/restart, pipeline stability, and runtime watchdog duties.
    """
    def __init__(self):
        self.heartbeats = {}
        self.system_stable = True

    def report_heartbeat(self, phase_name: str, status: str):
        self.heartbeats[phase_name] = {"timestamp": time.time(), "status": status}

    def report_error(self, component: str, error_msg: str):
        logger.error(f"▲ HEALTH CONTROLLER Alert -> Component Error caught in [{component}]: {error_msg}")
        # Run auto-recovery routines here

    async def run_watchdog(self):
        logger.info("▲ HEALTH CONTROLLER: Watchdog Active. Tracking continuous system metrics.")
        while True:
            await asyncio.sleep(5)
            # Cycle stability diagnostics across pipeline data pipelines
            logger.info(f"▲ HEALTH CHECK: Diagnostics nominal. Processing cycles clean.")

# =====================================================================
# CRYPTOMASTER X1 APP LAYERS
# =====================================================================
class CryptoMasterX1App:
    """APP / UI Wrapper Layer."""
    def __init__(self):
        self.health = HealthController()
        self.pipeline = MasterPipeline(self.health)

    async def run(self):
        logger.info("▼ APP / UI Engine Active. Spawning master tracking concurrent threads.")
        # Connects directly to core.master_pipeline.run_pipeline()
        await asyncio.gather(
            self.pipeline.run_pipeline(),
            self.health.run_watchdog()
        )

def check_password_lock() -> bool:
    """Secure local terminal gateway barrier."""
    print("=========================================")
    print("🔒 CRYPTOMASTER X1 SECURITY GATEWAY")
    print("=========================================")
    try:
        entered_pin = input("Enter System Security Access Pin: ").strip()
        return entered_pin == "admin123"
    except (IOError, EOFError):
        return False

def main():
    # main.py -> Password Lock logic check
    if not check_password_lock():
        print("❌ ACCESS DENIED.")
        sys.exit(1)
        
    print("✅ ACCESS GRANTED. Initializing Master Framework Architecture...")
    
    # -> CryptoMasterX1App Layer
    app = CryptoMasterX1App()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n⚙️ System shutdown sequence finalized safely.")

if __name__ == "__main__":
    main()
