#!/usr/bin/env python3

from pathlib import Path
import marshal
import dis
import struct
import sys
import shutil
import types

ROOT = Path.home() / "CryptoMasterX1"
OUT = ROOT / "RECOVERED_11_PHASES"

OUT.mkdir(parents=True, exist_ok=True)

PHASES = [
    "phase1_scanner",
    "phase2_account_binding",
    "phase3_account_verify",
    "phase4_market_discovery",
    "phase5_market_intelligence",
    "phase6_trade_intelligence",
    "phase6_trade_quality",
    "phase7_entry_intelligence",
    "phase7_final_validation",
    "phase8_entry_validation",
    "phase8_execution_lifecycle_v8",
    "phase9_decision_gate",
    "phase10_pre_execution_gate",
    "phase10_trade_lifecycle",
    "phase11_full_system_verification",
]

def find_sources(name):
    matches = []

    # Prefer actual Python source.
    for p in ROOT.rglob(name + ".py"):
        if "android" not in p.parts:
            matches.append(p)

    # Also look for versioned/archive source files.
    for p in ROOT.rglob("*" + name + "*.py"):
        if "android" not in p.parts and p not in matches:
            matches.append(p)

    return matches


def find_pyc(name):
    matches = []

    for p in ROOT.rglob(name + ".cpython-313.pyc"):
        if "android" not in p.parts:
            matches.append(p)

    return matches


def pyc_code_object(path):
    data = path.read_bytes()

    # Standard CPython .pyc:
    # 4-byte magic
    # 4-byte flags
    # 8-byte timestamp/hash area
    # followed by marshalled code object.
    if len(data) < 16:
        raise ValueError("PYC file is too small")

    return marshal.loads(data[16:])


def write_disassembly(pyc, output):
    code = pyc_code_object(pyc)

    with output.open("w", encoding="utf-8") as f:
        f.write("# ============================================================\n")
        f.write("# CryptoMasterX1 recovered bytecode listing\n")
        f.write("# Source: " + str(pyc) + "\n")
        f.write("# Python runtime: " + sys.version + "\n")
        f.write("# IMPORTANT: This is DISASSEMBLED BYTECODE, not original .py.\n")
        f.write("# ============================================================\n\n")

        f.write("MODULE CODE OBJECT\n")
        f.write("==================\n\n")
        dis.dis(code, file=f)

        f.write("\n\nCODE OBJECT CONSTANTS\n")
        f.write("=====================\n\n")
        for i, const in enumerate(code.co_consts):
            f.write(f"[{i}] {const!r}\n")

        f.write("\n\nNAMES\n")
        f.write("=====\n\n")
        for name in code.co_names:
            f.write(repr(name) + "\n")


print("=" * 72)
print("CRYPTOMASTERX1 — 11-PHASE SOURCE RECOVERY")
print("=" * 72)
print()
print("Project:", ROOT)
print("Output :", OUT)
print("Python :", sys.version)
print()

found_source = []
found_pyc = []

for name in PHASES:
    print("-" * 72)
    print(name)

    sources = find_sources(name)

    if sources:
        print("SOURCE FOUND:")

        # Select the most useful source:
        # Prefer active project source over archive when possible.
        sources_sorted = sorted(
            sources,
            key=lambda p: (
                "archive" in p.parts,
                len(p.parts),
                str(p)
            )
        )

        selected = sources_sorted[0]
        destination = OUT / (name + ".py")

        shutil.copy2(selected, destination)

        print("  ", selected)
        print(" ->", destination)

        found_source.append((name, selected, destination))

    pycs = find_pyc(name)

    if pycs:
        print("PYC FOUND:")

        for pyc in pycs:
            print("  ", pyc)
            found_pyc.append((name, pyc))

            # Preserve a copy of the bytecode.
            pyc_out = OUT / (pyc.name)
            if not pyc_out.exists():
                shutil.copy2(pyc, pyc_out)

            # Produce readable disassembly.
            safe_name = str(pyc).replace("/", "_").replace("\\", "_")
            txt_out = OUT / (safe_name + ".dis.txt")

            try:
                write_disassembly(pyc, txt_out)
                print(" -> DIS:", txt_out)
            except Exception as exc:
                print(" -> DISASSEMBLY ERROR:", exc)

    if not sources and not pycs:
        print("NOT FOUND")


print()
print("=" * 72)
print("RECOVERY SUMMARY")
print("=" * 72)

print()
print("Actual .py source recovered:", len(found_source))
for name, src, dst in found_source:
    print("  [SOURCE] ", name)
    print("           ", src)

print()
print("Compiled .pyc modules found:", len(found_pyc))
for name, pyc in found_pyc:
    print("  [PYC]    ", name)
    print("           ", pyc)

print()
print("Recovered files are in:")
print(OUT)

print()
print("=" * 72)
print("PHASE STATUS")
print("=" * 72)

for name in PHASES:
    source = OUT / (name + ".py")
    pyc = list(OUT.glob(name + "*.pyc"))

    if source.exists():
        status = "SOURCE RECOVERED"
    elif pyc:
        status = "BYTECODE RECOVERED / DISASSEMBLED"
    else:
        status = "MISSING"

    print(f"{name:40} {status}")

print()
print("=" * 72)
print("DONE")
print("=" * 72)
