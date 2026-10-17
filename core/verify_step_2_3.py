"""
core/verify_step_2_3.py
======================
Comprehensive automated verification suite for Stage 2 - Step 2.3:
20-Pipeline Visual Switchboard (Isolated vs. Global),
Cascading Folder-Wise Index Inspector, and Dedicated 4-Tier Log Filter Hub.
"""

import sys
import os
import json
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.state_tracker import update_progress


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 2 STEP 2.3 VERIFICATION SUITE")
    print("=" * 70)

    passed = 0
    total = 0

    def assert_check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [PASS] {name}" + (f" ({detail})" if detail else ""))
        else:
            print(f"  ❌ [FAIL] {name}" + (f" - {detail}" if detail else ""))

    base_url = "http://127.0.0.1:8000"

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: GET /api/index/pipelines-status (20-Pipeline Sync Diagnostics)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 1: 20-Pipeline Status & Sync Diagnostics ---")
    update_progress(progress_percent=45, subtask="Verifying 20-pipeline status diagnostics...")
    try:
        res = urllib.request.urlopen(f"{base_url}/api/index/pipelines-status")
        assert_check("GET /api/index/pipelines-status responds with 200 OK", res.status == 200)
        data = json.loads(res.read())

        total_tools = data.get("total_tools", 0)
        synced_count = data.get("synced_count", 0)
        pipelines = data.get("pipelines", [])

        assert_check("Total tools reported is exactly 20", total_tools == 20, f"found {total_tools}")
        assert_check("All 20 tools report SYNCED status", synced_count == 20, f"synced: {synced_count}/20")
        assert_check("Pipelines array length is 20", len(pipelines) == 20)

        # Validate structure of each pipeline
        sample_p = pipelines[0]
        required_keys = ["tool_id", "name", "batch", "mechanism_type", "sqlite_path", "db_size_kb",
                         "isolated_runs_count", "global_runs_count", "isolated_files_count",
                         "global_files_count", "isolated_logs_count", "sync_status"]
        missing_keys = [k for k in required_keys if k not in sample_p]
        assert_check("Pipeline status contains all required schema keys", len(missing_keys) == 0, str(missing_keys))

        # Check counts matching
        all_counts_match = all(
            p["isolated_runs_count"] == p["global_runs_count"] and
            p["isolated_files_count"] == p["global_files_count"]
            for p in pipelines
        )
        assert_check("Isolated counts strictly match Global Master counts for all 20 tools", all_counts_match)

    except Exception as e:
        assert_check("GET /api/index/pipelines-status verification", False, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: GET /api/index/cascading-facets (Cascading Hierarchy)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 2: Cascading Facets (Tool -> Action -> Date -> Run) ---")
    update_progress(progress_percent=60, subtask="Verifying cascading hierarchy endpoints...")
    try:
        # Global scope
        res_glob = urllib.request.urlopen(f"{base_url}/api/index/cascading-facets?scope=global")
        facets_glob = json.loads(res_glob.read())
        assert_check("GET /api/index/cascading-facets?scope=global status 200", res_glob.status == 200)
        assert_check("Global facets return 20 tools", len(facets_glob.get("tools", [])) == 20)
        assert_check("Global facets return available actions", len(facets_glob.get("actions", [])) > 0)
        assert_check("Global facets return available dates", len(facets_glob.get("dates", [])) > 0)
        assert_check("Global facets return available runs", len(facets_glob.get("runs", [])) > 0)
        assert_check("Global facets return distinct stages & steps",
                     len(facets_glob.get("stages", [])) > 0 and len(facets_glob.get("steps", [])) > 0)

        # Isolated tool scope (01_curl_cffi)
        res_tool = urllib.request.urlopen(f"{base_url}/api/index/cascading-facets?scope=01_curl_cffi")
        facets_tool = json.loads(res_tool.read())
        assert_check("GET /api/index/cascading-facets?scope=01_curl_cffi status 200", res_tool.status == 200)
        assert_check("Isolated facets scoped to 01_curl_cffi", facets_tool.get("active_tool_id") == "01_curl_cffi")

        # Cascading filter: tool + action
        test_action = facets_glob["actions"][0]["action_name"]
        res_filter = urllib.request.urlopen(f"{base_url}/api/index/cascading-facets?scope=global&action_name={urllib.parse.quote(test_action)}")
        facets_filter = json.loads(res_filter.read())
        assert_check(f"Cascading filter by action '{test_action}' returns runs", len(facets_filter.get("runs", [])) > 0)

    except Exception as e:
        assert_check("GET /api/index/cascading-facets verification", False, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: GET /api/index/folder-bundle (Unified Run Folder Bundle)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 3: Unified Folder-Bundle (Single-Call Inspection) ---")
    update_progress(progress_percent=75, subtask="Verifying folder-bundle single-call API...")
    try:
        sample_run_id = facets_glob["runs"][0]["run_id"]
        res_bundle = urllib.request.urlopen(f"{base_url}/api/index/folder-bundle?run_id={urllib.parse.quote(sample_run_id)}&scope=global")
        bundle = json.loads(res_bundle.read())
        assert_check("GET /api/index/folder-bundle responds with 200 OK", res_bundle.status == 200)

        m = bundle.get("run_metadata", {})
        assert_check("Bundle metadata has run_id matching request", m.get("run_id") == sample_run_id)
        assert_check("Bundle has parsed domain_metrics dictionary", isinstance(m.get("domain_metrics"), dict))
        assert_check("Bundle contains raw_files list with SHA-256 hashes",
                     "raw_files" in bundle and all("sha256_short" in f for f in bundle["raw_files"]))
        assert_check("Bundle contains cleaned_files list with SHA-256 hashes",
                     "cleaned_files" in bundle and all("sha256_short" in f for f in bundle["cleaned_files"]))
        assert_check("Bundle contains action_logs list", "action_logs" in bundle)

        # Isolated scope test
        tool_id = m.get("tool_id", "01_curl_cffi")
        res_bundle_iso = urllib.request.urlopen(f"{base_url}/api/index/folder-bundle?run_id={urllib.parse.quote(sample_run_id)}&scope={tool_id}")
        bundle_iso = json.loads(res_bundle_iso.read())
        assert_check("GET /api/index/folder-bundle works in isolated tool mode", res_bundle_iso.status == 200 and bundle_iso.get("run_id") == sample_run_id)

    except Exception as e:
        assert_check("GET /api/index/folder-bundle verification", False, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: GET /api/index/prompt-history (Milestones & Prompt Logs)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 4: Antigravity Prompt Execution & Git Milestones History ---")
    update_progress(progress_percent=85, subtask="Verifying prompt history & milestone logging...")
    try:
        res_hist = urllib.request.urlopen(f"{base_url}/api/index/prompt-history?limit=100")
        hist_data = json.loads(res_hist.read())
        assert_check("GET /api/index/prompt-history responds with 200 OK", res_hist.status == 200)
        assert_check("Prompt history returns prompt logs count > 0", hist_data.get("count", 0) > 0)
        assert_check("Prompt history extracts milestones list", len(hist_data.get("milestones", [])) > 0)

        # Check commit extraction
        milestones = hist_data.get("milestones", [])
        has_commits = any(m.get("git_commit") for m in milestones)
        assert_check("Prompt milestones contain structured Git commit hashes", has_commits)

    except Exception as e:
        assert_check("GET /api/index/prompt-history verification", False, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: Frontend Control Center Elements & 4 Sub-Views
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 5: Frontend Control Center 4 Sub-Views & Styling ---")
    update_progress(progress_percent=95, subtask="Verifying frontend control center components...")
    html_content = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js_content = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    css_content = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    # HTML
    assert_check("index.html contains isolated mode warning banner", "isolated-mode-banner" in html_content)
    assert_check("index.html contains Sub-View A 'subview-switchboard'", "subview-switchboard" in html_content)
    assert_check("index.html contains Sub-View B 'subview-cascading'", "subview-cascading" in html_content)
    assert_check("index.html contains Sub-View C 'subview-matrix'", "subview-matrix" in html_content)
    assert_check("index.html contains Sub-View D 'subview-search'", "subview-search" in html_content)
    assert_check("index.html contains 4-column cascading selectors",
                 "cascade-select-tool" in html_content and
                 "cascade-select-action" in html_content and
                 "cascade-select-date" in html_content and
                 "cascade-select-run" in html_content)
    assert_check("index.html contains 4 tier pills in matrix",
                 "count-tier-all" in html_content and
                 "count-tier-4" in html_content and
                 "count-tier-3" in html_content and
                 "count-tier-2" in html_content and
                 "count-tier-1" in html_content)

    # JS
    assert_check("app.js implements loadPipelinesStatus()", "loadPipelinesStatus" in js_content)
    assert_check("app.js implements loadCascadingFacets()", "loadCascadingFacets" in js_content)
    assert_check("app.js implements loadFolderBundle()", "loadFolderBundle" in js_content)
    assert_check("app.js implements loadMatrixLogs()", "loadMatrixLogs" in js_content)
    assert_check("app.js implements exportFilteredLogs()", "exportFilteredLogs" in js_content)
    assert_check("app.js implements loadFtsFiles()", "loadFtsFiles" in js_content)

    # CSS
    assert_check("styles.css styles .isolated-mode-banner", ".isolated-mode-banner" in css_content)
    assert_check("styles.css styles .arch-overview-banner", ".arch-overview-banner" in css_content)
    assert_check("styles.css styles .pipelines-grid", ".pipelines-grid" in css_content)
    assert_check("styles.css styles .cascading-nav-bar", ".cascading-nav-bar" in css_content)
    assert_check("styles.css styles .cascade-bundle-grid", ".cascade-bundle-grid" in css_content)
    assert_check("styles.css styles .matrix-tier-selector", ".matrix-tier-selector" in css_content)

    update_progress(progress_percent=100, subtask="Stage 2 Step 2.3 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 2 STEP 2.3 CHECKS PASSED WITH 100% SUCCESS!")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
