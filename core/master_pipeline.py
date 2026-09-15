import asyncio
import logging
import importlib
import sys

logger = logging.getLogger("CryptoMasterX1.Pipeline")

class PipelineContext:
    """The continuous state adapter keeping data alive across phases."""
    def __init__(self):
        self.market_intelligence = {}
        self.execution_payloads = []
        self.gate_passed = False
        self.active_positions = {}
        self.system_verification_status = "PENDING"

class MasterPipeline:
    def __init__(self, health_controller):
        self.health = health_controller
        self.ctx = PipelineContext()
        
        # Exact phase blueprint matching your system specifications
        self.phases = [
            {"name": "P1", "module": "modules.p1_core", "func": "process"},
            {"name": "P2", "module": "modules.p2_auth", "func": "process"},
            {"name": "P3", "module": "modules.p3_binance", "func": "process"},
            {"name": "P4", "module": "modules.p4_discovery", "func": "process"},
            {"name": "P5", "module": "modules.p5_intelligence", "func": "process"},
            {"name": "P6", "module": "modules.p6_quality", "func": "process"},
            {"name": "P7", "module": "modules.p7_entry", "func": "process"},
            {"name": "P8", "module": "modules.p8_execution", "func": "process"},
            {"name": "P9", "module": "modules.p9_gate", "func": "process"},
            {"name": "P10", "module": "modules.p10_monitoring", "func": "process"},
            {"name": "P11", "module": "modules.p11_verification", "func": "process"},
        ]

    async def run_pipeline(self):
        logger.info("⚡ MASTER PIPELINE: Loop initiated. No holidays in crypto.")
        
        while True:
            try:
                for phase in self.phases:
                    # Dynamically extract and cycle phase functions
                    mod = importlib.import_module(phase["module"])
                    func = getattr(mod, phase["func"])
                    
                    # Cycle context adapter down the loop
                    self.ctx = await func(self.ctx)
                    
                    # Ping Health Controller Watchdog instantly
                    self.health.report_heartbeat(phase["name"], "NOMINAL")
                
                # Zero delay pause sequence - quick yield to keep Termux responsive
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"⚠️ PIPELINE INSTABILITY DETECTED: {str(e)}")
                self.health.report_error("PIPELINE_CRASH", str(e))
                await asyncio.sleep(1) # Structural recovery delay
