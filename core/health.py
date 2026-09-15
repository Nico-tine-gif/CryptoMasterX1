class HealthController:
    def report_heartbeat(self, phase, status): print(f" 💓 {phase} -> {status}")
    def report_error(self, code, msg): print(f" ❌ {code}: {msg}")
