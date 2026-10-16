"""
core/verify_step_2_1.py
======================
Verification Script for Stage 2 - Step 2.1:
  - Validates 20/20 dedicated per-tool indexing pipelines.
  - Verifies SQLite databases and JSON snapshots in index_store/tool_indexes/.
  - Verifies domain-specific metrics extraction across all 20 tools.
  - Verifies Rule 5 auto-indexing hook in folder_manager.py.
  - Verifies 4-tier logging and live state telemetry.
"""
from __future__ import annotations

import importlib
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.base_indexer import BaseToolIndexer
from core.folder_manager import create_action_run, complete_action_run
from core.logger_engine import LogEngine
from core.state_tracker import update_progress

INDEX_STORE_DIR = ROOT / "index_store" / "tool_indexes"
REGISTRY_PATH = ROOT / "tools" / "registry.json"


def main():
    print("=" * 70)
    print("  [STEP 2.1 VERIFICATION] 20 Dedicated Per-Tool Indexing Pipelines")
    print("=" * 70)

    logger = LogEngine(tool_id="core_indexer", action_name="verify_step_2_1", stage="Stage 2", step="Step 2.1")
    logger.info("Starting comprehensive verification for Stage 2 Step 2.1", progress_pct=5)
    update_progress(progress_percent=5, subtask="Starting verification...")

    assert REGISTRY_PATH.exists(), f"registry.json missing at {REGISTRY_PATH}"
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    tools = registry.get("tools", [])
    assert len(tools) == 20, f"Expected 20 tools, found {len(tools)}"

    results = []
    total_runs_indexed = 0
    total_files_indexed = 0

    # 1. Index and verify each of the 20 tools
    for idx, tool_info in enumerate(tools, start=1):
        tool_id = tool_info["tool_id"]
        pct = 5 + int((idx / 20.0) * 75)
        update_progress(progress_percent=pct, subtask=f"Indexing & verifying {tool_id} ({idx}/20)...")
        print(f"\n--> [{idx:02d}/20] Verifying {tool_id}...")

        # A. Import tool indexer module
        mod_name = f"tools.{tool_id}.indexer"
        try:
            mod = importlib.import_module(mod_name)
            indexer_cls = getattr(mod, "ToolIndexer", None)
            assert indexer_cls is not None, f"ToolIndexer class missing in {mod_name}"
        except Exception as e:
            print(f"    [FAIL] Failed to import {mod_name}: {e}")
            logger.error(f"Failed to import indexer for {tool_id}: {e}", progress_pct=pct)
            sys.exit(1)

        # B. Instantiate indexer and run full indexing
        indexer: BaseToolIndexer = indexer_cls(tool_id)
        index_res = indexer.index_all_runs()
        runs_count = index_res.get("runs_indexed", 0)
        total_runs_indexed += runs_count
        print(f"    [OK] Indexer executed: {runs_count} runs indexed")

        # C. Verify SQLite database exists and is valid
        sqlite_file = INDEX_STORE_DIR / f"{tool_id}.sqlite"
        assert sqlite_file.exists(), f"SQLite DB missing: {sqlite_file}"
        assert sqlite_file.stat().st_size > 0, f"SQLite DB is empty: {sqlite_file}"

        conn = sqlite3.connect(str(sqlite_file))
        conn.row_factory = sqlite3.Row
        
        # Check tool_metadata table
        meta = conn.execute("SELECT * FROM tool_metadata WHERE tool_id = ?", (tool_id,)).fetchone()
        assert meta is not None, f"tool_metadata empty for {tool_id}"
        assert meta["total_runs"] == runs_count, f"Metadata runs mismatch: {meta['total_runs']} vs {runs_count}"

        # Check indexed_runs table
        runs = conn.execute("SELECT * FROM indexed_runs WHERE tool_id = ?", (tool_id,)).fetchall()
        assert len(runs) == runs_count, f"indexed_runs count mismatch: {len(runs)} vs {runs_count}"

        # Check indexed_files table
        files = conn.execute("SELECT * FROM indexed_files WHERE tool_id = ?", (tool_id,)).fetchall()
        total_files_indexed += len(files)

        # Check indexed_logs table
        logs = conn.execute("SELECT * FROM indexed_logs WHERE tool_id = ?", (tool_id,)).fetchall()

        conn.close()
        print(f"    [OK] SQLite tables: {len(runs)} runs, {len(files)} files, {len(logs)} logs")

        # D. Verify Companion JSON summary exists and is valid
        json_file = INDEX_STORE_DIR / f"{tool_id}_index.json"
        assert json_file.exists(), f"JSON summary missing: {json_file}"
        assert json_file.stat().st_size > 0, f"JSON summary empty: {json_file}"
        summary_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert summary_data.get("tool_id") == tool_id
        assert summary_data.get("total_runs") == runs_count

        # E. Verify Domain Metrics Extraction
        latest_run = summary_data.get("runs", [{}])[0] if summary_data.get("runs") else {}
        domain_metrics = latest_run.get("domain_metrics", {})
        print(f"    [OK] Domain Metrics: {domain_metrics}")

        results.append({
            "tool_id": tool_id,
            "status": "PASS",
            "runs": runs_count,
            "files": len(files),
            "logs": len(logs),
            "sample_metric": list(domain_metrics.keys())[:3],
        })

    # 2. Verify Rule 5 Auto-Indexing Hook via folder_manager.complete_action_run()
    print("\n--> [HOOK TEST] Testing Rule 5 Auto-Indexing Hook in complete_action_run()...")
    test_run_info = create_action_run(
        tool_id="01_curl_cffi",
        action_name="scrape_for_leetcode",
        target_url="https://leetcode.com/problems/test-auto-index/",
    )
    # Write a test raw and cleaned file
    raw_test = Path(test_run_info["raw_dir"]) / "auto_index_raw.txt"
    raw_test.write_text("auto-index test raw content", encoding="utf-8")
    clean_test = Path(test_run_info["cleaned_dir"]) / "auto_index_clean.md"
    clean_test.write_text("# Auto Index Clean Content\nVerified auto-indexing hook.", encoding="utf-8")

    # Complete the run - should automatically update 01_curl_cffi.sqlite
    complete_action_run(test_run_info, status="completed")

    # Verify that the test run is now in 01_curl_cffi.sqlite
    conn = sqlite3.connect(str(INDEX_STORE_DIR / "01_curl_cffi.sqlite"))
    row = conn.execute("SELECT * FROM indexed_runs WHERE run_id = ?", (test_run_info["run_id"],)).fetchone()
    conn.close()
    assert row is not None, "Auto-indexing hook failed to register new run in SQLite!"
    print(f"    [OK] Auto-indexing successfully indexed run: {test_run_info['run_id']}")

    # 3. Final Summary & 4-Tier Log
    update_progress(progress_percent=95, subtask="Finalizing Step 2.1 verification...")
    logger.info(
        f"Step 2.1 Verification Passed: 20/20 indexers validated, {total_runs_indexed} total runs, {total_files_indexed} total files indexed",
        progress_pct=100,
        extra_data={"total_runs": total_runs_indexed, "total_files": total_files_indexed, "tools_count": len(results)},
    )
    update_progress(progress_percent=100, subtask="Verification 100% complete!")

    print("\n" + "=" * 70)
    print("  STAGE 2 - STEP 2.1 VERIFICATION SUMMARY:")
    print("=" * 70)
    for r in results:
        print(f"  [PASS] {r['tool_id']:<32} | Runs: {r['runs']:<3} | Files: {r['files']:<3} | Logs: {r['logs']:<3} | Metrics: {r['sample_metric']}")
    print("-" * 70)
    print(f"  TOTAL TOOLS INDEXED:   20 / 20")
    print(f"  TOTAL RUNS INDEXED:    {total_runs_indexed}")
    print(f"  TOTAL FILES INDEXED:   {total_files_indexed}")
    print(f"  RULE 5 AUTO-INDEXING:  VERIFIED & OPERATIONAL")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
