#!/usr/bin/env python3
"""
Master Test Runner — 一键全量验证
==================================
Runs all validation, compliance, robustness, and benchmark tests
in a single command.

Usage:
  python scripts/run_all.py              # everything
  python scripts/run_all.py --quick      # skip robustness (faster)
  python scripts/run_all.py --ci         # CI mode (exit code)
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/Reasonix")
SCRIPTS = ROOT / "scripts"

TESTS = [
    {
        "name": "Cross-Project Validation",
        "script": "validate_cross_project.py",
        "args": ["--ci"],
        "quick": False,
    },
    {
        "name": "Rule Compliance Check",
        "script": "check_rules.py",
        "args": ["--ci"],
        "quick": False,
    },
    {
        "name": "Robustness & Boundary Tests",
        "script": "test_robustness.py",
        "args": [],
        "quick": True,   # skip in --quick mode
    },
    {
        "name": "Benchmark",
        "script": "benchmark.py",
        "args": ["--quick"],
        "quick": False,
    },
]


def run_test(name: str, script: str, args: list[str]) -> tuple[bool, float, str]:
    """Run a single test script. Returns (passed, elapsed_sec, output)."""
    path = SCRIPTS / script
    if not path.exists():
        return False, 0, f"Script not found: {path}"
    
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, str(path)] + args,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        elapsed = time.perf_counter() - start
        passed = result.returncode == 0
        output = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
        if result.stderr.strip():
            output += "\n[stderr]: " + result.stderr.strip()[-200:]
        return passed, elapsed, output
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return False, elapsed, "TIMEOUT (>60s)"
    except Exception as e:
        elapsed = time.perf_counter() - start
        return False, elapsed, str(e)


def main():
    quick = "--quick" in sys.argv
    ci_mode = "--ci" in sys.argv
    
    print("═" * 60)
    print(f"  🧠 S-T-V Master Test Suite")
    print(f"  {datetime.now().isoformat()[:19]}")
    print(f"  Mode: {'quick' if quick else 'full'}")
    print("═" * 60)
    print()
    
    total = 0
    passed = 0
    failed = 0
    total_time = 0
    
    for test in TESTS:
        if quick and test.get("quick"):
            print(f"  ⏭  {test['name']} (skipped in quick mode)")
            continue
        
        print(f"  ⏳ {test['name']}...", end=" ", flush=True)
        ok, elapsed, output = run_test(test["name"], test["script"], test["args"])
        total += 1
        total_time += elapsed
        
        if ok:
            passed += 1
            print(f"✅ {elapsed:.1f}s")
        else:
            failed += 1
            print(f"❌ {elapsed:.1f}s")
            if output:
                # Show last relevant lines
                lines = output.strip().splitlines()
                for line in lines[-3:]:
                    print(f"     {line[:100]}")
    
    print()
    print("═" * 60)
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print(f"  Duration: {total_time:.1f}s")
    print("═" * 60)
    
    if ci_mode:
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
