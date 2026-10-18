"""
core/verify_step_4_5.py
=======================
Focused Verification Suite for Stage 4 — Step 4.5:
Precision Task Router & Multi-Tool Chaining Engine (`core/task_router.py`),
Multi-Stage Pipeline Recipes, Predecessor Artifact Handoffs, and Unified Reporting.

Verifies:
1. Directory Setup & Canonical Pipeline Factory Recipes (GraphQL->MD, Stream->Whisper, Browser->OCR).
2. Live Execution of Recipe 1 (01_curl_cffi -> 16_crawl4ai): Data Fetch to Semantic Markdown Chunker.
3. Live Execution of Recipe 2 (11_yt_dlp_ffmpeg -> 20_faster_whisper_scrapegraph): Stream Demux to Whisper & Knowledge Graph.
4. Report Persistence (.json & .md in index_store/pipeline_reports/), Retrieval APIs, and FTS5 Master Sync.
5. Pre-Commit Secret Guard (Rule 6 Zero-Plaintext Security).
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

from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress
from core.task_router import PrecisionTaskRouter, PipelineStage

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
            step="Step 4.5",
            tool_id="task_router",
            action_name="verify_task_router",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.5",
            tool_id="task_router",
            action_name="verify_task_router",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("🚀 STARTING STAGE 4 STEP 4.5 VERIFICATION SUITE")
    print("   Precision Task Router: Multi-Tool Chaining & Artifact Handoffs")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 Step 4.5 verification suite...")
    router = PrecisionTaskRouter()

    # ------------------------------------------------------------------
    # Check 1: Directory Setup & Canonical Pipeline Factory
    # ------------------------------------------------------------------
    print("--- Check 1: Directory Setup & Canonical Pipeline Factory ---")
    update_progress(15, "Verifying pipeline reports directory and recipe builders...")

    reports_dir = router.reports_dir
    assert_check(
        "index_store/pipeline_reports/ exists and is a directory",
        reports_dir.exists() and reports_dir.is_dir(),
        f"Path: {reports_dir}",
    )

    test_file = reports_dir / ".write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        writable = test_file.exists() and test_file.read_text(encoding="utf-8") == "ok"
        test_file.unlink()
    except Exception:
        writable = False
    assert_check(
        "index_store/pipeline_reports/ is writable",
        writable,
        f"Writable check on {reports_dir}",
    )

    # Test Canonical Recipe Factories
    recipe1 = router.build_graphql_markdown_pipeline()
    recipe2 = router.build_stream_whisper_pipeline()
    recipe3 = router.build_browser_ocr_pipeline()

    assert_check(
        "build_graphql_markdown_pipeline() constructs valid 2-stage recipe",
        isinstance(recipe1, dict) and len(recipe1.get("stages", [])) == 2 and recipe1["stages"][0]["tool_id"] == "01_curl_cffi" and recipe1["stages"][1]["tool_id"] == "16_crawl4ai",
        f"Stages: {[s['tool_id'] for s in recipe1.get('stages', [])]}",
    )
    assert_check(
        "build_stream_whisper_pipeline() constructs valid 2-stage recipe",
        isinstance(recipe2, dict) and len(recipe2.get("stages", [])) == 2 and recipe2["stages"][0]["tool_id"] == "11_yt_dlp_ffmpeg" and recipe2["stages"][1]["tool_id"] == "20_faster_whisper_scrapegraph",
        f"Stages: {[s['tool_id'] for s in recipe2.get('stages', [])]}",
    )
    assert_check(
        "build_browser_ocr_pipeline() constructs valid 2-stage recipe",
        isinstance(recipe3, dict) and len(recipe3.get("stages", [])) == 2 and recipe3["stages"][0]["tool_id"] == "06_playwright" and recipe3["stages"][1]["tool_id"] == "17_surya_ocr",
        f"Stages: {[s['tool_id'] for s in recipe3.get('stages', [])]}",
    )

    # ------------------------------------------------------------------
    # Check 2: Live Execution of Recipe 1 (01_curl_cffi -> 16_crawl4ai)
    # ------------------------------------------------------------------
    print("\n--- Check 2: Live Execution of Recipe 1 (01_curl_cffi -> 16_crawl4ai) ---")
    update_progress(30, "Executing Recipe 1: 01_curl_cffi -> 16_crawl4ai on LeetCode/Quotes target...")

    t0_pipe1 = time.perf_counter()
    pipe1_result = router.execute_pipeline(
        pipeline_id=recipe1["pipeline_id"],
        target_url="https://quotes.toscrape.com",
        stages=recipe1["stages"],
        pipeline_label="Stage 4 Step 4.5 Test: GraphQL to Markdown Chunker",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
    )
    pipe1_elapsed = time.perf_counter() - t0_pipe1

    assert_check(
        "Recipe 1 completes successfully with completed status",
        isinstance(pipe1_result, dict) and pipe1_result.get("status") == "completed",
        f"Status: {pipe1_result.get('status')}, Error: {pipe1_result.get('error')}",
    )

    p1_stages = pipe1_result.get("stage_records", [])
    assert_check(
        "Recipe 1 executed both pipeline stages",
        len(p1_stages) == 2 and p1_stages[0]["tool_id"] == "01_curl_cffi" and p1_stages[1]["tool_id"] == "16_crawl4ai",
        f"Stages executed: {[s['tool_id'] for s in p1_stages]}",
    )

    p1_s2 = p1_stages[1] if len(p1_stages) > 1 else {}
    assert_check(
        "Stage 2 (16_crawl4ai) consumed predecessor artifacts from Stage 1 (01_curl_cffi)",
        len(p1_s2.get("artifacts_consumed", [])) > 0,
        f"Consumed: {p1_s2.get('artifacts_consumed')}",
    )

    assert_check(
        "Recipe 1 generated consolidated deliverables (llm_ready.md / semantic_chunks.json)",
        any(d["name"] in ["llm_ready.md", "semantic_chunks.json"] for d in pipe1_result.get("consolidated_deliverables", [])),
        f"Deliverables: {[d['name'] for d in pipe1_result.get('consolidated_deliverables', [])]}",
    )

    # ------------------------------------------------------------------
    # Check 3: Live Execution of Recipe 2 (11_yt_dlp_ffmpeg -> 20_faster_whisper)
    # ------------------------------------------------------------------
    print("\n--- Check 3: Live Execution of Recipe 2 (11_yt_dlp_ffmpeg -> 20_faster_whisper) ---")
    update_progress(55, "Executing Recipe 2: 11_yt_dlp_ffmpeg -> 20_faster_whisper_scrapegraph...")

    t0_pipe2 = time.perf_counter()
    pipe2_result = router.execute_pipeline(
        pipeline_id=recipe2["pipeline_id"],
        target_url="https://www.instagram.com/reel/C8XYZ12345/",
        stages=recipe2["stages"],
        pipeline_label="Stage 4 Step 4.5 Test: Media Demux to Whisper Transcription",
        human_mode=False,
    )
    pipe2_elapsed = time.perf_counter() - t0_pipe2

    assert_check(
        "Recipe 2 completes successfully with completed status",
        isinstance(pipe2_result, dict) and pipe2_result.get("status") == "completed",
        f"Status: {pipe2_result.get('status')}, Error: {pipe2_result.get('error')}",
    )

    p2_stages = pipe2_result.get("stage_records", [])
    assert_check(
        "Recipe 2 executed both media pipeline stages",
        len(p2_stages) == 2 and p2_stages[0]["tool_id"] == "11_yt_dlp_ffmpeg" and p2_stages[1]["tool_id"] == "20_faster_whisper_scrapegraph",
        f"Stages executed: {[s['tool_id'] for s in p2_stages]}",
    )

    p2_s2 = p2_stages[1] if len(p2_stages) > 1 else {}
    assert_check(
        "Stage 2 (20_faster_whisper) consumed demuxed audio artifact from Stage 1 (11_yt_dlp_ffmpeg)",
        len(p2_s2.get("artifacts_consumed", [])) > 0 and any("audio" in a["key"] or "wav" in a["key"] for a in p2_s2.get("artifacts_consumed", [])),
        f"Consumed: {p2_s2.get('artifacts_consumed')}",
    )

    assert_check(
        "Recipe 2 produced multimodal deliverables (transcript.srt, knowledge_graph.json)",
        any(d["name"] in ["transcript.srt", "knowledge_graph.json"] for d in pipe2_result.get("consolidated_deliverables", [])),
        f"Deliverables: {[d['name'] for d in pipe2_result.get('consolidated_deliverables', [])]}",
    )

    # ------------------------------------------------------------------
    # Check 4: Report Persistence & Master Index Synchronization
    # ------------------------------------------------------------------
    print("\n--- Check 4: Report Persistence & Master Index Synchronization ---")
    update_progress(80, "Verifying pipeline report documents and testing retrieval APIs...")

    report1_id = pipe1_result["report_id"]
    report2_id = pipe2_result["report_id"]

    json1_path = router.reports_dir / f"{report1_id}.json"
    md1_path = router.reports_dir / f"{report1_id}.md"
    json2_path = router.reports_dir / f"{report2_id}.json"
    md2_path = router.reports_dir / f"{report2_id}.md"

    assert_check(
        "Pipeline Recipe 1 JSON & Markdown reports persisted",
        json1_path.exists() and md1_path.exists() and json1_path.stat().st_size > 100 and md1_path.stat().st_size > 200,
        f"JSON: {json1_path.exists()}, MD: {md1_path.exists()}",
    )

    assert_check(
        "Pipeline Recipe 2 JSON & Markdown reports persisted",
        json2_path.exists() and md2_path.exists() and json2_path.stat().st_size > 100 and md2_path.stat().st_size > 200,
        f"JSON: {json2_path.exists()}, MD: {md2_path.exists()}",
    )

    # Test list_pipeline_reports API
    listed = router.list_pipeline_reports(limit=20)
    has_pipe1 = any(r.get("report_id") == report1_id for r in listed)
    has_pipe2 = any(r.get("report_id") == report2_id for r in listed)
    assert_check(
        "list_pipeline_reports() retrieves historical reports including recent runs",
        isinstance(listed, list) and has_pipe1 and has_pipe2,
        f"Total listed: {len(listed)}, Found pipe1: {has_pipe1}, Found pipe2: {has_pipe2}",
    )

    # Test get_pipeline_report API
    retrieved = router.get_pipeline_report(report1_id)
    assert_check(
        "get_pipeline_report() returns exact pipeline document",
        retrieved is not None and retrieved.get("report_id") == report1_id and "stage_records" in retrieved,
        f"Retrieved: {bool(retrieved)}",
    )

    # Verify Global Master Indexer synchronization
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() indexes pipeline runs and Stage 4 logs",
        isinstance(sync_stats, dict) and sync_stats.get("status") == "active" and "totals" in sync_stats,
        f"Master index totals: {sync_stats.get('totals')}",
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
    print(f"📊 STAGE 4 STEP 4.5 VERIFICATION RESULT: {PASSED_COUNT}/{total} CHECKS PASSED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        print(f"❌ Verification failed with {FAILED_COUNT} errors.")
        sys.exit(1)
    else:
        print("🎉 ALL STAGE 4 STEP 4.5 CHECKS COMPLETED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
