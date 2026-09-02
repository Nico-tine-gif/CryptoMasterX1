#!/usr/bin/env python3

import subprocess
import sys
import time

ONCE = "--once" in sys.argv

print("=== CONDUCTOR - FIXED ONCE/CYCLE MODE ===", flush=True)


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

    while True:
        cycle += 1

        print(
            f"\n{'=' * 78}\n"
            f"CRYPTOMASTERX1 CONDUCTOR — CYCLE {cycle}\n"
            f"{'=' * 78}",
            flush=True,
        )

        try:
            # Phase 4 — discovery runs once.
            run_phase(
                "PHASE 4",
                ["phase4_market_discovery.py"],
                120,
            )

            # Phase 5 — explicitly once.
            run_phase(
                "PHASE 5",
                ["phase5_market_intelligence.py", "--once"],
                600,
            )

            # Phase 6 — explicitly once.
            run_phase(
                "PHASE 6",
                ["phase6_trade_quality.py", "--once"],
                120,
            )

            # Phase 7 — explicitly once.
            run_phase(
                "PHASE 7",
                ["phase7_entry_intelligence.py", "--once"],
                120,
            )

            # Phase 8 — explicitly once.
            run_phase(
                "PHASE 8",
                ["phase8_entry_validation.py", "--once"],
                120,
            )

            print(
                f"\n=== CYCLE {cycle} COMPLETE ===",
                flush=True,
            )

            if ONCE:
                print(
                    "=== CONDUCTOR ONCE MODE - EXIT ===",
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
                print(
                    "=== CONDUCTOR ONCE MODE - EXIT AFTER TIMEOUT ===",
                    flush=True,
                )
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
                print(
                    "=== CONDUCTOR ONCE MODE - EXIT AFTER ERROR ===",
                    flush=True,
                )
                break

            time.sleep(5)


if __name__ == "__main__":
    main()
