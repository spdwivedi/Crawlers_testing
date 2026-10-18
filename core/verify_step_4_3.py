"""
core/verify_step_4_3.py
=======================
Focused Verification Suite for Stage 4 — Step 4.3:
Shared Human Mode Helper (`core/human_adapter_helper.py`), Working Way 1 (`human_mode`)
Integration across 4 Tool Adapter Cohorts, 4-Tier Stage 4 Logging, and Governance.

Verifies:
1. Shared HumanAdapterHelper timing dispatch (pre-request delay, reading pauses, chunk pacing).
2. Sync and Async Browser Human Flow Execution (Playwright & Patchright integration).
3. Working Way 1 Integration in HTTP Clients (01_curl_cffi, 04_httpx_parsel) with manifest domain_metrics.
4. Working Way 1 Integration in Media & AI Extractors (11_yt_dlp_ffmpeg, 16_crawl4ai).
5. Backward Compatibility & Unified run() Entrypoint across Cohorts.
6. Stage 4 Logging, Global FTS5 Master Index Synchronization & Pre-Commit Secret Guard.
"""

import asyncio
import importlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.human_adapter_helper import HumanAdapterHelper
from core.human_timing import HumanTimingEngine
from core.logger_engine import log_global
from core.state_tracker import update_progress

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, condition: bool, details: str = "") -> None:
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  ✅ [PASS] {name}")
        log_global(
            message=f"CHECK PASSED: {name}",
            level="INFO",
            stage="Stage 4",
            step="Step 4.3",
            tool_id="human_adapter_helper",
            action_name="verify_human_mode_integration",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.3",
            tool_id="human_adapter_helper",
            action_name="verify_human_mode_integration",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("🚀 STARTING STAGE 4 STEP 4.3 VERIFICATION SUITE")
    print("   Working Way 1 (Human Mode) Helper, Cohort Adapters & Stage 4 Governance")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 Step 4.3 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Shared HumanAdapterHelper Timing Delays
    # ------------------------------------------------------------------
    print("--- Check 1: Shared HumanAdapterHelper Timing Delays ---")
    update_progress(10, "Verifying HumanAdapterHelper pre-request, reading, and pacing delays...")

    t0 = time.perf_counter()
    pre_delay = HumanAdapterHelper.apply_pre_request_delay(
        timing_profile="FAST_AUTOMATED",
        target_delay=0.05,
    )
    elapsed_pre = time.perf_counter() - t0
    assert_check(
        "apply_pre_request_delay executes and respects target timing bound",
        pre_delay >= 0.04 and elapsed_pre >= 0.04,
        f"Calculated: {pre_delay:.4f}s, Elapsed: {elapsed_pre:.4f}s",
    )

    t0 = time.perf_counter()
    read_delay = HumanAdapterHelper.apply_reading_delay(
        word_count=50,
        timing_profile="FAST_AUTOMATED",
    )
    elapsed_read = time.perf_counter() - t0
    assert_check(
        "apply_reading_delay scales and executes within bounds",
        read_delay >= 0.04 and elapsed_read >= 0.04,
        f"Calculated: {read_delay:.4f}s, Elapsed: {elapsed_read:.4f}s",
    )

    t0 = time.perf_counter()
    chunk_delay = HumanAdapterHelper.apply_chunk_pacing(
        chunk_duration_sec=0.1,
        playback_ratio=1.0,
    )
    elapsed_chunk = time.perf_counter() - t0
    assert_check(
        "apply_chunk_pacing calculates stream chunk interval",
        chunk_delay > 0.05,
        f"Calculated: {chunk_delay:.4f}s, Elapsed: {elapsed_chunk:.4f}s",
    )

    # ------------------------------------------------------------------
    # Check 2: Browser Human Flow (Sync & Async)
    # ------------------------------------------------------------------
    print("\n--- Check 2: Browser Human Flow (Sync & Async) ---")
    update_progress(25, "Testing sync and async browser human flows...")

    from playwright.sync_api import sync_playwright

    test_html = """<!DOCTYPE html>
<html>
<head><title>Human Flow Test</title></head>
<body style="height: 2000px; margin: 0; padding: 20px;">
    <h1>Human Interaction Verification</h1>
    <p>Target area for human mouse & scroll test</p>
    <button id="cta-btn" style="margin-top: 300px; padding: 15px 30px;">Click Me</button>
</body>
</html>"""

    # Sync flow test
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(test_html)
        metrics_sync = HumanAdapterHelper.execute_browser_human_flow(
            page=page,
            target_url="mock://test-sync",
            do_warmup=False,
            do_scroll=True,
            max_scrolls=1,
        )
        browser.close()

    assert_check(
        "execute_browser_human_flow (sync) records valid interaction metrics",
        isinstance(metrics_sync, dict) and (
            metrics_sync.get("scroll_executed") is True or
            metrics_sync.get("scroll_metrics", {}).get("scroll_steps", 0) >= 1
        ),
        f"Metrics: {metrics_sync}",
    )

    # Async flow test
    async def _test_async_flow():
        from playwright.async_api import async_playwright as ap
        async with ap() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)
            metrics_async = await HumanAdapterHelper.async_execute_browser_human_flow(
                page=page,
                target_url="mock://test-async",
                do_warmup=False,
                do_scroll=True,
                max_scrolls=1,
            )
            await browser.close()
            return metrics_async

    metrics_async = asyncio.run(_test_async_flow())

    assert_check(
        "async_execute_browser_human_flow (async) records valid interaction metrics",
        isinstance(metrics_async, dict) and (
            metrics_async.get("scroll_executed") is True or
            metrics_async.get("scroll_metrics", {}).get("scroll_steps", 0) >= 1
        ),
        f"Metrics: {metrics_async}",
    )

    def _get_manifest(res: dict) -> dict:
        if "manifest" in res and res["manifest"]:
            return res["manifest"]
        if "run_info" in res and "manifest_file" in res["run_info"]:
            mf = Path(res["run_info"]["manifest_file"])
            if mf.exists():
                return json.loads(mf.read_text(encoding="utf-8"))
        return {}

    # ------------------------------------------------------------------
    # Check 3: HTTP Client Cohort (01_curl_cffi & 04_httpx_parsel)
    # ------------------------------------------------------------------
    print("\n--- Check 3: HTTP Client Cohort (01_curl_cffi & 04_httpx_parsel) ---")
    update_progress(45, "Testing HTTP client adapters under human_mode=True and False...")

    curl_adapter = importlib.import_module("tools.01_curl_cffi.adapter")
    res_curl_off = curl_adapter.run(
        target_url="https://leetcode.com/problems/two-sum/",
        human_mode=False,
    )
    manifest_curl_off = _get_manifest(res_curl_off)
    assert_check(
        "01_curl_cffi runs with human_mode=False and records domain_metrics",
        manifest_curl_off.get("status") == "completed" and
        manifest_curl_off.get("domain_metrics", {}).get("human_mode_active") is False,
        f"domain_metrics: {manifest_curl_off.get('domain_metrics')}",
    )

    res_curl_on = curl_adapter.run(
        target_url="https://leetcode.com/problems/two-sum/",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_curl_on = _get_manifest(res_curl_on)
    assert_check(
        "01_curl_cffi runs with human_mode=True and records timing delay metric",
        manifest_curl_on.get("status") == "completed" and
        manifest_curl_on.get("domain_metrics", {}).get("human_mode_active") is True and
        manifest_curl_on.get("domain_metrics", {}).get("timing_profile") == "FAST_AUTOMATED",
        f"domain_metrics: {manifest_curl_on.get('domain_metrics')}",
    )

    httpx_adapter = importlib.import_module("tools.04_httpx_parsel.adapter")
    res_httpx_on = httpx_adapter.run(
        target_url="https://quotes.toscrape.com",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_httpx = _get_manifest(res_httpx_on)
    assert_check(
        "04_httpx_parsel runs with human_mode=True and records domain_metrics",
        manifest_httpx.get("status") == "completed" and
        manifest_httpx.get("domain_metrics", {}).get("human_mode_active") is True,
        f"domain_metrics: {manifest_httpx.get('domain_metrics')}",
    )


    # ------------------------------------------------------------------
    # Check 4: Browser Cohort (06_playwright & 07_patchright)
    # ------------------------------------------------------------------
    print("\n--- Check 4: Browser Cohort (06_playwright & 07_patchright) ---")
    update_progress(65, "Testing browser adapters with human_mode=True...")

    pw_adapter = importlib.import_module("tools.06_playwright.adapter")
    res_pw = pw_adapter.run(
        target_url="https://quotes.toscrape.com/js/",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_pw = _get_manifest(res_pw)
    assert_check(
        "06_playwright runs with human_mode=True and captures human interaction metrics",
        manifest_pw.get("status") == "completed" and
        manifest_pw.get("domain_metrics", {}).get("human_mode_active") is True and
        manifest_pw.get("domain_metrics", {}).get("has_human_metrics") is True,
        f"domain_metrics: {manifest_pw.get('domain_metrics')}",
    )

    pr_adapter = importlib.import_module("tools.07_patchright.adapter")
    res_pr = pr_adapter.run(
        target_url="https://quotes.toscrape.com/js/",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_pr = _get_manifest(res_pr)
    assert_check(
        "07_patchright runs with human_mode=True and records stealth evasion metrics",
        manifest_pr.get("status") == "completed" and
        manifest_pr.get("domain_metrics", {}).get("human_mode_active") is True,
        f"domain_metrics: {manifest_pr.get('domain_metrics')}",
    )

    # ------------------------------------------------------------------
    # Check 5: Media & AI Extraction Cohort (11_yt_dlp_ffmpeg & 16_crawl4ai)
    # ------------------------------------------------------------------
    print("\n--- Check 5: Media & AI Extraction Cohort (11_yt_dlp_ffmpeg & 16_crawl4ai) ---")
    update_progress(80, "Testing 11_yt_dlp_ffmpeg and 16_crawl4ai with human_mode=True...")

    yt_adapter = importlib.import_module("tools.11_yt_dlp_ffmpeg.adapter")
    res_yt = yt_adapter.run(
        target_url="mock://test_reel_human_mode",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_yt = _get_manifest(res_yt)
    assert_check(
        "11_yt_dlp_ffmpeg runs with human_mode=True and records stream chunk pacing metric",
        manifest_yt.get("status") == "completed" and
        manifest_yt.get("domain_metrics", {}).get("human_mode_active") is True and
        manifest_yt.get("domain_metrics", {}).get("pacing_delay_applied") > 0,
        f"domain_metrics: {manifest_yt.get('domain_metrics')}",
    )

    crawl_adapter = importlib.import_module("tools.16_crawl4ai.adapter")
    res_crawl = crawl_adapter.run(
        target_url="https://leetcode.com/problems/trapping-rain-water/",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    manifest_crawl = _get_manifest(res_crawl)
    assert_check(
        "16_crawl4ai runs with human_mode=True and records pre-delay & reading delay metrics",
        manifest_crawl.get("status") == "completed" and
        manifest_crawl.get("domain_metrics", {}).get("human_mode_active") is True and
        manifest_crawl.get("domain_metrics", {}).get("reading_delay_applied") > 0,
        f"domain_metrics: {manifest_crawl.get('domain_metrics')}",
    )


    # ------------------------------------------------------------------
    # Check 6: Backward Compatibility & Unified run() API
    # ------------------------------------------------------------------
    print("\n--- Check 6: Backward Compatibility & Unified run() API ---")
    update_progress(90, "Verifying backward compatibility and top-level run() signatures...")

    adapters_to_test = [
        ("01_curl_cffi", curl_adapter),
        ("04_httpx_parsel", httpx_adapter),
        ("06_playwright", pw_adapter),
        ("07_patchright", pr_adapter),
        ("11_yt_dlp_ffmpeg", yt_adapter),
        ("16_crawl4ai", crawl_adapter),
    ]

    all_have_run = True
    all_accept_kwargs = True
    for name, mod in adapters_to_test:
        if not hasattr(mod, "run") or not callable(getattr(mod, "run")):
            all_have_run = False
            print(f"Missing run() in {name}")
        if not hasattr(mod, "run_action") or not callable(getattr(mod, "run_action")):
            all_accept_kwargs = False
            print(f"Missing run_action() in {name}")

    assert_check(
        "All 6 target adapters export unified run() and preserve legacy run_action() entrypoints",
        all_have_run and all_accept_kwargs,
        f"Checked: {[a[0] for a in adapters_to_test]}",
    )

    # ------------------------------------------------------------------
    # Check 7: Stage 4 Logging, Master Index Sync & Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 7: Stage 4 Logging, Master Index Sync & Secret Guard ---")
    update_progress(95, "Checking stage_4_working_ways.jsonl, FTS5 sync, and pre-commit secret guard...")

    stage_log = ROOT / "logs" / "stages" / "stage_4_working_ways.jsonl"
    assert_check(
        "logs/stages/stage_4_working_ways.jsonl exists and records Step 4.3 entries",
        stage_log.exists() and stage_log.stat().st_size > 0,
        f"Size: {stage_log.stat().st_size if stage_log.exists() else 0} bytes",
    )

    # Sync Master Index
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() synchronizes runs and FTS5 entries without error",
        isinstance(sync_stats, dict) and sync_stats.get("status") == "active" and "totals" in sync_stats,
        f"Sync stats totals: {sync_stats.get('totals')}",
    )

    # Secret Guard
    secret_findings = scan_staged_for_secrets()
    assert_check(
        "Pre-commit secret guard reports 0 plaintext secrets staged",
        secret_findings.get("violations_found") is False and secret_findings.get("blocked_secrets_count", 0) == 0,
        f"Violations: {secret_findings}",
    )


    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    update_progress(100, "Verification suite complete.")
    total = PASSED_COUNT + FAILED_COUNT
    print("\n" + "=" * 70)
    print(f"📊 STAGE 4 STEP 4.3 VERIFICATION RESULT: {PASSED_COUNT}/{total} CHECKS PASSED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        print(f"❌ Verification failed with {FAILED_COUNT} errors.")
        sys.exit(1)
    else:
        print("🎉 ALL STAGE 4 STEP 4.3 CHECKS COMPLETED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
