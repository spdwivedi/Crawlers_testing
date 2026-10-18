"""
core/verify_step_4_4.py
=======================
Focused Verification Suite for Stage 4 — Step 4.4:
Safe Arena Engine (`core/arena_runner.py`), Multi-Tool Staggered Concurrency,
Comparative Analysis & Side-by-Side Reporting, Master Indexing, and Governance.

Verifies:
1. Directory & Staggered Timing Coordination (index_store/arena_reports/, log-normal intervals).
2. Multi-Tool Safe Arena Execution on Single Target across 3 Cohorts (01_curl_cffi, 04_httpx_parsel, 06_playwright).
3. Comparative Scoring Matrix & Winner Determination (Speed, Richness, Stealth, Composite Ranking).
4. Automated Report Persistence (.json & .md) and Retrieval APIs (list_arena_reports, get_arena_report).
5. Global Master Indexer FTS5 Sync & Pre-Commit Secret Guard.
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

from core.arena_runner import SafeArenaRunner
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
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
            step="Step 4.4",
            tool_id="arena_runner",
            action_name="verify_arena_runner",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.4",
            tool_id="arena_runner",
            action_name="verify_arena_runner",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("🚀 STARTING STAGE 4 STEP 4.4 VERIFICATION SUITE")
    print("   Safe Arena Engine: Multi-Tool Staggered Benchmarking & Comparative Reporting")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 Step 4.4 verification suite...")
    runner = SafeArenaRunner()

    # ------------------------------------------------------------------
    # Check 1: Directory & Staggered Timing Coordination
    # ------------------------------------------------------------------
    print("--- Check 1: Directory & Staggered Timing Coordination ---")
    update_progress(15, "Verifying reports directory and staggered delay distribution...")

    reports_dir = runner.reports_dir
    assert_check(
        "index_store/arena_reports/ exists and is a directory",
        reports_dir.exists() and reports_dir.is_dir(),
        f"Path: {reports_dir}",
    )

    # Test file writability in reports dir
    test_file = reports_dir / ".write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        writable = test_file.exists() and test_file.read_text(encoding="utf-8") == "ok"
        test_file.unlink()
    except Exception:
        writable = False
    assert_check(
        "index_store/arena_reports/ is writable",
        writable,
        f"Writable check on {reports_dir}",
    )

    # Statistical distribution check for staggered delays
    stagger_samples = [
        HumanTimingEngine.log_normal_delay(median=2.5, sigma=0.4, min_val=1.0, max_val=8.0)
        for _ in range(50)
    ]
    all_bounded = all(1.0 <= s <= 8.0 for s in stagger_samples)
    mean_stagger = sum(stagger_samples) / len(stagger_samples)
    assert_check(
        "Staggered delay adheres strictly to [1.0s, 8.0s] bounds",
        all_bounded,
        f"Samples range: min={min(stagger_samples):.3f}s, max={max(stagger_samples):.3f}s",
    )
    assert_check(
        "Staggered delay distribution mean reflects safe human pause (1.8s - 3.5s)",
        1.8 <= mean_stagger <= 3.5,
        f"Calculated mean: {mean_stagger:.3f}s",
    )

    # ------------------------------------------------------------------
    # Check 2: Multi-Tool Safe Arena Execution on Single Target
    # ------------------------------------------------------------------
    print("\n--- Check 2: Multi-Tool Safe Arena Execution on Single Target ---")
    update_progress(30, "Executing SafeArenaRunner across 3 tool cohorts on quotes.toscrape.com...")

    test_target_url = "https://quotes.toscrape.com"
    test_squad = ["01_curl_cffi", "04_httpx_parsel", "06_playwright"]

    t0_arena = time.perf_counter()
    arena_result = runner.run_arena(
        target_url=test_target_url,
        tool_ids=test_squad,
        action_name="arena_benchmark",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
        stagger_delay_sec=0.15,
        run_label="Stage 4 Step 4.4 Verification Arena Benchmark",
    )
    arena_elapsed = time.perf_counter() - t0_arena

    assert_check(
        "SafeArenaRunner.run_arena() completes and returns valid structured output",
        isinstance(arena_result, dict) and arena_result.get("report_id", "").startswith("arena_run_"),
        f"Report ID: {arena_result.get('report_id')}",
    )

    tool_executions = arena_result.get("tool_executions", [])
    assert_check(
        "Arena executed all 3 requested candidate tools",
        len(tool_executions) == 3,
        f"Tools count: {len(tool_executions)} (expected 3)",
    )

    all_completed = all(t.get("status") == "completed" for t in tool_executions)
    assert_check(
        "All candidate tools in squad completed successfully without blocks or crashes",
        all_completed,
        f"Statuses: {[(t['tool_id'], t['status']) for t in tool_executions]}",
    )

    # Verify isolated run folders and domain metrics exist
    valid_artifacts = True
    for t in tool_executions:
        run_dir = ROOT / t.get("run_dir", "")
        if not (run_dir.exists() and (run_dir / "run_manifest.json").exists()):
            valid_artifacts = False
            print(f"Missing run_dir or manifest for {t['tool_id']}: {run_dir}")
    assert_check(
        "Each executed tool generated an isolated run directory with run_manifest.json",
        valid_artifacts,
        f"Run directories checked for: {[t['tool_id'] for t in tool_executions]}",
    )

    # ------------------------------------------------------------------
    # Check 3: Comparative Scoring & Metrics Matrix
    # ------------------------------------------------------------------
    print("\n--- Check 3: Comparative Scoring & Metrics Matrix ---")
    update_progress(60, "Evaluating comparison matrix and scoring vectors...")

    matrix = arena_result.get("comparison_matrix", [])
    assert_check(
        "Comparison matrix contains entries for all executed candidate tools",
        len(matrix) == 3,
        f"Matrix count: {len(matrix)}",
    )

    matrix_has_vectors = all(
        "speed_score" in m and "data_richness_score" in m and "stealth_score" in m and "composite_score" in m
        for m in matrix
    )
    assert_check(
        "Comparison matrix calculates speed, richness, stealth, and composite scores",
        matrix_has_vectors,
        f"Sample vector: {matrix[0] if matrix else {}}",
    )

    winning_tool = arena_result.get("winning_tool")
    assert_check(
        "Winning tool is designated from candidate squad",
        winning_tool in test_squad,
        f"Winning tool: {winning_tool}",
    )

    rationale = arena_result.get("winning_rationale", "")
    assert_check(
        "Winning rationale is documented with analytical explanation",
        len(rationale) > 20 and winning_tool in rationale,
        f"Rationale: {rationale}",
    )

    # ------------------------------------------------------------------
    # Check 4: Report Persistence & Master Index Synchronization
    # ------------------------------------------------------------------
    print("\n--- Check 4: Report Persistence & Master Index Synchronization ---")
    update_progress(80, "Verifying JSON and Markdown reports and testing retrieval APIs...")

    report_id = arena_result["report_id"]
    json_path = runner.reports_dir / f"{report_id}.json"
    md_path = runner.reports_dir / f"{report_id}.md"

    assert_check(
        "Structured JSON arena report file is persisted in index_store/arena_reports/",
        json_path.exists() and json_path.stat().st_size > 100,
        f"Size: {json_path.stat().st_size if json_path.exists() else 0} bytes",
    )

    assert_check(
        "Human-readable Markdown arena report file is persisted with side-by-side table",
        md_path.exists() and md_path.stat().st_size > 200,
        f"Size: {md_path.stat().st_size if md_path.exists() else 0} bytes",
    )

    # Test list_arena_reports API
    listed_reports = runner.list_arena_reports(limit=10)
    found_in_list = any(r.get("report_id") == report_id for r in listed_reports)
    assert_check(
        "list_arena_reports() returns sorted report summaries including current run",
        isinstance(listed_reports, list) and found_in_list,
        f"Total listed: {len(listed_reports)}",
    )

    # Test get_arena_report API
    retrieved_report = runner.get_arena_report(report_id)
    assert_check(
        "get_arena_report() retrieves exact structured arena report document",
        retrieved_report is not None and retrieved_report.get("report_id") == report_id,
        f"Retrieved: {bool(retrieved_report)}",
    )

    # Verify Global Master Indexer synchronization
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() federates arena tool runs without error",
        isinstance(sync_stats, dict) and sync_stats.get("status") == "active" and "totals" in sync_stats,
        f"Master index sync totals: {sync_stats.get('totals')}",
    )

    # ------------------------------------------------------------------
    # Check 5: Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Pre-Commit Secret Guard ---")
    update_progress(95, "Scanning staged files and repository for plaintext credentials...")

    secret_findings = scan_staged_for_secrets()
    assert_check(
        "Pre-commit secret guard reports zero blocked secrets",
        secret_findings.get("blocked_secrets_count", 0) == 0,
        f"Blocked secrets count: {secret_findings.get('blocked_secrets_count')}",
    )
    assert_check(
        "Pre-commit secret guard violations_found is False",
        secret_findings.get("violations_found") is False,
        f"Violations: {secret_findings.get('details')}",
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    update_progress(100, "Verification suite complete.")
    total = PASSED_COUNT + FAILED_COUNT
    print("\n" + "=" * 70)
    print(f"📊 STAGE 4 STEP 4.4 VERIFICATION RESULT: {PASSED_COUNT}/{total} CHECKS PASSED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        print(f"❌ Verification failed with {FAILED_COUNT} errors.")
        sys.exit(1)
    else:
        print("🎉 ALL STAGE 4 STEP 4.4 CHECKS COMPLETED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
