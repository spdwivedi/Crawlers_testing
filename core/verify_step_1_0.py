"""
core/verify_step_1_0.py
=======================
Verification script for Stage 1 Step 1.0.

Runs a 5-step simulation flow through state_tracker, folder_manager,
and logger_engine. Validates all 20 tool directories, registry.json,
GEMINI.md, and governance rule files exist.

Usage:
  python core/verify_step_1_0.py
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ─── Color helpers (ASCII-safe) ───────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg:  str) -> None: print(f"  {GREEN}[OK]{RESET} {msg}")
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


# ─── Step 1: Governance files ─────────────────────────────────────────────────
header("STEP 1 — Governance & Git Files")

files_to_check = [
    ROOT / ".gitignore",
    ROOT / "GEMINI.md",
    ROOT / ".agents" / "rules" / "antigravity_governance.md",
    ROOT / ".agent"  / "rules" / "antigravity_governance.md",
    ROOT / "tools" / "registry.json",
]
for f in files_to_check:
    check(f.exists(), f"Found: {f.relative_to(ROOT)}", f"MISSING: {f.relative_to(ROOT)}")


# ─── Step 2: Core engine modules ─────────────────────────────────────────────
header("STEP 2 — Core Engine Modules")

core_files = [
    ROOT / "core" / "folder_manager.py",
    ROOT / "core" / "state_tracker.py",
    ROOT / "core" / "cli_tracker.py",
    ROOT / "core" / "logger_engine.py",
    ROOT / "core" / "git_manager.py",
]
for f in core_files:
    check(f.exists(), f"Found: {f.relative_to(ROOT)}", f"MISSING: {f.relative_to(ROOT)}")


# ─── Step 3: 20-tool directories ─────────────────────────────────────────────
header("STEP 3 — 20-Tool Directory Scaffold")

TOOL_IDS = [
    "01_curl_cffi", "02_selectolax_lxml", "03_scrapy",
    "04_httpx_parsel", "05_trafilatura",
    "06_playwright", "07_patchright", "08_camoufox",
    "09_nodriver", "10_scrapling",
    "11_yt_dlp_ffmpeg", "12_instaloader", "13_gallery_dl",
    "14_singlefile_archive", "15_mitmproxy_interceptor",
    "16_crawl4ai", "17_surya_ocr", "18_paddleocr_img2table",
    "19_docling_pdf", "20_faster_whisper_scrapegraph",
]

for tid in TOOL_IDS:
    tool_dir = ROOT / "tools" / tid
    data_dir = ROOT / "data" / tid
    config   = tool_dir / "config.json"
    stub     = tool_dir / "adapter_stub.py"
    tool_log = tool_dir / "logs" / "tool_ops.jsonl"

    all_ok = all([tool_dir.exists(), data_dir.exists(), config.exists(), stub.exists(), tool_log.exists()])
    check(all_ok, f"{tid} — all files present", f"{tid} — INCOMPLETE scaffold")


# ─── Step 4: Simulate state tracker flow ─────────────────────────────────────
header("STEP 4 — State Tracker Simulation (5 Steps)")

try:
    from core.state_tracker import (
        start_task, update_progress, complete_task, read_state
    )

    start_task(
        stage="Stage 1",
        step="Step 1.0",
        tool_id="01_curl_cffi",
        action="system_scaffold_check",
        subtask="Verify: initializing state tracker",
    )
    state = read_state()
    check(state["is_running"], "state_tracker: is_running=True after start", "state_tracker: start failed")
    check(state["current_stage"] == "Stage 1", "state_tracker: stage set correctly", "stage mismatch")

    for i, (pct, subtask) in enumerate([
        (20, "Verify: checking tool directories"),
        (40, "Verify: running folder_manager"),
        (60, "Verify: testing logger_engine"),
        (80, "Verify: validating registry.json"),
    ], 1):
        update_progress(pct, subtask=subtask)
        state = read_state()
        check(state["progress_percent"] == pct, f"Step {i}: progress={pct}%", f"Step {i}: progress mismatch")
        info(f"Subtask: {subtask}")
        time.sleep(0.1)

    ok("State tracker simulation: 5 steps completed")

except Exception as e:
    fail(f"State tracker simulation failed: {e}")
    errors += 1


# ─── Step 5: Folder Manager dry-run ──────────────────────────────────────────
header("STEP 5 — Folder Manager Dry-Run")

try:
    from core.folder_manager import create_action_run, complete_action_run
    from core.logger_engine import LogEngine

    run_info = create_action_run(
        tool_id="01_curl_cffi",
        action_name="system_scaffold_check",
        target_url="https://verify.step.1.0",
    )
    info(f"Created run: {run_info['run_id']}")

    run_dir = Path(run_info["run_dir"])
    check(run_dir.exists(), "run_dir created", "run_dir missing")
    check((run_dir / "raw").exists(), "raw/ dir created", "raw/ missing")
    check((run_dir / "cleaned").exists(), "cleaned/ dir created", "cleaned/ missing")
    check((run_dir / "logs").exists(), "logs/ dir created", "logs/ missing")
    check((run_dir / "run_manifest.json").exists(), "run_manifest.json created", "run_manifest.json missing")

    # Write a sample raw file
    sample_raw = run_dir / "raw" / "verify_output.txt"
    sample_raw.write_text("Stage 1 Step 1.0 verification dry-run output.\n", encoding="utf-8")
    check(sample_raw.exists(), "Sample raw file written", "Raw file write failed")

    # Test logger engine
    log_engine = LogEngine(
        tool_id="01_curl_cffi",
        action_name="system_scaffold_check",
        run_id=run_info["run_id"],
        run_log_path=Path(run_info["log_file"]),
        stage="Stage 1",
        step="Step 1.0",
        stage_log_name="stage_1_scaffolding",
    )
    log_engine.info("Verification dry-run: 4-tier logger test", progress_pct=95)
    log_engine.warn("This is a test WARN entry")
    check((run_dir / "logs" / "action_run.jsonl").exists(), "action_run.jsonl written (Tier 1)", "Tier 1 log missing")
    check((ROOT / "tools" / "01_curl_cffi" / "logs" / "tool_ops.jsonl").stat().st_size > 0, "tool_ops.jsonl populated (Tier 2)", "Tier 2 log empty")
    check((ROOT / "logs" / "stages" / "stage_1_scaffolding.jsonl").exists(), "stage_1_scaffolding.jsonl written (Tier 3)", "Tier 3 log missing")
    check((ROOT / "logs" / "global" / "antigravity_prompt_log.jsonl").exists(), "antigravity_prompt_log.jsonl written (Tier 4 JSONL)", "Tier 4 JSONL missing")
    check((ROOT / "logs" / "global" / "antigravity_prompt_log.md").exists(), "antigravity_prompt_log.md written (Tier 4 MD)", "Tier 4 MD missing")

    complete_action_run(run_info, status="completed")

    # Confirm manifest updated
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    check(manifest["status"] == "completed", "run_manifest.json status=completed", "run_manifest not updated")

    update_progress(100, subtask="Verify: all checks complete")
    from core.state_tracker import complete_task as ct
    ct("Stage 1 Step 1.0 verification PASSED")

except Exception as e:
    import traceback
    fail(f"Folder manager / logger test failed: {e}")
    traceback.print_exc()
    errors += 1


# ─── Registry validation ──────────────────────────────────────────────────────
header("Registry.json Validation")

try:
    registry = json.loads((ROOT / "tools" / "registry.json").read_text(encoding="utf-8"))
    tools = registry.get("tools", [])
    check(len(tools) == 20, f"registry.json has 20 tools ({len(tools)} found)", f"registry.json tool count wrong: {len(tools)}")

    required_keys = {"tool_id", "name", "batch", "mechanism_type", "supported_actions", "installed", "status", "last_run"}
    for t in tools:
        missing = required_keys - set(t.keys())
        if missing:
            fail(f"Tool {t.get('tool_id')} missing keys: {missing}")
            errors += 1

    if errors == 0:
        ok("All registry.json tool entries have required keys")
except Exception as e:
    fail(f"Registry validation failed: {e}")
    errors += 1


# --- Final Summary ---───────────────
header("VERIFICATION SUMMARY")

if errors == 0:
    print(f"\n  {GREEN}{BOLD}✓ ALL CHECKS PASSED — Stage 1 Step 1.0 scaffold is complete and healthy.{RESET}\n")
    sys.exit(0)
else:
    print(f"\n  {RED}{BOLD}✗ {errors} CHECK(S) FAILED — Review output above.{RESET}\n")
    sys.exit(1)
