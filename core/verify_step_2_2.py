"""
core/verify_step_2_2.py
======================
Comprehensive automated verification suite for Stage 2 - Step 2.2:
Global Master Indexer, SQLite FTS5 Full-Text Search, Multi-Tier Log Indexing,
REST API Endpoints, Auto-Sync Hooks, and Frontend Control Center.
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

from core.global_indexer import GlobalMasterIndexer
from core.base_indexer import get_tool_indexer
from core.state_tracker import update_progress


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 2 STEP 2.2 VERIFICATION SUITE")
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

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: Global Master Indexer Sync & Schema Integrity
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 1: Master Indexer Sync & Schema Integrity ---")
    indexer = GlobalMasterIndexer()
    summary = indexer.sync_all(rebuild_tools_first=False)
    
    db_path = ROOT / "index_store" / "global_master_index.sqlite"
    json_path = ROOT / "index_store" / "global_master_index.json"
    
    assert_check("Master SQLite database file exists", db_path.exists(), str(db_path))
    assert_check("Master JSON snapshot file exists", json_path.exists(), str(json_path))
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    assert_check("Table 'global_tools' exists", "global_tools" in tables)
    assert_check("Table 'global_runs' exists", "global_runs" in tables)
    assert_check("Table 'global_files' exists", "global_files" in tables)
    assert_check("Table 'global_logs' exists", "global_logs" in tables)
    assert_check("FTS5 table 'fts_artifacts' exists", "fts_artifacts" in tables)
    assert_check("FTS5 table 'fts_logs' exists", "fts_logs" in tables)
    
    # Check counts
    tools_count = conn.execute("SELECT COUNT(*) FROM global_tools").fetchone()[0]
    runs_count = conn.execute("SELECT COUNT(*) FROM global_runs").fetchone()[0]
    files_count = conn.execute("SELECT COUNT(*) FROM global_files").fetchone()[0]
    logs_count = conn.execute("SELECT COUNT(*) FROM global_logs").fetchone()[0]
    
    assert_check("All 20 tools indexed in global_tools", tools_count == 20, f"found {tools_count}")
    assert_check("Indexed runs count > 0", runs_count > 0, f"found {runs_count} runs")
    assert_check("Indexed files count > 0", files_count > 0, f"found {files_count} files")
    assert_check("Indexed logs count > 0", logs_count > 0, f"found {logs_count} log records")
    
    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: Multi-Tier Log Integrity in Master Index
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 2: Multi-Tier Log Coverage in Master Index ---")
    tiers = [r[0] for r in conn.execute("SELECT DISTINCT log_tier FROM global_logs").fetchall()]
    print(f"  Discovered log tiers: {tiers}")
    assert_check("Tier 1: 'action_run' logs indexed", "action_run" in tiers)
    assert_check("Tier 2: 'tool_ops' logs indexed", "tool_ops" in tiers)
    assert_check("Tier 3: 'stage_log' logs indexed", "stage_log" in tiers)
    assert_check("Tier 4: 'global_prompt' logs indexed", "global_prompt" in tiers)
    
    # Check deduplication: log_id is primary key
    dup_check = conn.execute("SELECT log_id, COUNT(*) FROM global_logs GROUP BY log_id HAVING COUNT(*) > 1").fetchall()
    assert_check("Master log table has 0 duplicates", len(dup_check) == 0)
    
    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: SQLite FTS5 Full-Text Search Queries
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 3: SQLite FTS5 Full-Text Search Queries ---")
    fts_artifacts_results = indexer.query_files(q="two-sum")
    assert_check("FTS5 artifact query 'two-sum' returns results", len(fts_artifacts_results) > 0, f"found {len(fts_artifacts_results)} matches")
    
    fts_logs_results = indexer.query_logs(q="impersonating")
    assert_check("FTS5 log query 'impersonating' returns results", len(fts_logs_results) > 0, f"found {len(fts_logs_results)} matches")
    
    fts_empty = indexer.query_files(q="nonexistentxyz123456term")
    assert_check("FTS5 handles non-matching queries gracefully", len(fts_empty) == 0)
    
    conn.close()

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: Dedicated Per-Tool Index Isolation vs Global Master
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 4: Dedicated Per-Tool Index Isolation ---")
    tool_01_db = ROOT / "index_store" / "tool_indexes" / "01_curl_cffi.sqlite"
    assert_check("Tool 01 dedicated SQLite database exists", tool_01_db.exists())
    
    tool_01_indexer = get_tool_indexer("01_curl_cffi")
    t01_summary = tool_01_indexer.get_summary()
    assert_check("Tool 01 runs queryable directly from its dedicated DB", t01_summary.get("total_runs", 0) > 0, f"{t01_summary.get('total_runs')} runs")
    assert_check("Tool 01 files queryable directly from its dedicated DB", t01_summary.get("total_files", 0) > 0, f"{t01_summary.get('total_files')} files")


    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: FastAPI REST API Endpoints (Local Backend Verification)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 5: FastAPI REST Endpoints ---")
    base_url = "http://127.0.0.1:8000"
    
    try:
        # GET /api/index/overview
        res = urllib.request.urlopen(f"{base_url}/api/index/overview")
        data = json.loads(res.read())
        assert_check("GET /api/index/overview status 200", res.status == 200)
        assert_check("Overview has totals and 20 tool summaries", 
                     data.get("totals", {}).get("total_tools") == 20 and len(data.get("individual_tool_indexes", [])) == 20)
        
        # GET /api/index/runs (global scope)
        res_runs_glob = urllib.request.urlopen(f"{base_url}/api/index/runs?scope=global")
        runs_glob = json.loads(res_runs_glob.read())
        assert_check("GET /api/index/runs?scope=global returns runs", runs_glob.get("count", 0) > 0)
        
        # GET /api/index/runs (tool scope)
        res_runs_tool = urllib.request.urlopen(f"{base_url}/api/index/runs?scope=01_curl_cffi")
        runs_tool = json.loads(res_runs_tool.read())
        assert_check("GET /api/index/runs?scope=01_curl_cffi hits dedicated DB", runs_tool.get("scope") == "01_curl_cffi")
        
        # GET /api/index/files with FTS5 search
        q_encoded = urllib.parse.quote("two-sum")
        res_files = urllib.request.urlopen(f"{base_url}/api/index/files?scope=global&q={q_encoded}")
        files_data = json.loads(res_files.read())
        assert_check("GET /api/index/files?q=two-sum returns FTS5 matches", files_data.get("count", 0) > 0)
        
        # GET /api/index/logs with FTS5 search
        q_log_enc = urllib.parse.quote("impersonating")
        res_logs = urllib.request.urlopen(f"{base_url}/api/index/logs?scope=global&q={q_log_enc}")
        logs_data = json.loads(res_logs.read())
        assert_check("GET /api/index/logs?q=impersonating returns FTS5 matches", logs_data.get("count", 0) > 0)
        
    except Exception as e:
        assert_check("FastAPI REST endpoints respond successfully", False, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6: Auto-Sync Hook in folder_manager.py
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 6: Auto-Sync Hook Verification ---")
    from core.folder_manager import create_action_run, complete_action_run
    
    test_run = create_action_run("01_curl_cffi", "test_index_sync", "https://example.com/test_sync")
    test_raw = Path(test_run["raw_dir"]) / "test_raw.html"
    test_raw.write_text("<html><body>Auto-indexing verification payload unique_test_token_8899</body></html>", encoding="utf-8")
    test_clean = Path(test_run["cleaned_dir"]) / "test_clean.json"
    test_clean.write_text(json.dumps({"token": "unique_test_token_8899", "status": "verified"}), encoding="utf-8")
    
    complete_action_run(test_run, status="completed")

    
    # Verify the new run immediately landed in global_master_index.sqlite and fts_artifacts
    conn2 = sqlite3.connect(str(db_path))
    conn2.row_factory = sqlite3.Row
    hook_run = conn2.execute("SELECT * FROM global_runs WHERE run_id = ?", (test_run["run_id"],)).fetchone()
    assert_check("complete_action_run hook synced run to global_master_index.sqlite", hook_run is not None)
    
    hook_fts = conn2.execute("SELECT * FROM fts_artifacts WHERE fts_artifacts MATCH 'unique_test_token_8899'").fetchall()
    assert_check("complete_action_run hook updated FTS5 virtual table fts_artifacts", len(hook_fts) > 0)
    conn2.close()

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7: Frontend Assets Verification
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- Check 7: Frontend Control Center Assets ---")
    html_content = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js_content = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    css_content = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")
    
    assert_check("index.html contains Tab 4 button 'Index & Search Hub'", "tab-index" in html_content)
    assert_check("index.html contains stage filter in Tab 1", "filter-stage" in html_content)
    assert_check("index.html contains scope select dropdown", "index-scope-select" in html_content)
    assert_check("index.html contains all 3 sub-views (runs, files, logs)", 
                 "subview-runs" in html_content and "subview-files" in html_content and "subview-logs" in html_content)
    
    assert_check("app.js contains switchSubView & loadIndexHub", 
                 "switchSubView" in js_content and "loadIndexHub" in js_content)
    assert_check("app.js contains jumpToRunDetail (Tab 4 -> Tab 3)", "jumpToRunDetail" in js_content)
    assert_check("app.js contains domain metrics rendering in showRunDetail", "domainMetrics" in js_content)
    
    assert_check("styles.css contains .index-hub-layout", ".index-hub-layout" in css_content)
    assert_check("styles.css contains .index-kpi-ribbon", ".index-kpi-ribbon" in css_content)
    assert_check("styles.css contains .subview-btn.active", ".subview-btn.active" in css_content)
    assert_check("styles.css contains mark.fts-hl", "mark.fts-hl" in css_content)

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)
    
    if passed == total:
        print("🎉 ALL STAGE 2 STEP 2.2 CHECKS PASSED WITH 100% SUCCESS!")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
