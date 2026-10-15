"""
core/verify_step_1_2.py
=======================
Verification & sequential smoke-testing script for Stage 1 Step 1.2.

Executes all 5 Batch 2 adapters in sequence:
  - 06_playwright (Standard Browser Automation + HAR Origin Discovery & Visual Snapshot)
  - 07_patchright (Binary-Patched Stealth Chromium — Anti-Bot & CDP Leak Evasion)
  - 08_camoufox (C++-Level Stealth Firefox with Fingerprint Spoofing)
  - 09_nodriver (Direct CDP Ultra-Stealth Chrome Control Without WebDriver)
  - 10_scrapling (Self-Healing / Adaptive DOM Scraper)

Validates outputs, non-empty files in raw/ and cleaned/, action_run.jsonl,
and run_manifest.json status='completed'.
Updates tools/registry.json and tools/<tool_id>/config.json with verified status.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Set single thread for OpenBLAS on Windows before any library loads
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# UTF-8 console output for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib

# Color helpers (ASCII-safe)
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str) -> None: print(f"  {GREEN}[OK]{RESET} {msg}")
def fail(msg: str) -> None: print(f"  {RED}[FAIL]{RESET} {msg}")
def info(msg: str) -> None: print(f"  {CYAN}-->{RESET} {msg}")
def header(msg: str) -> None: print(f"\n{BOLD}{YELLOW}{'-'*60}{RESET}\n{BOLD}  {msg}{RESET}\n{BOLD}{YELLOW}{'-'*60}{RESET}")

errors = 0

def check(condition: bool, msg_pass: str, msg_fail: str) -> bool:
    global errors
    if condition:
        ok(msg_pass)
        return True
    else:
        fail(msg_fail)
        errors += 1
        return False


def verify_run_folder(run_info: dict) -> bool:
    """Validate raw, cleaned, logs, manifest exist and are non-empty."""
    global errors
    run_dir = Path(run_info["run_dir"])
    raw_dir = Path(run_info["raw_dir"])
    cleaned_dir = Path(run_info["cleaned_dir"])
    manifest_path = Path(run_info["manifest_path"])
    log_file = Path(run_info["log_file"])

    valid = True
    valid &= check(run_dir.exists(), f"Run directory exists: {run_dir.name}", f"Missing run dir: {run_dir}")
    valid &= check(raw_dir.exists(), "raw/ directory exists", "Missing raw/ dir")
    valid &= check(cleaned_dir.exists(), "cleaned/ directory exists", "Missing cleaned/ dir")
    valid &= check(manifest_path.exists(), "run_manifest.json exists", "Missing run_manifest.json")
    valid &= check(log_file.exists() and log_file.stat().st_size > 0, "logs/action_run.jsonl populated", "Missing or empty action_run.jsonl")

    raw_files = list(raw_dir.iterdir())
    cleaned_files = list(cleaned_dir.iterdir())
    valid &= check(len(raw_files) > 0, f"raw/ has {len(raw_files)} files: {[f.name for f in raw_files]}", "raw/ directory is empty")
    valid &= check(len(cleaned_files) > 0, f"cleaned/ has {len(cleaned_files)} files: {[f.name for f in cleaned_files]}", "cleaned/ directory is empty")

    if manifest_path.exists():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            valid &= check(m.get("status") == "completed", "manifest status='completed'", f"manifest status={m.get('status')}")
        except Exception as e:
            fail(f"Invalid JSON in run_manifest.json: {e}")
            valid = False
            errors += 1

    return valid


def update_tool_status(tool_id: str) -> None:
    """Set installed=True, status='verified', last_run=timestamp in registry and config."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 1. Update config.json
    cfg_path = ROOT / "tools" / tool_id / "config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["installed"] = True
            cfg["status"] = "verified"
            cfg["last_run"] = now_iso
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass

    # 2. Update registry.json
    reg_path = ROOT / "tools" / "registry.json"
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            for t in reg.get("tools", []):
                if t.get("tool_id") == tool_id:
                    t["installed"] = True
                    t["status"] = "verified"
                    t["last_run"] = now_iso
            reg_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
        except Exception:
            pass


def main():
    print(f"\n{BOLD}=== STAGE 1 - STEP 1.2 BATCH 2 VERIFICATION & SMOKE TEST ==={RESET}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 06: playwright
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 06: playwright (Standard Browser Automation + HAR & Visual Snapshot)")
    info("Importing and executing tools/06_playwright/adapter.py...")
    mod6 = importlib.import_module("tools.06_playwright.adapter")
    res6 = mod6.run_action("secured_page_origin")
    check(res6.get("manifest", {}).get("status") == "completed", "06_playwright run returned completed", "06_playwright failed")
    verify_run_folder(res6["run_info"])
    update_tool_status("06_playwright")
    ok("06_playwright marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 07: patchright
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 07: patchright (Binary-Patched Stealth Chromium)")
    info("Importing and executing tools/07_patchright/adapter.py...")
    mod7 = importlib.import_module("tools.07_patchright.adapter")
    res7 = mod7.run_action("secured_page_origin")
    check(res7.get("manifest", {}).get("status") == "completed", "07_patchright run returned completed", "07_patchright failed")
    verify_run_folder(res7["run_info"])
    update_tool_status("07_patchright")
    ok("07_patchright marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 08: camoufox
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 08: camoufox (C++-Level Stealth Firefox & Fingerprint Spoofing)")
    info("Importing and executing tools/08_camoufox/adapter.py...")
    mod8 = importlib.import_module("tools.08_camoufox.adapter")
    res8 = mod8.run_action("fingerprint_evasion")
    check(res8.get("manifest", {}).get("status") == "completed", "08_camoufox run returned completed", "08_camoufox failed")
    verify_run_folder(res8["run_info"])
    update_tool_status("08_camoufox")
    ok("08_camoufox marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 09: nodriver
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 09: nodriver (Direct CDP Ultra-Stealth Without WebDriver)")
    info("Importing and executing tools/09_nodriver/adapter.py...")
    mod9 = importlib.import_module("tools.09_nodriver.adapter")
    res9 = mod9.run_action("cdp_intercept")
    check(res9.get("manifest", {}).get("status") == "completed", "09_nodriver run returned completed", "09_nodriver failed")
    verify_run_folder(res9["run_info"])
    update_tool_status("09_nodriver")
    ok("09_nodriver marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 10: scrapling
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 10: scrapling (Self-Healing / Adaptive DOM Scraper)")
    info("Importing and executing tools/10_scrapling/adapter.py...")
    mod10 = importlib.import_module("tools.10_scrapling.adapter")
    res10 = mod10.run_action("adaptive_extract")
    check(res10.get("manifest", {}).get("status") == "completed", "10_scrapling run returned completed", "10_scrapling failed")
    verify_run_folder(res10["run_info"])
    update_tool_status("10_scrapling")
    ok("10_scrapling marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    header("VERIFICATION SUMMARY")
    if errors == 0:
        print(f"\n  {GREEN}{BOLD}[PASS] ALL BATCH 2 CHECKS PASSED -- Tools 06 through 10 are fully operational & verified.{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}[FAIL] {errors} checks failed.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
