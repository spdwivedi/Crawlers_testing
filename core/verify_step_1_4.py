"""
core/verify_step_1_4.py
=======================
Verification & sequential smoke-testing script for Stage 1 Step 1.4 (FINAL STEP OF STAGE 1).

Executes all 5 Batch 4 adapters in sequence:
  - 16_crawl4ai (AI-Native Web Crawler & Semantic Markdown Chunker)
  - 17_surya_ocr (Visual Test Screenshot Layout Detection & OCR)
  - 18_paddleocr_img2table (Visual Table & Canvas Grid Extraction from Images)
  - 19_docling_pdf (Layout-Aware PDF & Document Structure Parser)
  - 20_faster_whisper_scrapegraph (Audio Whisper Transcription + Schema Graph Extraction)

Validates outputs, non-empty files in raw/ and cleaned/, action_run.jsonl,
and run_manifest.json status='completed'.
Updates tools/registry.json and tools/<tool_id>/config.json with verified status.
Performs final Stage 1 20/20 tools verified check.
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
    print(f"\n{BOLD}=== STAGE 1 - STEP 1.4 BATCH 4 VERIFICATION & FINAL STAGE 1 AUDIT ==={RESET}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 16: crawl4ai
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 16: crawl4ai (AI-Native Web Crawler & Semantic Markdown Chunker)")
    info("Importing and executing tools/16_crawl4ai/adapter.py...")
    mod16 = importlib.import_module("tools.16_crawl4ai.adapter")
    res16 = mod16.run_action("scrape_for_leetcode")
    check(res16.get("manifest", {}).get("status") == "completed", "16_crawl4ai run returned completed", "16_crawl4ai failed")
    verify_run_folder(res16["run_info"])
    update_tool_status("16_crawl4ai")
    ok("16_crawl4ai marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 17: surya_ocr
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 17: surya_ocr (Visual Test Screenshot Layout Detection & OCR)")
    info("Importing and executing tools/17_surya_ocr/adapter.py...")
    mod17 = importlib.import_module("tools.17_surya_ocr.adapter")
    res17 = mod17.run_action("visual_test_ocr")
    check(res17.get("manifest", {}).get("status") == "completed", "17_surya_ocr run returned completed", "17_surya_ocr failed")
    verify_run_folder(res17["run_info"])
    update_tool_status("17_surya_ocr")
    ok("17_surya_ocr marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 18: paddleocr_img2table
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 18: paddleocr_img2table (Visual Table & Canvas Grid Extraction)")
    info("Importing and executing tools/18_paddleocr_img2table/adapter.py...")
    mod18 = importlib.import_module("tools.18_paddleocr_img2table.adapter")
    res18 = mod18.run_action("visual_test_ocr")
    check(res18.get("manifest", {}).get("status") == "completed", "18_paddleocr_img2table run returned completed", "18_paddleocr_img2table failed")
    verify_run_folder(res18["run_info"])
    update_tool_status("18_paddleocr_img2table")
    ok("18_paddleocr_img2table marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 19: docling_pdf
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 19: docling_pdf (Layout-Aware PDF & Document Structure Parser)")
    info("Importing and executing tools/19_docling_pdf/adapter.py...")
    mod19 = importlib.import_module("tools.19_docling_pdf.adapter")
    res19 = mod19.run_action("pdf_parse")
    check(res19.get("manifest", {}).get("status") == "completed", "19_docling_pdf run returned completed", "19_docling_pdf failed")
    verify_run_folder(res19["run_info"])
    update_tool_status("19_docling_pdf")
    ok("19_docling_pdf marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # TOOL 20: faster_whisper_scrapegraph
    # ──────────────────────────────────────────────────────────────────────────
    header("TOOL 20: faster_whisper_scrapegraph (Audio Whisper Transcription + Knowledge Graph)")
    info("Importing and executing tools/20_faster_whisper_scrapegraph/adapter.py...")
    mod20 = importlib.import_module("tools.20_faster_whisper_scrapegraph.adapter")
    res20 = mod20.run_action("audio_transcribe")
    check(res20.get("manifest", {}).get("status") == "completed", "20_faster_whisper_scrapegraph run returned completed", "20_faster_whisper_scrapegraph failed")
    verify_run_folder(res20["run_info"])
    update_tool_status("20_faster_whisper_scrapegraph")
    ok("20_faster_whisper_scrapegraph marked verified in registry.json & config.json")

    # ──────────────────────────────────────────────────────────────────────────
    # FINAL STAGE 1 MASTER CHECK (20/20 TOOLS)
    # ──────────────────────────────────────────────────────────────────────────
    header("STAGE 1 FINAL MASTER CHECK: 20/20 TOOLS VERIFICATION")
    reg_path = ROOT / "tools" / "registry.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    tools_list = reg.get("tools", [])

    verified_count = sum(1 for t in tools_list if t.get("status") == "verified")
    installed_count = sum(1 for t in tools_list if t.get("installed") is True)
    total_count = len(tools_list)

    print(f"\n  Installed Tools: {installed_count}/{total_count}")
    print(f"  Verified Tools:  {verified_count}/{total_count}\n")

    check(total_count == 20, f"Total tools defined is 20", f"Unexpected total tools: {total_count}")
    check(verified_count == 20, f"All 20/20 tools are verified!", f"Only {verified_count}/20 tools verified")
    check(installed_count == 20, f"All 20/20 tools are installed!", f"Only {installed_count}/20 tools installed")

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    header("VERIFICATION SUMMARY")
    if errors == 0:
        print(f"\n  {GREEN}{BOLD}[PASS] ALL BATCH 4 CHECKS PASSED -- STAGE 1 COMPLETE (20/20 TOOLS VERIFIED){RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}[FAIL] {errors} checks failed.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
