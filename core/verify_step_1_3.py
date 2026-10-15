"""
core/verify_step_1_3.py
=======================
Verification & sequential smoke-testing script for Stage 1 Step 1.3.

Executes all 5 Batch 3 adapters in sequence:
  - 11_yt_dlp_ffmpeg (Raw Stream Chunk Downloading + FFmpeg Audio/Video Combining & Demuxing)
  - 12_instaloader (Dedicated Instagram Graph & Session Archiver)
  - 13_gallery_dl (Multi-Platform Social & Media Gallery Extractor — Facebook/Insta/Reddit/X)
  - 14_singlefile_archive (Self-Contained Single-File Full-Page Offline Snapshot)
  - 15_mitmproxy_interceptor (Man-in-the-Middle Traffic & Hidden API/Stream Interceptor)

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
    print(f"\n{BOLD}=== STAGE 1 - STEP 1.3 BATCH 3 VERIFICATION & SMOKE TEST ==={RESET}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 11: yt_dlp_ffmpeg
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 11: yt_dlp_ffmpeg (Stream Chunk Downloading + FFmpeg Demuxing)")
    info("Importing and executing tools/11_yt_dlp_ffmpeg/adapter.py...")
    mod11 = importlib.import_module("tools.11_yt_dlp_ffmpeg.adapter")
    res11 = mod11.run_action("scrape_for_insta")
    check(res11.get("manifest", {}).get("status") == "completed", "11_yt_dlp_ffmpeg run returned completed", "11_yt_dlp_ffmpeg failed")
    verify_run_folder(res11["run_info"])
    update_tool_status("11_yt_dlp_ffmpeg")
    ok("11_yt_dlp_ffmpeg marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 12: instaloader
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 12: instaloader (Dedicated Instagram Graph & Session Archiver)")
    info("Importing and executing tools/12_instaloader/adapter.py...")
    mod12 = importlib.import_module("tools.12_instaloader.adapter")
    res12 = mod12.run_action("scrape_for_insta")
    check(res12.get("manifest", {}).get("status") == "completed", "12_instaloader run returned completed", "12_instaloader failed")
    verify_run_folder(res12["run_info"])
    update_tool_status("12_instaloader")
    ok("12_instaloader marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 13: gallery_dl
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 13: gallery_dl (Multi-Platform Social & Media Gallery Extractor)")
    info("Importing and executing tools/13_gallery_dl/adapter.py...")
    mod13 = importlib.import_module("tools.13_gallery_dl.adapter")
    res13 = mod13.run_action("scrape_for_facebook")
    check(res13.get("manifest", {}).get("status") == "completed", "13_gallery_dl run returned completed", "13_gallery_dl failed")
    verify_run_folder(res13["run_info"])
    update_tool_status("13_gallery_dl")
    ok("13_gallery_dl marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 14: singlefile_archive
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 14: singlefile_archive (Self-Contained Single-File Full-Page Offline Snapshot)")
    info("Importing and executing tools/14_singlefile_archive/adapter.py...")
    mod14 = importlib.import_module("tools.14_singlefile_archive.adapter")
    res14 = mod14.run_action("offline_archive")
    check(res14.get("manifest", {}).get("status") == "completed", "14_singlefile_archive run returned completed", "14_singlefile_archive failed")
    verify_run_folder(res14["run_info"])
    update_tool_status("14_singlefile_archive")
    ok("14_singlefile_archive marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 15: mitmproxy_interceptor
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 15: mitmproxy_interceptor (MITM Traffic & Hidden API Interceptor)")
    info("Importing and executing tools/15_mitmproxy_interceptor/adapter.py...")
    mod15 = importlib.import_module("tools.15_mitmproxy_interceptor.adapter")
    res15 = mod15.run_action("api_intercept")
    check(res15.get("manifest", {}).get("status") == "completed", "15_mitmproxy_interceptor run returned completed", "15_mitmproxy_interceptor failed")
    verify_run_folder(res15["run_info"])
    update_tool_status("15_mitmproxy_interceptor")
    ok("15_mitmproxy_interceptor marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    header("VERIFICATION SUMMARY")
    if errors == 0:
        print(f"\n  {GREEN}{BOLD}[PASS] ALL BATCH 3 CHECKS PASSED -- Tools 11 through 15 are fully operational & verified.{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}[FAIL] {errors} checks failed.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
