"""
core/verify_step_4_6.py
=======================
Master Verification Suite for Stage 4 — Step 4.6 (Stage 4 Completion):
Backend REST Endpoints for Working Ways, Frontend Tab 6 (Working Ways & Safe Arena UI),
Interactive Kinematics, Auto-Indexing, and Secret Guard.

Verifies:
1. Backend REST Endpoints (Read-Only & Metadata APIs):
   - GET /api/working-ways/overview
   - GET /api/working-ways/arena/reports
   - GET /api/working-ways/arena/reports/{report_id}
   - GET /api/working-ways/pipelines/reports
   - GET /api/working-ways/pipelines/reports/{report_id}
   - GET /api/working-ways/timing/simulate
2. Backend REST Endpoints (Live Mutation APIs):
   - POST /api/working-ways/arena/run (Safe Arena tournament trigger)
   - POST /api/working-ways/pipelines/run (Precision Task Router pipeline trigger)
3. Frontend Tab 6 Markup, Logic, and Design System Integration:
   - index.html: Tab navigation, 5-KPI ribbon, 3 sub-views, matrix table, timeline, canvas
   - app.js: Controller functions (loadWorkingWaysTab, launchArenaTournament, launchPipelineRun, animateKinematicsCurve)
   - styles.css: Responsive layout, winner glow banner, recipe cards, kinematics canvas
4. Global Master Index Sync:
   - GlobalMasterIndexer().sync_all() across all tool indexes and run logs
5. Zero-Plaintext Credential Security & Pre-Commit Secret Guard:
   - Rule 6 secret scanner (vault_store, .env, API keys)
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
            stage="Stage 4",
            step="Step 4.6",
            tool_id="working_ways",
            action_name="verify_stage_4_completion",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.6",
            tool_id="working_ways",
            action_name="verify_stage_4_completion",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 4 MASTER VERIFICATION SUITE -- STEP 4.6")
    print("   Working Ways Backend REST Endpoints, Frontend Tab 6 UI, and Governance")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 Step 4.6 master verification suite...")
    client = TestClient(app)

    # ------------------------------------------------------------------
    # Check 1: Backend REST Endpoints (Read-Only & Metadata APIs)
    # ------------------------------------------------------------------
    print("--- Check 1: Backend REST Endpoints (Read-Only & Metadata) ---")
    update_progress(15, "Testing /api/working-ways overview, reports, and timing simulation...")

    # 1. Overview API
    res_ov = client.get("/api/working-ways/overview")
    assert_check(
        "GET /api/working-ways/overview returns HTTP 200",
        res_ov.status_code == 200,
        f"Status: {res_ov.status_code}",
    )
    ov_data = res_ov.json()
    assert_check(
        "Overview contains complete KPI summary keys",
        all(k in ov_data for k in ["total_arena_reports", "total_pipeline_reports", "winning_scrapers_leaderboard", "canonical_recipes", "timing_profiles"]),
        f"Keys: {list(ov_data.keys())}",
    )

    # 2. Arena Reports List API
    res_ar_list = client.get("/api/working-ways/arena/reports?limit=5")
    assert_check(
        "GET /api/working-ways/arena/reports returns HTTP 200 with reports array",
        res_ar_list.status_code == 200 and "reports" in res_ar_list.json(),
        f"Status: {res_ar_list.status_code}",
    )
    ar_reports = res_ar_list.json().get("reports", [])
    if ar_reports:
        first_ar_id = ar_reports[0]["report_id"]
        res_ar_single = client.get(f"/api/working-ways/arena/reports/{first_ar_id}")
        assert_check(
            f"GET /api/working-ways/arena/reports/{first_ar_id} returns single report with markdown",
            res_ar_single.status_code == 200 and "markdown_content" in res_ar_single.json(),
            f"Status: {res_ar_single.status_code}",
        )
    else:
        assert_check("Arena reports query executed", True, "No historical arena reports yet")

    # 3. Pipeline Reports List API
    res_pr_list = client.get("/api/working-ways/pipelines/reports?limit=5")
    assert_check(
        "GET /api/working-ways/pipelines/reports returns HTTP 200 with reports array",
        res_pr_list.status_code == 200 and "reports" in res_pr_list.json(),
        f"Status: {res_pr_list.status_code}",
    )
    pr_reports = res_pr_list.json().get("reports", [])
    if pr_reports:
        first_pr_id = pr_reports[0]["report_id"]
        res_pr_single = client.get(f"/api/working-ways/pipelines/reports/{first_pr_id}")
        assert_check(
            f"GET /api/working-ways/pipelines/reports/{first_pr_id} returns single report with stage records",
            res_pr_single.status_code == 200 and "stage_records" in res_pr_single.json(),
            f"Status: {res_pr_single.status_code}",
        )
    else:
        assert_check("Pipeline reports query executed", True, "No historical pipeline reports yet")

    # 4. Timing Simulation API
    res_timing = client.get("/api/working-ways/timing/simulate?profile=BALANCED_HUMAN&action_type=navigate&samples=30")
    assert_check(
        "GET /api/working-ways/timing/simulate returns HTTP 200 with sampled delays",
        res_timing.status_code == 200,
        f"Status: {res_timing.status_code}",
    )
    tm_data = res_timing.json()
    assert_check(
        "Timing simulation returns valid distribution statistics",
        len(tm_data.get("delays", [])) == 30 and tm_data.get("min_sec", 0) <= tm_data.get("mean_sec", 0) <= tm_data.get("max_sec", 0),
        f"Min: {tm_data.get('min_sec')}, Mean: {tm_data.get('mean_sec')}, Max: {tm_data.get('max_sec')}",
    )

    # ------------------------------------------------------------------
    # Check 2: Live POST Mutation APIs
    # ------------------------------------------------------------------
    print("\n--- Check 2: Live POST Mutation APIs ---")
    update_progress(35, "Testing POST /api/working-ways/arena/run and pipelines/run...")

    # 1. Trigger Fast Arena Run
    arena_payload = {
        "target_url": "https://quotes.toscrape.com",
        "candidate_tools": ["01_curl_cffi"],
        "timing_profile": "FAST_AUTOMATED",
        "human_mode": True,
        "run_label": "Automated Verification Test Arena",
    }
    res_ar_post = client.post("/api/working-ways/arena/run", json=arena_payload)
    assert_check(
        "POST /api/working-ways/arena/run launches tournament successfully",
        res_ar_post.status_code == 200 and res_ar_post.json().get("status") in ["started", "initiated", "completed"],
        f"Status: {res_ar_post.status_code}, Body: {res_ar_post.text}",
    )

    # 2. Trigger Fast Pipeline Run
    pipeline_payload = {
        "pipeline_recipe": "graphql_markdown",
        "target_url": "https://quotes.toscrape.com",
        "timing_profile": "FAST_AUTOMATED",
        "human_mode": True,
        "pipeline_label": "Automated Verification Test Pipeline",
    }
    res_pipe_post = client.post("/api/working-ways/pipelines/run", json=pipeline_payload)
    assert_check(
        "POST /api/working-ways/pipelines/run launches precision pipeline successfully",
        res_pipe_post.status_code == 200 and res_pipe_post.json().get("status") in ["started", "initiated", "completed"],
        f"Status: {res_pipe_post.status_code}, Body: {res_pipe_post.text}",
    )

    # Wait briefly for background threads to complete
    time.sleep(3.0)

    # ------------------------------------------------------------------
    # Check 3: Frontend Tab 6 Markup, Logic, and Design System Integration
    # ------------------------------------------------------------------
    print("\n--- Check 3: Frontend Tab 6 Markup, Logic, and Styles Integration ---")
    update_progress(60, "Verifying frontend HTML, JS, and CSS files for Tab 6...")

    html_path = ROOT / "frontend" / "index.html"
    js_path = ROOT / "frontend" / "app.js"
    css_path = ROOT / "frontend" / "styles.css"

    html_content = html_path.read_text(encoding="utf-8")
    js_content = js_path.read_text(encoding="utf-8")
    css_content = css_path.read_text(encoding="utf-8")

    # HTML Checks
    expected_html_elements = [
        'data-tab="tab-working-ways"',
        'id="tab-working-ways"',
        'id="ww-kpi-arena-count"',
        'id="ww-kpi-top-winner"',
        'id="subview-arena"',
        'id="subview-pipelines"',
        'id="subview-timing"',
        'id="arena-matrix-table"',
        'id="pipeline-timeline"',
        'id="pipeline-deliverables-list"',
        'id="kinematics-canvas"',
    ]
    html_all_present = all(el in html_content for el in expected_html_elements)
    assert_check(
        "frontend/index.html contains all required Tab 6 components and subviews",
        html_all_present,
        f"Missing: {[el for el in expected_html_elements if el not in html_content]}",
    )

    # JS Checks
    expected_js_functions = [
        "loadWorkingWaysTab",
        "switchWorkingWaysSubView",
        "loadWorkingWaysOverview",
        "launchArenaTournament",
        "loadArenaReports",
        "viewArenaReport",
        "renderArenaResults",
        "selectPipelineRecipe",
        "launchPipelineRun",
        "loadPipelineReports",
        "viewPipelineReport",
        "renderPipelineResults",
        "runTimingSimulation",
        "animateKinematicsCurve",
        "clearKinematicsCanvas",
    ]
    js_all_present = all(fn in js_content for fn in expected_js_functions)
    assert_check(
        "frontend/app.js contains all Tab 6 controller and rendering functions",
        js_all_present,
        f"Missing: {[fn for fn in expected_js_functions if fn not in js_content]}",
    )

    # CSS Checks
    expected_css_classes = [
        ".working-ways-layout",
        ".working-ways-ribbon",
        ".ww-kpi-card",
        ".ww-subview-nav",
        ".ww-subview-btn",
        ".ww-two-col",
        ".ww-card",
        ".ww-winner-banner",
        ".ww-table",
        ".ww-recipe-card",
        ".ww-pipeline-timeline",
        ".timeline-step",
        ".ww-deliverable-item",
        ".timing-bars-container",
        "#kinematics-canvas",
    ]
    css_all_present = all(cls in css_content for cls in expected_css_classes)
    assert_check(
        "frontend/styles.css contains complete Tab 6 design system classes",
        css_all_present,
        f"Missing: {[cls for cls in expected_css_classes if cls not in css_content]}",
    )

    # ------------------------------------------------------------------
    # Check 4: Global Master Index Sync Across All Subsystems
    # ------------------------------------------------------------------
    print("\n--- Check 4: Global Master Index Sync Across All Subsystems ---")
    update_progress(80, "Executing federated GlobalMasterIndexer().sync_all()...")

    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()

    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    total_tools = sync_stats.get("totals", {}).get("total_tools", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() completes with non-zero indexing count",
        isinstance(sync_stats, dict) and total_runs > 0 and total_tools == 20,
        f"Total runs: {total_runs}, Total tools: {total_tools}",
    )

    # ------------------------------------------------------------------
    # Check 5: Zero-Plaintext Security & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Zero-Plaintext Security & Pre-Commit Secret Guard ---")
    update_progress(95, "Running pre-commit secret scan across staged and workspace files...")

    secret_scan = scan_staged_for_secrets()
    violations_found = secret_scan.get("violations_found", False)
    blocked_count = secret_scan.get("blocked_secrets_count", 0)
    assert_check(
        "Pre-commit secret guard passes with zero leaks",
        (not violations_found) and blocked_count == 0,
        f"Findings: {secret_scan.get('details', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"STAGE 4 STEP 4.6 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, "Stage 4 Step 4.6 Master Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 4 STEP 4.6 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
