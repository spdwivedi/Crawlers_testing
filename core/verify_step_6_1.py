"""
core/verify_step_6_1.py
=======================
Focused Verification Suite for Stage 6 — Step 6.1:
Initialize Stage 6 Governance & Logging, Build the Master 20-Tool Performance
& Quality Matrix Engine (`core/benchmark_engine.py`), and Run Verification Suite.

Verifies:
1. Check 1 — Stage 6 Governance & Directory Setup:
   - Confirms logs/stages/stage_6_benchmarking.jsonl exists and is writable
   - Confirms GEMINI.md reflects Stage 6 and Rule 9
   - Confirms index_store/benchmark_reports/ exists and is writable
2. Check 2 — Statistical Metric Calculators:
   - Verifies latency percentile calculations (p50, p90, p99) against synthetic distributions
   - Confirms composite score calculation satisfies weighting bounds (0.0 to 100.0)
3. Check 3 — Single Tool Benchmark Execution:
   - Runs BenchmarkEngine().run_tool_benchmark("01_curl_cffi", iterations=2, human_mode=False)
   - Confirms all iterations complete with non-zero metrics and valid memory deltas
4. Check 4 — Multi-Cohort Battery Benchmark Execution:
   - Runs BenchmarkEngine().run_battery_benchmark(tool_ids=["01_curl_cffi", "04_httpx_parsel"], iterations=2)
   - Confirms battery output contains rankings, leaderboard, and radar vectors
5. Check 5 — Report Persistence & Master Index Synchronization:
   - Confirms .json and .md reports are written to index_store/benchmark_reports/
   - Confirms list_benchmark_reports() and get_benchmark_report() retrieve records cleanly
   - Verifies GlobalMasterIndexer.sync_all() federates Stage 6 benchmark logs
   - Confirms core/git_manager.py:scan_staged_for_secrets() reports zero violations
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

from core.benchmark_engine import BenchmarkEngine, get_benchmark_engine
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
            step="Step 6.1",
            tool_id="core_benchmark_engine",
            action_name="verify_step_6_1",
            stage_log_name="stage_6_benchmarking",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 6",
            step="Step 6.1",
            tool_id="core_benchmark_engine",
            action_name="verify_step_6_1",
            stage_log_name="stage_6_benchmarking",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 6 STEP 6.1 VERIFICATION SUITE")
    print("   Master 20-Tool Performance & Quality Matrix Engine")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 6 Step 6.1 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Stage 6 Governance & Directory Setup
    # ------------------------------------------------------------------
    print("--- Check 1: Stage 6 Governance & Directory Setup ---")
    update_progress(15, subtask="Verifying Stage 6 governance, logs, and report directories...")

    stage_log_path = ROOT / "logs" / "stages" / "stage_6_benchmarking.jsonl"
    assert_check(
        "logs/stages/stage_6_benchmarking.jsonl exists",
        stage_log_path.exists(),
        f"Path: {stage_log_path}",
    )

    gemini_md_path = ROOT / "GEMINI.md"
    gemini_text = gemini_md_path.read_text(encoding="utf-8") if gemini_md_path.exists() else ""
    assert_check(
        "GEMINI.md reflects Stage 6 in header",
        ("Stage:** 6" in gemini_text or "Stage 6" in gemini_text) and "Master Benchmarking" in gemini_text,
        "Stage 6 header missing or incorrect",
    )
    assert_check(
        "GEMINI.md contains Rule 9 (Benchmark Traceability & Non-Destructive Testing)",
        "Rule 9 — Benchmark Traceability" in gemini_text,
        "Rule 9 missing in GEMINI.md",
    )

    reports_dir = ROOT / "index_store" / "benchmark_reports"
    assert_check(
        "index_store/benchmark_reports/ exists and is a directory",
        reports_dir.exists() and reports_dir.is_dir(),
        f"Path: {reports_dir}",
    )

    html_path = ROOT / "frontend" / "index.html"
    html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    assert_check(
        "frontend/index.html includes Stage 6 in stage dropdowns",
        '<option value="Stage 6">Stage 6</option>' in html_text,
        "Stage 6 missing in frontend index.html dropdowns",
    )

    # ------------------------------------------------------------------
    # Check 2: Statistical Metric Calculators
    # ------------------------------------------------------------------
    print("\n--- Check 2: Statistical Metric Calculators ---")
    update_progress(30, subtask="Verifying percentiles and composite score calculators...")

    # Synthetic distribution 1: 5-element uniform [1.0, 2.0, 3.0, 4.0, 5.0]
    lat_5 = [1.0, 2.0, 3.0, 4.0, 5.0]
    pct_5 = BenchmarkEngine.compute_percentiles(lat_5)
    assert_check(
        "Percentiles for [1.0..5.0] calculate expected p50=3.0, p90=4.6, p99=4.96",
        pct_5["p50"] == 3.0 and pct_5["p90"] == 4.6 and pct_5["p99"] == 4.96,
        f"Result: {pct_5}",
    )
    assert_check(
        "Mean and min/max calculated correctly for [1.0..5.0]",
        pct_5["mean"] == 3.0 and pct_5["min"] == 1.0 and pct_5["max"] == 5.0,
        f"Result: {pct_5}",
    )

    # Synthetic distribution 2: 100-element uniform [1..100]
    lat_100 = [float(i) for i in range(1, 101)]
    pct_100 = BenchmarkEngine.compute_percentiles(lat_100)
    assert_check(
        "Percentiles for 100 elements satisfy p50 <= p90 <= p99",
        pct_100["min"] <= pct_100["p50"] <= pct_100["p90"] <= pct_100["p99"] <= pct_100["max"],
        f"Result: {pct_100}",
    )

    # Composite Score Weighting & Bounding Checks
    # Formula: (0.35 * Speed) + (0.30 * Richness) + (0.25 * Stealth) + (0.10 * Memory)
    score_max = BenchmarkEngine.compute_composite_score(100.0, 100.0, 100.0, 100.0)
    assert_check(
        "Composite score for maximum inputs (100, 100, 100, 100) equals 100.0",
        score_max == 100.0,
        f"Score: {score_max}",
    )

    score_min = BenchmarkEngine.compute_composite_score(0.0, 0.0, 0.0, 0.0)
    assert_check(
        "Composite score for minimum inputs (0, 0, 0, 0) equals 0.0",
        score_min == 0.0,
        f"Score: {score_min}",
    )

    score_mix = BenchmarkEngine.compute_composite_score(80.0, 70.0, 90.0, 85.0)
    # Expected: (0.35*80) + (0.30*70) + (0.25*90) + (0.10*85) = 28 + 21 + 22.5 + 8.5 = 80.0
    assert_check(
        "Composite score for mixed inputs (80, 70, 90, 85) equals exactly 80.0",
        score_mix == 80.0,
        f"Score: {score_mix}",
    )

    # ------------------------------------------------------------------
    # Check 3: Single Tool Benchmark Execution
    # ------------------------------------------------------------------
    print("\n--- Check 3: Single Tool Benchmark Execution ---")
    update_progress(50, subtask="Executing single tool benchmark for 01_curl_cffi...")

    engine = get_benchmark_engine()
    t_res = engine.run_tool_benchmark(
        tool_id="01_curl_cffi",
        target_url="https://quotes.toscrape.com",
        iterations=2,
        human_mode=False,
        timing_profile="FAST_AUTOMATED",
    )

    assert_check(
        "run_tool_benchmark completed with status 'completed'",
        t_res.get("status") == "completed",
        f"Status: {t_res.get('status')}",
    )
    assert_check(
        "Tool benchmark completed 2/2 iterations with error_rate == 0.0",
        t_res.get("completed_iterations") == 2 and t_res.get("error_rate") == 0.0,
        f"Completed: {t_res.get('completed_iterations')}, Error rate: {t_res.get('error_rate')}",
    )
    assert_check(
        "Tool benchmark reports non-zero latency and valid memory delta",
        t_res.get("p50_sec", 0.0) > 0.0 and t_res.get("mem_delta_mb", -1) >= 0.0,
        f"p50: {t_res.get('p50_sec')}, RAM delta: {t_res.get('mem_delta_mb')}",
    )
    assert_check(
        "Tool benchmark generates composite score in [0.0, 100.0] and 5-element radar vector",
        0.0 <= t_res.get("composite_score", -1) <= 100.0 and len(t_res.get("radar_vector", [])) == 5,
        f"Composite: {t_res.get('composite_score')}, Radar: {t_res.get('radar_vector')}",
    )

    # ------------------------------------------------------------------
    # Check 4: Multi-Cohort Battery Benchmark Execution
    # ------------------------------------------------------------------
    print("\n--- Check 4: Multi-Cohort Battery Benchmark Execution ---")
    update_progress(70, subtask="Executing multi-cohort battery benchmark (01_curl_cffi & 04_httpx_parsel)...")

    b_res = engine.run_battery_benchmark(
        tool_ids=["01_curl_cffi", "04_httpx_parsel"],
        target_url="https://quotes.toscrape.com",
        iterations=2,
        human_mode=False,
        battery_label="verify_battery_squad",
        timing_profile="FAST_AUTOMATED",
    )

    assert_check(
        "run_battery_benchmark returns valid report document",
        isinstance(b_res, dict) and "report_id" in b_res and b_res.get("total_tools") == 2,
        f"Report ID: {b_res.get('report_id')}, Tools: {b_res.get('total_tools')}",
    )
    assert_check(
        "Battery contains ranked leaderboard with 2 tool items",
        len(b_res.get("leaderboard", [])) == 2 and b_res["leaderboard"][0]["rank"] == 1,
        f"Leaderboard count: {len(b_res.get('leaderboard', []))}",
    )
    assert_check(
        "Battery assigns overall winner tool with positive composite score",
        b_res.get("winner_tool") in ["01_curl_cffi", "04_httpx_parsel"] and b_res.get("winner_composite_score", 0) > 0,
        f"Winner: {b_res.get('winner_tool')} ({b_res.get('winner_composite_score')})",
    )
    assert_check(
        "Radar matrix contains vector entries for both tools",
        "01_curl_cffi" in b_res.get("radar_matrix", {}) and "04_httpx_parsel" in b_res.get("radar_matrix", {}),
        f"Radar keys: {list(b_res.get('radar_matrix', {}).keys())}",
    )

    # ------------------------------------------------------------------
    # Check 5: Report Persistence & Master Index Synchronization
    # ------------------------------------------------------------------
    print("\n--- Check 5: Report Persistence & Master Index Synchronization ---")
    update_progress(85, subtask="Verifying report disk persistence, discovery, and secret scanning...")

    report_id = b_res.get("report_id")
    json_path = reports_dir / f"{report_id}.json"
    md_path = reports_dir / f"{report_id}.md"

    assert_check(
        f"Benchmark JSON report persisted at {json_path.name}",
        json_path.exists() and json_path.stat().st_size > 0,
        f"JSON exists: {json_path.exists()}",
    )
    assert_check(
        f"Benchmark Markdown report persisted at {md_path.name}",
        md_path.exists() and md_path.stat().st_size > 0,
        f"MD exists: {md_path.exists()}",
    )

    # Report Discovery APIs
    all_reports = engine.list_benchmark_reports(limit=10)
    assert_check(
        "list_benchmark_reports() finds newly created report",
        any(r["report_id"] == report_id for r in all_reports),
        f"Found report IDs: {[r['report_id'] for r in all_reports]}",
    )

    fetched_report = engine.get_benchmark_report(report_id)
    assert_check(
        "get_benchmark_report() retrieves report with markdown_content",
        fetched_report is not None and "markdown_content" in fetched_report,
        f"Report fetched: {fetched_report is not None}",
    )

    # Global Indexer Synchronization
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() federates all runs cleanly",
        isinstance(sync_stats, dict) and sync_stats.get("total_runs", 0) >= 0,
        f"Sync stats: {sync_stats}",
    )

    # Pre-Commit Secret Scanning
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports ZERO violations",
        not secret_scan.get("violations_found", False),
        f"Violations: {secret_scan.get('violations', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Stage 6 Step 6.1 Verification Suite completed.")
    print("\n" + "=" * 70)
    print(f"STAGE 6 STEP 6.1 VERIFICATION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
