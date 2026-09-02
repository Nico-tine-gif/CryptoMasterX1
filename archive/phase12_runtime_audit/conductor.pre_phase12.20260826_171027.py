#!/usr/bin/env python3

import subprocess
import sys
import time

ONCE = "--once" in sys.argv

PHASES = [
    ("PHASE 4 — MARKET SCANNING + DISCOVERY",
     ["phase4_market_discovery.py"], 180),

    ("PHASE 5 — TRADE INTELLIGENCE + DETECTORS",
     ["phase5_market_intelligence.py", "--once"], 900),

    ("PHASE 6 — TRADE VERIFICATION + FINAL CONSTRUCTION",
     ["phase6_trade_intelligence.py", "--once"], 900),

    ("PHASE 7 — EXECUTION + ORDER OPENING",
     ["phase7_final_validation.py", "--once"], 600),

    ("PHASE 8 — TRADE LIFECYCLE MANAGEMENT",
     ["phase8_execution_lifecycle_v8.py", "--once"], 600),
]


def run_phase(label, command, timeout):
    print(f"\n>>> {label}", flush=True)

    result = subprocess.run(
        [sys.executable] + command,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{label} exited with return code {result.returncode}"
        )

    return result


def main():
    cycle = 0

    print(
        "============================================================",
        flush=True,
    )
    print(
        "CRYPTOMASTERX1 — CONSOLIDATED 8-PHASE CONDUCTOR",
        flush=True,
    )
    print(
        "LIVE EXECUTION MUST REMAIN LOCKED DURING VERIFICATION",
        flush=True,
    )
    print(
        "============================================================",
        flush=True,
    )

    while True:
        cycle += 1

        print(
            f"\n{'=' * 78}\n"
            f"CRYPTOMASTERX1 — CYCLE {cycle}\n"
            f"{'=' * 78}",
            flush=True,
        )

        try:
            for label, command, timeout in PHASES:
                run_phase(label, command, timeout)

            print(
                f"\n=== CYCLE {cycle} COMPLETE ===",
                flush=True,
            )

            if ONCE:
                print(
                    "=== CONDUCTOR ONCE MODE — EXIT ===",
                    flush=True,
                )
                break

            print(
                "\n=== CONDUCTOR SLEEP 60 SECONDS ===",
                flush=True,
            )

            time.sleep(60)

        except subprocess.TimeoutExpired as exc:
            print(
                f"\nTIMEOUT: {exc.cmd} after {exc.timeout}s",
                flush=True,
            )

            if ONCE:
                break

            time.sleep(5)

        except KeyboardInterrupt:
            print(
                "\n=== CONDUCTOR STOPPED BY USER ===",
                flush=True,
            )
            break

        except Exception as exc:
            print(
                f"\nCONDUCTOR ERROR: {exc}",
                flush=True,
            )

            if ONCE:
                break

            time.sleep(5)


if __name__ == "__main__":
    main()
