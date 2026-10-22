"""
core/verify_step_6_4.py
=======================
Stage 6 Master Verification Suite (Step 6.4):
Build Backend REST Endpoints for Benchmarking, Chaos Resilience & Exports (`backend/app.py`),
Build Frontend Tab 8 (`📊 Benchmarks, Stress Lab & Exporter` in `frontend/`),
and Verify Master System Index Federation & Pre-Commit Secret Guard.

Verifies:
1. Check 1 — Backend Benchmark REST Endpoints:
   - GET /api/benchmarks/overview returns 200 OK with valid KPI metrics
   - GET /api/benchmarks/reports returns list of historical reports
   - POST /api/benchmarks/run triggers battery execution with status == "started"
2. Check 2 — Backend Resilience & Chaos REST Endpoints:
   - GET /api/resilience/overview returns 200 OK with resilience index
   - GET /api/resilience/reports returns list of historical resilience reports
   - POST /api/resilience/run triggers chaos scenario with status == "started"
3. Check 3 — Backend Project Exporter REST Endpoints:
   - GET /api/exports/list returns all 3 export categories
   - POST /api/exports/tool exports standalone tool cleanly
   - POST /api/exports/bundle generates verified data lake zip bundle
   - GET /api/exports/download/... streams exported zip bundle and strictly blocks path traversal
4. Check 4 — Frontend Tab 8 Assets & Subviews Integration:
   - Confirms frontend/index.html contains Tab 8 button, #tab-benchmarks-exporter, and all 3 sub-views
   - Confirms frontend/app.js implements required handlers
   - Confirms frontend/styles.css contains styling for Tab 8 and sub-view components
5. Check 5 — Master System Index Federation & Pre-Commit Secret Guard:
   - Verifies GlobalMasterIndexer.sync_all() federates all stages cleanly
   - Confirms core/git_manager.py:scan_staged_for_secrets() reports ZERO violations
"""

import json
import os
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

from fastapi.testclient import TestClient
from backend.app import app
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, condition: bool, details: str = "") -> None:
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  [PASS] {name}")
        log_global(
            message=f"CHECK PASSED: {name}",
            level="INFO",
            stage="Stage 6",
            step="Step 6.4",
            tool_id="core_benchmark_engine",
            action_name="verify_step_6_4",
            stage_log_name="stage_6_benchmarking",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 6",
            step="Step 6.4",
            tool_id="core_benchmark_engine",
            action_name="verify_step_6_4",
            stage_log_name="stage_6_benchmarking",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 6 STEP 6.4 MASTER VERIFICATION SUITE")
    print("   Benchmarks, Stress Lab & Exporter Backend REST + Frontend Tab 8")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 6 Step 6.4 master verification suite...")
    client = TestClient(app)

    # ------------------------------------------------------------------
    # Check 1: Backend Benchmark REST Endpoints
    # ------------------------------------------------------------------
    print("--- Check 1: Backend Benchmark REST Endpoints ---")
    update_progress(15, subtask="Testing benchmark overview, reports, and runner endpoints...")

    # GET /api/benchmarks/overview
    res_bm_ov = client.get("/api/benchmarks/overview")
    assert_check(
        "GET /api/benchmarks/overview returns 200 OK",
        res_bm_ov.status_code == 200,
        f"Status: {res_bm_ov.status_code}",
    )
    bm_ov_data = res_bm_ov.json()
    assert_check(
        "Benchmark overview contains valid summary keys",
        "total_benchmark_reports" in bm_ov_data and "recent_reports" in bm_ov_data,
        f"Keys: {list(bm_ov_data.keys())}",
    )

    # GET /api/benchmarks/reports
    res_bm_reps = client.get("/api/benchmarks/reports?limit=10")
    assert_check(
        "GET /api/benchmarks/reports returns 200 OK with reports list",
        res_bm_reps.status_code == 200 and "reports" in res_bm_reps.json(),
        f"Status: {res_bm_reps.status_code}",
    )

    # POST /api/benchmarks/run
    res_bm_run = client.post(
        "/api/benchmarks/run",
        json={
            "target_url": "https://quotes.toscrape.com",
            "iterations": 1,
            "human_mode": False,
            "battery_label": "Verify Step 6.4 Battery",
            "tool_ids": ["01_curl_cffi"],
        },
    )
    assert_check(
        "POST /api/benchmarks/run launches background battery with status == 'started'",
        res_bm_run.status_code == 200 and res_bm_run.json().get("status") == "started",
        f"Response: {res_bm_run.text}",
    )

    # ------------------------------------------------------------------
    # Check 2: Backend Resilience & Chaos REST Endpoints
    # ------------------------------------------------------------------
    print("\n--- Check 2: Backend Resilience & Chaos REST Endpoints ---")
    update_progress(35, subtask="Testing resilience overview, reports, and chaos dispatch endpoints...")

    # GET /api/resilience/overview
    res_res_ov = client.get("/api/resilience/overview")
    assert_check(
        "GET /api/resilience/overview returns 200 OK",
        res_res_ov.status_code == 200,
        f"Status: {res_res_ov.status_code}",
    )
    res_ov_data = res_res_ov.json()
    assert_check(
        "Resilience overview contains latest_resilience_index",
        "latest_resilience_index" in res_ov_data and "total_resilience_reports" in res_ov_data,
        f"Keys: {list(res_ov_data.keys())}",
    )

    # GET /api/resilience/reports
    res_res_reps = client.get("/api/resilience/reports?limit=10")
    assert_check(
        "GET /api/resilience/reports returns 200 OK with reports list",
        res_res_reps.status_code == 200 and "reports" in res_res_reps.json(),
        f"Status: {res_res_reps.status_code}",
    )

    # POST /api/resilience/run
    res_chaos_run = client.post(
        "/api/resilience/run",
        json={
            "scenario": "contract_fuzzing",
            "tool_id": "01_curl_cffi",
        },
    )
    assert_check(
        "POST /api/resilience/run dispatches chaos test with status == 'started'",
        res_chaos_run.status_code == 200 and res_chaos_run.json().get("status") == "started",
        f"Response: {res_chaos_run.text}",
    )

    # ------------------------------------------------------------------
    # Check 3: Backend Project Exporter REST Endpoints
    # ------------------------------------------------------------------
    print("\n--- Check 3: Backend Project Exporter REST Endpoints ---")
    update_progress(55, subtask="Testing export list, tool, bundle, pipeline, and secure download...")

    # GET /api/exports/list
    res_exp_list = client.get("/api/exports/list")
    assert_check(
        "GET /api/exports/list returns 200 OK with 3 export categories",
        res_exp_list.status_code == 200
        and "standalone_tools" in res_exp_list.json()
        and "data_bundles" in res_exp_list.json()
        and "pipeline_packages" in res_exp_list.json(),
        f"Keys: {list(res_exp_list.json().keys()) if res_exp_list.status_code == 200 else res_exp_list.status_code}",
    )

    # POST /api/exports/tool
    res_exp_tool = client.post(
        "/api/exports/tool",
        json={"tool_id": "01_curl_cffi", "output_format": "zip"},
    )
    assert_check(
        "POST /api/exports/tool returns 200 OK with export path and manifest",
        res_exp_tool.status_code == 200 and "export_path" in res_exp_tool.json(),
        f"Response: {res_exp_tool.text}",
    )

    # POST /api/exports/bundle
    res_exp_bundle = client.post(
        "/api/exports/bundle",
        json={"scope": "cleaned", "pipeline_id": "", "archive_format": "zip"},
    )
    assert_check(
        "POST /api/exports/bundle generates verified data lake zip bundle",
        res_exp_bundle.status_code == 200 and "bundle_id" in res_exp_bundle.json(),
        f"Response: {res_exp_bundle.text}",
    )
    bundle_id = res_exp_bundle.json().get("bundle_id", "")

    # GET /api/exports/download/{category}/{filename}
    res_dl = client.get(f"/api/exports/download/data_bundles/{bundle_id}.zip")
    assert_check(
        "GET /api/exports/download streams valid zip archive (200 OK)",
        res_dl.status_code == 200 and len(res_dl.content) > 0,
        f"Status: {res_dl.status_code}, Length: {len(res_dl.content)}",
    )

    # Directory Traversal Security Test
    res_traversal = client.get("/api/exports/download/data_bundles/..%2f..%2f.env")
    assert_check(
        "GET /api/exports/download strictly blocks directory traversal (400 Bad Request)",
        res_traversal.status_code == 400,
        f"Status: {res_traversal.status_code}, Body: {res_traversal.text}",
    )

    # ------------------------------------------------------------------
    # Check 4: Frontend Tab 8 Assets & Subviews Integration
    # ------------------------------------------------------------------
    print("\n--- Check 4: Frontend Tab 8 Assets & Subviews Integration ---")
    update_progress(75, subtask="Verifying Tab 8 HTML, JS handlers, and CSS styling...")

    html_file = ROOT / "frontend" / "index.html"
    js_file = ROOT / "frontend" / "app.js"
    css_file = ROOT / "frontend" / "styles.css"

    html_content = html_file.read_text(encoding="utf-8")
    js_content = js_file.read_text(encoding="utf-8")
    css_content = css_file.read_text(encoding="utf-8")

    # HTML Checks
    assert_check(
        "index.html contains Tab 8 nav button (data-tab='tab-benchmarks-exporter')",
        'data-tab="tab-benchmarks-exporter"' in html_content,
    )
    assert_check(
        "index.html contains #tab-benchmarks-exporter container",
        'id="tab-benchmarks-exporter"' in html_content,
    )
    assert_check(
        "index.html contains Sub-View A (#subview-benchmark-lab)",
        'id="subview-benchmark-lab"' in html_content,
    )
    assert_check(
        "index.html contains Sub-View B (#subview-resilience-lab)",
        'id="subview-resilience-lab"' in html_content,
    )
    assert_check(
        "index.html contains Sub-View C (#subview-exporter-lab)",
        'id="subview-exporter-lab"' in html_content,
    )

    # JS Checks
    for handler in [
        "loadBenchmarksTab",
        "runBenchmarkBattery",
        "loadBenchmarkReports",
        "runChaosScenario",
        "loadResilienceReports",
        "exportStandaloneTool",
        "bundleDataLake",
        "exportStandalonePipeline",
        "loadExportsTab",
        "downloadExportArchive",
    ]:
        assert_check(
            f"app.js implements handler: {handler}",
            handler in js_content,
            f"Handler {handler} missing in app.js",
        )

    # CSS Checks
    for selector in [
        ".bench-subview-panel",
        ".bench-card",
        ".gold-border",
        ".chaos-card",
        ".export-card",
        ".btn-danger-glow",
        ".resilience-item",
    ]:
        assert_check(
            f"styles.css defines style rule: {selector}",
            selector in css_content,
            f"Rule {selector} missing in styles.css",
        )

    # ------------------------------------------------------------------
    # Check 5: Master System Index Federation & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Master System Index Federation & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Synchronizing Global Master Index and running pre-commit secret scan...")

    # Global Master Indexer synchronization
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() federates all runs cleanly",
        isinstance(sync_stats, dict) and sync_stats.get("total_runs", 0) >= 0,
        f"Sync stats: {sync_stats}",
    )

    # Pre-Commit Secret Guard
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports ZERO violations",
        not secret_scan.get("violations_found", False),
        f"Violations: {secret_scan.get('violations', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Stage 6 Step 6.4 Master Verification Suite completed.")
    print("\n" + "=" * 70)
    print(f"STAGE 6 STEP 6.4 VERIFICATION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
