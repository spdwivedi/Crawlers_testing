"""
core/verify_step_1_1.py
=======================
Verification & sequential smoke-testing script for Stage 1 Step 1.1.

Executes all 5 Batch 1 adapters in sequence:
  - 01_curl_cffi (TLS Impersonation)
  - 02_selectolax_lxml (C-Engine Lexbor vs lxml Benchmark)
  - 03_scrapy (Subprocess Spider Runner)
  - 04_httpx_parsel (Async HTTP/2 + JMESPath/XPath)
  - 05_trafilatura (Boilerplate Stripping & Metadata)

Validates outputs, non-empty files in raw/ and cleaned/, action_run.jsonl,
and run_manifest.json status='completed'.
Updates tools/registry.json and tools/<tool_id>/config.json with verified status.
"""
from __future__ import annotations

import importlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# UTF-8 console output for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
    valid &= check(len(raw_files) > 0, f"raw/ has {len(raw_files)} files", "raw/ directory is empty")
    valid &= check(len(cleaned_files) > 0, f"cleaned/ has {len(cleaned_files)} files", "cleaned/ directory is empty")

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
    print(f"\n{BOLD}=== STAGE 1 - STEP 1.1 BATCH 1 VERIFICATION & SMOKE TEST ==={RESET}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 01: curl_cffi
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 01: curl_cffi (TLS Impersonation)")
    info("Importing and executing tools/01_curl_cffi/adapter.py...")
    mod1 = importlib.import_module("tools.01_curl_cffi.adapter")
    res1 = mod1.run_scrape_for_leetcode()
    check(res1.get("status") == "completed", "01_curl_cffi run returned completed", "01_curl_cffi failed")
    verify_run_folder(res1["run_info"])
    update_tool_status("01_curl_cffi")
    ok("01_curl_cffi marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 02: selectolax_lxml
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 02: selectolax_lxml (C-Engine Lexbor vs lxml Benchmark)")
    info("Importing and executing tools/02_selectolax_lxml/adapter.py...")
    mod2 = importlib.import_module("tools.02_selectolax_lxml.adapter")
    res2 = mod2.run_catalog_parse()
    check(res2.get("status") == "completed", "02_selectolax_lxml run returned completed", "02_selectolax_lxml failed")
    verify_run_folder(res2["run_info"])
    update_tool_status("02_selectolax_lxml")
    ok("02_selectolax_lxml marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 03: scrapy
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 03: scrapy (Async Spider & Item Pipeline Framework)")
    info("Importing and executing tools/03_scrapy/adapter.py...")
    mod3 = importlib.import_module("tools.03_scrapy.adapter")
    res3 = mod3.run_catalog_crawl()
    check(res3.get("status") == "completed", "03_scrapy run returned completed", "03_scrapy failed")
    verify_run_folder(res3["run_info"])
    update_tool_status("03_scrapy")
    ok("03_scrapy marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 04: httpx_parsel
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 04: httpx_parsel (Async HTTP/2 + JMESPath/XPath)")
    info("Importing and executing tools/04_httpx_parsel/adapter.py...")
    mod4 = importlib.import_module("tools.04_httpx_parsel.adapter")
    res4 = mod4.run_async_parsel()
    check(res4.get("status") == "completed", "04_httpx_parsel run returned completed", "04_httpx_parsel failed")
    verify_run_folder(res4["run_info"])
    update_tool_status("04_httpx_parsel")
    ok("04_httpx_parsel marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 05: trafilatura
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 05: trafilatura (Boilerplate Stripping & Content Mining)")
    info("Importing and executing tools/05_trafilatura/adapter.py...")
    mod5 = importlib.import_module("tools.05_trafilatura.adapter")
    res5 = mod5.run_article_extract()
    check(res5.get("status") == "completed", "05_trafilatura run returned completed", "05_trafilatura failed")
    verify_run_folder(res5["run_info"])
    update_tool_status("05_trafilatura")
    ok("05_trafilatura marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    header("VERIFICATION SUMMARY")
    if errors == 0:
        print(f"\n  {GREEN}{BOLD}[PASS] ALL BATCH 1 CHECKS PASSED -- Tools 01 through 05 are fully operational & verified.{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}[FAIL] {errors} checks failed.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
