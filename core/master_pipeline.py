import asyncio
from pathlib import Path
import importlib.util
from .health import HealthController

class PipelineContext:
    def __init__(self):
        self.data = {}
        self.market_intelligence = {}
        self.execution_payloads = []
        self.gate_passed = False
        self.active_positions = {}
        self.system_verification_status = "PENDING"
        self.loop_count = 0

class MasterPipeline:
    def __init__(self, health_controller=None):
        self.health = health_controller or HealthController()
        self.ctx = PipelineContext()
        self.phases = [
            ("P1-SCANNER","phase1_scanner"),
            ("P2-AUTH","phase2_auth"),
            ("P3-ACCOUNT","phase3_account_verify"),
            ("P4-DISCOVERY","phase4_market_discovery"),
            ("P5-INTELLIGENCE","phase5_market_intelligence"),
            ("P6-QUALITY","phase6_trade_intelligence"),
            ("P7-ENTRY","phase7_entry_intelligence"),
            ("P8-VALIDATION","phase8_entry_validation"),
            ("P9-GATE","phase9_decision_gate"),
            ("P10-MONITOR","phase10_monitoring"),
            ("P11-VERIFY","phase11_full_system_verification"),
        ]

    def load(self, name):
        p = Path(__file__).parent / f"{name}.py"
        spec = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    async def run_pipeline(self):
        print("⚡ MASTER PIPELINE - NON-STOP LOOP")
        while True:
            self.ctx.loop_count += 1
            print(f"\n========== LOOP #{self.ctx.loop_count} ==========")
            for pname, fname in self.phases:
                mod = self.load(fname)
                self.ctx = mod.process(self.ctx)
                self.health.report_heartbeat(pname, "NOMINAL")
                await asyncio.sleep(0.05)
            await asyncio.sleep(1)

    def run(self, dry_run=False):
        return asyncio.run(self.run_pipeline())
