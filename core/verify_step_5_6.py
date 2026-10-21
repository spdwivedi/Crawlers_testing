"""
core/verify_step_5_6.py
=======================
Master Verification Suite for Stage 5 — Step 5.6:
Build Backend Pipeline Control Plane Endpoints, Build Frontend Tab 7
(Real Task Pipelines & Cleaned Inspector), and Stage 5 Master Verification.

Verifies:
1. Backend Pipeline Overview & Run Query REST Endpoints:
   - GET /api/pipelines/overview returns HTTP 200 with aggregated KPIs, schemas, active pipelines
   - GET /api/pipelines/runs returns HTTP 200 with pagination and pipeline_id filtering
   - GET /api/pipelines/runs/{pipeline_id}/{action}/{date}/{run_id} returns 200 with manifest & tree
   - Invalid run path returns HTTP 404
2. Live Pipeline Execution APIs (POST Background Triggers):
   - POST /api/pipelines/leetcode/run triggers background problem archiver
   - POST /api/pipelines/social/run triggers background social media stream pipeline
   - POST /api/pipelines/forensics/run triggers background secured snapshot forensics
   - POST /api/pipelines/multimodal/run triggers background multimodal auto-resolver
3. Artifact Streaming & Directory Traversal Protection:
   - GET /api/pipelines/artifacts/... streams valid raw/cleaned files with correct MIME type
   - Traversal attempt (..%2f..%2f.env) is blocked with HTTP 400
   - Non-existent artifact returns HTTP 404
4. Frontend Tab 7 UI Assets, Subviews & Design System:
   - frontend/index.html contains tab button, 3 subviews, KPI ribbon, and 4 launcher cards
   - frontend/app.js contains subview switcher, fetchers, file viewers, and launch handlers
   - frontend/styles.css contains styling for studio cards, split inspector, and contract matrix
5. Data Lake Auto-Indexing & Pre-Commit Secret Guard:
   - GlobalMasterIndexer.sync_all() federates all runs into global SQLite index
   - core/git_manager.py:scan_staged_for_secrets() reports zero violations
"""

import importlib
import json
import os
import re
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

from backend.app import app, _scan_pipeline_runs
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
            stage="Stage 5",
            step="Step 5.6",
            tool_id="05_real_pipelines_control_plane",
            action_name="verify_step_5_6",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.6",
            tool_id="05_real_pipelines_control_plane",
            action_name="verify_step_5_6",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 MASTER VERIFICATION SUITE -- STEP 5.6")
    print("   Pipeline Control Plane Endpoints, Frontend Tab 7 UI & Cleaned Inspector")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 5 Step 5.6 master verification suite...")
    client = TestClient(app)

    # ------------------------------------------------------------------
    # Check 1: Backend Pipeline Overview & Run Query REST Endpoints
    # ------------------------------------------------------------------
    print("--- Check 1: Backend Pipeline Overview & Run Query REST Endpoints ---")
    update_progress(15, subtask="Testing /api/pipelines/overview and /api/pipelines/runs endpoints...")

    # 1. Overview API
    res_ov = client.get("/api/pipelines/overview")
    assert_check(
        "GET /api/pipelines/overview returns HTTP 200",
        res_ov.status_code == 200,
        f"Status: {res_ov.status_code}",
    )
    ov_data = res_ov.json()
    assert_check(
        "Overview contains complete KPI summary keys",
        all(k in ov_data for k in [
            "total_pipeline_runs",
            "deliverables_count",
            "active_pipelines",
            "contract_schemas",
            "recent_runs",
        ]),
        f"Keys: {list(ov_data.keys())}",
    )
    assert_check(
        "Overview reports 4 active production pipelines and 5 contract schemas",
        len(ov_data.get("active_pipelines", [])) == 4 and len(ov_data.get("contract_schemas", [])) == 5,
        f"Pipelines: {len(ov_data.get('active_pipelines', []))}, Schemas: {len(ov_data.get('contract_schemas', []))}",
    )

    # 2. Pipeline Runs List API
    res_runs = client.get("/api/pipelines/runs?limit=10&offset=0")
    assert_check(
        "GET /api/pipelines/runs returns HTTP 200 with paged runs array",
        res_runs.status_code == 200 and "runs" in res_runs.json(),
        f"Status: {res_runs.status_code}",
    )
    runs_data = res_runs.json()
    assert_check(
        "Runs response has pagination keys (total, limit, offset, runs)",
        all(k in runs_data for k in ["total", "limit", "offset", "runs"]),
        f"Keys: {list(runs_data.keys())}",
    )

    # 3. Filtered Runs List API
    res_filt = client.get("/api/pipelines/runs?pipeline_id=01_leetcode_archiver")
    assert_check(
        "GET /api/pipelines/runs?pipeline_id=01_leetcode_archiver filters correctly",
        res_filt.status_code == 200 and all("01_leetcode_archiver" in r["pipeline_id"] for r in res_filt.json().get("runs", [])),
        f"Status: {res_filt.status_code}",
    )

    # 4. Pipeline Run Details API
    historical_runs = _scan_pipeline_runs()
    assert_check(
        "Historical pipeline runs detected in data lake",
        len(historical_runs) > 0,
        f"Count: {len(historical_runs)}",
    )

    sample_run = historical_runs[0]
    p_id = sample_run["pipeline_id"]
    a_name = sample_run["action_name"]
    r_date = sample_run["run_date"]
    r_id = sample_run["run_id"]

    res_detail = client.get(f"/api/pipelines/runs/{p_id}/{a_name}/{r_date}/{r_id}")
    assert_check(
        f"GET /api/pipelines/runs/{p_id}/{a_name}/{r_date}/{r_id} returns HTTP 200",
        res_detail.status_code == 200,
        f"Status: {res_detail.status_code}",
    )
    detail_data = res_detail.json()
    assert_check(
        "Run details contain manifest, raw_files, and cleaned_files",
        all(k in detail_data for k in ["manifest", "raw_files", "cleaned_files", "pipeline_id", "run_id"]),
        f"Keys: {list(detail_data.keys())}",
    )

    # 5. Invalid run path returns 404
    res_inv = client.get("/api/pipelines/runs/nonexistent_pipe/action/2026-10-21/run_000000_fake")
    assert_check(
        "GET non-existent pipeline run returns HTTP 404",
        res_inv.status_code == 404,
        f"Status: {res_inv.status_code}",
    )

    # ------------------------------------------------------------------
    # Check 2: Live Pipeline Execution APIs (POST Background Triggers)
    # ------------------------------------------------------------------
    print("\n--- Check 2: Live Pipeline Execution APIs (POST Background Triggers) ---")
    update_progress(35, subtask="Testing POST trigger endpoints for all 4 pipelines...")

    # 1. Trigger LeetCode Archiver
    res_lc = client.post("/api/pipelines/leetcode/run", json={
        "title_slug": "two-sum",
        "human_mode": False,
        "timing_profile": "FAST_AUTOMATED",
        "languages": ["python3"],
        "force_mock": True,
    })
    assert_check(
        "POST /api/pipelines/leetcode/run returns HTTP 200 with status=started",
        res_lc.status_code == 200 and res_lc.json().get("status") == "started",
        f"Status: {res_lc.status_code}, Body: {res_lc.text}",
    )

    # 2. Trigger Social Media Stream Pipeline
    res_soc = client.post("/api/pipelines/social/run", json={
        "target_url": "https://www.instagram.com/reel/verify_reel_sample/",
        "platform": "instagram",
        "human_mode": False,
        "timing_profile": "FAST_AUTOMATED",
        "transcribe_audio": False,
        "force_mock": True,
    })
    assert_check(
        "POST /api/pipelines/social/run returns HTTP 200 with status=started",
        res_soc.status_code == 200 and res_soc.json().get("status") == "started",
        f"Status: {res_soc.status_code}, Body: {res_soc.text}",
    )

    # 3. Trigger Forensics Pipeline
    res_for = client.post("/api/pipelines/forensics/run", json={
        "target_url": "https://httpbin.org/html",
        "human_mode": False,
        "timing_profile": "FAST_AUTOMATED",
        "scroll_depth": 1,
        "force_mock": True,
    })
    assert_check(
        "POST /api/pipelines/forensics/run returns HTTP 200 with status=started",
        res_for.status_code == 200 and res_for.json().get("status") == "started",
        f"Status: {res_for.status_code}, Body: {res_for.text}",
    )

    # 4. Trigger Multimodal Auto-Resolver Pipeline
    res_mm = client.post("/api/pipelines/multimodal/run", json={
        "target_input": "fixtures/exam_question_sample.png",
        "expected_type": "exam_question",
        "human_mode": False,
        "timing_profile": "FAST_AUTOMATED",
        "extract_tables": False,
        "force_mock": True,
    })
    assert_check(
        "POST /api/pipelines/multimodal/run returns HTTP 200 with status=started",
        res_mm.status_code == 200 and res_mm.json().get("status") == "started",
        f"Status: {res_mm.status_code}, Body: {res_mm.text}",
    )

    # Wait for fast background threads to complete
    print("  Waiting 3.5s for fast mock pipelines to finish...")
    time.sleep(3.5)

    # ------------------------------------------------------------------
    # Check 3: Artifact Streaming & Directory Traversal Protection
    # ------------------------------------------------------------------
    print("\n--- Check 3: Artifact Streaming & Directory Traversal Protection ---")
    update_progress(55, subtask="Testing artifact streaming and security guards...")

    # Find a valid file to stream
    pipe_dir = ROOT / "data" / "pipelines"
    deliverable = None
    for p in pipe_dir.glob("*/*/*/*/cleaned/**/*"):
        if p.is_file():
            deliverable = p
            break

    assert_check(
        "Found sample cleaned deliverable in data lake",
        deliverable is not None,
        f"Deliverable: {deliverable}",
    )

    if deliverable:
        rel_parts = deliverable.relative_to(pipe_dir).parts
        pipe_id_part = rel_parts[0]
        act_part = rel_parts[1]
        date_part = rel_parts[2]
        run_part = rel_parts[3]
        folder_part = rel_parts[4]
        filename_part = "/".join(rel_parts[5:])

        art_url = f"/api/pipelines/artifacts/{pipe_id_part}/{act_part}/{date_part}/{run_part}/{folder_part}/{filename_part}"
        res_art = client.get(art_url)
        assert_check(
            f"GET {art_url} returns HTTP 200 with non-empty payload",
            res_art.status_code == 200 and len(res_art.content) > 0,
            f"Status: {res_art.status_code}, Length: {len(res_art.content)}",
        )

        # Path traversal guard test
        bad_art_url = f"/api/pipelines/artifacts/{pipe_id_part}/{act_part}/{date_part}/{run_part}/cleaned/..%2f..%2f..%2f.env"
        res_trav = client.get(bad_art_url)
        assert_check(
            "Directory traversal attempt is strictly blocked (HTTP 400)",
            res_trav.status_code == 400,
            f"Status: {res_trav.status_code}",
        )

        # Non-existent file in valid run
        missing_art_url = f"/api/pipelines/artifacts/{pipe_id_part}/{act_part}/{date_part}/{run_part}/cleaned/nonexistent_file_xyz.json"
        res_miss = client.get(missing_art_url)
        assert_check(
            "Non-existent artifact file returns HTTP 404",
            res_miss.status_code == 404,
            f"Status: {res_miss.status_code}",
        )

    # ------------------------------------------------------------------
    # Check 4: Frontend Tab 7 UI Assets, Subviews & Design System
    # ------------------------------------------------------------------
    print("\n--- Check 4: Frontend Tab 7 UI Assets, Subviews & Design System ---")
    update_progress(75, subtask="Verifying frontend HTML, JS, and CSS files for Tab 7...")

    html_path = ROOT / "frontend" / "index.html"
    js_path = ROOT / "frontend" / "app.js"
    css_path = ROOT / "frontend" / "styles.css"

    html_content = html_path.read_text(encoding="utf-8")
    js_content = js_path.read_text(encoding="utf-8")
    css_content = css_path.read_text(encoding="utf-8")

    # HTML Checks
    expected_html_elements = [
        'data-tab="tab-real-pipelines"',
        'id="tab-real-pipelines"',
        'id="subview-pipeline-studio"',
        'id="subview-cleaned-inspector"',
        'id="subview-contract-matrix"',
        'id="kpi-pipe-runs"',
        'id="kpi-pipe-deliverables"',
        'id="kpi-pipe-compliance"',
        'id="kpi-pipe-active"',
        'id="leetcode-slug"',
        'id="social-url"',
        'id="forensics-url"',
        'id="multimodal-input"',
        'id="pipe-runs-list"',
        'id="pipe-detail-content"',
        'id="pipe-contract-matrix-body"',
    ]
    for elem in expected_html_elements:
        assert_check(
            f"frontend/index.html contains '{elem}'",
            elem in html_content,
            f"Missing '{elem}' in index.html",
        )

    # JavaScript Checks
    expected_js_functions = [
        "loadPipelinesTab",
        "switchPipelinesSubview",
        "loadPipelineRuns",
        "inspectPipelineRun",
        "renderCleanedArtifact",
        "launchPipelineTask",
        "/api/pipelines/overview",
        "/api/pipelines/runs",
    ]
    for fn in expected_js_functions:
        assert_check(
            f"frontend/app.js contains handler '{fn}'",
            fn in js_content,
            f"Missing '{fn}' in app.js",
        )

    # CSS Checks
    expected_css_rules = [
        ".pipe-ribbon",
        ".pipe-kpi-card",
        ".pipe-studio-grid",
        ".pipe-launcher-card",
        ".pipe-inspector-split",
        ".pipe-inspector-sidebar",
        ".pipe-inspector-main",
        ".pipe-matrix-table",
        ".pipe-runs-list",
        ".pipe-code-wrapper",
    ]
    for rule in expected_css_rules:
        assert_check(
            f"frontend/styles.css contains style rule '{rule}'",
            rule in css_content,
            f"Missing '{rule}' in styles.css",
        )

    # ------------------------------------------------------------------
    # Check 5: Data Lake Auto-Indexing & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Data Lake Auto-Indexing & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Verifying global indexing synchronization and secret scan...")

    # Auto-indexing master sync
    try:
        indexer = GlobalMasterIndexer()
        sync_stats = indexer.sync_all()
        assert_check(
            "GlobalMasterIndexer.sync_all() completes without error",
            isinstance(sync_stats, dict) and sync_stats.get("total_runs", 0) >= 0,
            f"Sync stats: {sync_stats}",
        )
    except Exception as exc:
        assert_check("GlobalMasterIndexer.sync_all() executes cleanly", False, str(exc))

    # Pre-commit secret scanning
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports ZERO violations",
        not secret_scan.get("violations_found", False),
        f"Violations: {secret_scan.get('violations', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Stage 5 Step 5.6 Master Verification Suite completed.")
    print("\n" + "=" * 70)
    print(f"STAGE 5 STEP 5.6 VERIFICATION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
