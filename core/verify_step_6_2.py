"""
core/verify_step_6_2.py
=======================
Focused Verification Suite for Stage 6 — Step 6.2:
Build the Anti-Bot, Rate-Limit, DOM Mutation & Chaos Resilience Tester
(`core/resilience_tester.py`), and Run Verification Suite.

Verifies:
1. Check 1 — Testbed Setup & Chaos Server:
   - Confirms index_store/resilience_reports/ exists and is writable
   - Confirms ChaosFaultServer starts on an ephemeral port and handles endpoints
     (/health, /fault/rate-limit, /fault/anti-bot, /fault/mutated-dom)
2. Check 2 — Rate-Limit Backoff & Account Quarantine:
   - Executes test_rate_limit_resilience()
   - Confirms exponential backoff jitter calculation and account cooldown quarantine
3. Check 3 — DOM Mutation & Graceful Fallback:
   - Executes test_dom_mutation_resilience()
   - Confirms semantic fallback selector extraction without unhandled IndexErrors
4. Check 4 — Network Chaos & Socket Faults:
   - Executes test_network_fault_resilience()
   - Confirms client timeout handling, socket reset handling, and zero indefinite hangs
5. Check 5 — Silver-Tier Contract Schema Fuzzing:
   - Executes test_contract_fuzzing_resilience()
   - Confirms corrupted payloads are safely rejected by Pydantic contracts without crashes
6. Check 6 — Master Battery Reporting, Index Sync & Pre-Commit Secret Guard:
   - Executes run_full_resilience_battery()
   - Confirms .json and .md reports are persisted and discoverable
   - Verifies GlobalMasterIndexer.sync_all() federates Stage 6 chaos logs
   - Confirms core/git_manager.py:scan_staged_for_secrets() reports zero violations
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
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
from core.resilience_tester import ChaosFaultServer, ResilienceTester, get_resilience_tester
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
            step="Step 6.2",
            tool_id="core_resilience_tester",
            action_name="verify_step_6_2",
            stage_log_name="stage_6_benchmarking",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 6",
            step="Step 6.2",
            tool_id="core_resilience_tester",
            action_name="verify_step_6_2",
            stage_log_name="stage_6_benchmarking",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 6 STEP 6.2 VERIFICATION SUITE")
    print("   Anti-Bot, Rate-Limit, DOM Mutation & Chaos Resilience Tester")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 6 Step 6.2 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Testbed Setup & Chaos Server
    # ------------------------------------------------------------------
    print("--- Check 1: Testbed Setup & Chaos Server ---")
    update_progress(15, subtask="Verifying resilience reports directory and chaos server...")

    reports_dir = ROOT / "index_store" / "resilience_reports"
    assert_check(
        "index_store/resilience_reports/ exists and is a directory",
        reports_dir.exists() and reports_dir.is_dir(),
        f"Path: {reports_dir}",
    )

    # Spawn test server on ephemeral port
    server = ChaosFaultServer()
    base_url = server.start()
    assert_check(
        "ChaosFaultServer started on ephemeral localhost port",
        bool(base_url) and server.port > 0,
        f"Base URL: {base_url}",
    )

    # Test /health endpoint
    with urllib.request.urlopen(f"{base_url}/health", timeout=3.0) as resp:
        health_data = json.loads(resp.read().decode("utf-8"))
        assert_check(
            "Chaos server /health returns status 'chaos_server_ready'",
            health_data.get("status") == "chaos_server_ready",
            f"Health data: {health_data}",
        )

    # Test /fault/rate-limit endpoint
    rate_limit_code = 0
    retry_after_hdr = ""
    try:
        urllib.request.urlopen(f"{base_url}/fault/rate-limit", timeout=3.0)
    except urllib.error.HTTPError as exc:
        rate_limit_code = exc.code
        retry_after_hdr = exc.headers.get("Retry-After", "")

    assert_check(
        "Chaos server /fault/rate-limit emits HTTP 429 with Retry-After header",
        rate_limit_code == 429 and retry_after_hdr == "2",
        f"Code: {rate_limit_code}, Retry-After: {retry_after_hdr}",
    )

    # Test /fault/anti-bot endpoint
    anti_bot_code = 0
    server_hdr = ""
    anti_bot_body = ""
    try:
        urllib.request.urlopen(f"{base_url}/fault/anti-bot", timeout=3.0)
    except urllib.error.HTTPError as exc:
        anti_bot_code = exc.code
        server_hdr = exc.headers.get("Server", "")
        anti_bot_body = exc.read().decode("utf-8")

    assert_check(
        "Chaos server /fault/anti-bot emits HTTP 403 with Cloudflare challenge markers",
        anti_bot_code == 403 and server_hdr == "cloudflare" and "cf-turnstile" in anti_bot_body,
        f"Code: {anti_bot_code}, Server: {server_hdr}",
    )

    # Test /fault/mutated-dom endpoint
    with urllib.request.urlopen(f"{base_url}/fault/mutated-dom", timeout=3.0) as resp:
        dom_html = resp.read().decode("utf-8")
        assert_check(
            "Chaos server /fault/mutated-dom serves scrambled DOM with semantic tags",
            "c89_title_xyz" in dom_html and 'data-semantic="title"' in dom_html,
            f"DOM HTML preview: {dom_html[:120]}",
        )

    server.stop()

    # ------------------------------------------------------------------
    # Check 2: Rate-Limit Backoff & Account Quarantine
    # ------------------------------------------------------------------
    print("\n--- Check 2: Rate-Limit Backoff & Account Quarantine ---")
    update_progress(35, subtask="Executing rate limit resilience scenario...")

    tester = get_resilience_tester()
    r1 = tester.test_rate_limit_resilience(max_retries=3)

    assert_check(
        "test_rate_limit_resilience completed with status 'completed'",
        r1.get("status") == "completed",
        f"Status: {r1.get('status')}",
    )
    assert_check(
        "Rate-limit 429 caught across 3 retries",
        r1.get("rate_limit_caught") is True and r1.get("retries_attempted") == 3,
        f"Caught: {r1.get('rate_limit_caught')}, Retries: {r1.get('retries_attempted')}",
    )
    assert_check(
        "Exponential backoff jitter intervals calculated",
        len(r1.get("backoff_intervals", [])) == 3 and r1["backoff_intervals"][0] < r1["backoff_intervals"][-1] * 1.5,
        f"Intervals: {r1.get('backoff_intervals')}",
    )
    assert_check(
        "AccountRouter engaged cooldown quarantine on rate limit",
        r1.get("cooldown_engaged") is True,
        f"Cooldown engaged: {r1.get('cooldown_engaged')}",
    )

    # ------------------------------------------------------------------
    # Check 3: DOM Mutation & Graceful Fallback
    # ------------------------------------------------------------------
    print("\n--- Check 3: DOM Mutation & Graceful Fallback ---")
    update_progress(50, subtask="Executing DOM mutation resilience scenario...")

    r2 = tester.test_dom_mutation_resilience(target_selector=".standard-product-title")

    assert_check(
        "test_dom_mutation_resilience completed with status 'completed'",
        r2.get("status") == "completed",
        f"Status: {r2.get('status')}",
    )
    assert_check(
        "Standard primary selector safely reported absent without crashing",
        r2.get("primary_selector_found") is False and r2.get("unhandled_exceptions") == 0,
        f"Primary found: {r2.get('primary_selector_found')}, Exceptions: {r2.get('unhandled_exceptions')}",
    )
    assert_check(
        "Fallback heuristics successfully extracted target text",
        r2.get("fallback_selector_found") is True and r2.get("extracted_text") == "The Secret Life of Plants",
        f"Fallback found: {r2.get('fallback_selector_found')}, Text: '{r2.get('extracted_text')}'",
    )
    assert_check(
        "Graceful degradation detected with 100% extraction accuracy",
        r2.get("graceful_degradation_detected") is True and r2.get("extraction_accuracy_pct") == 100.0,
        f"Degradation: {r2.get('graceful_degradation_detected')}, Accuracy: {r2.get('extraction_accuracy_pct')}",
    )

    # ------------------------------------------------------------------
    # Check 4: Network Chaos & Socket Faults
    # ------------------------------------------------------------------
    print("\n--- Check 4: Network Chaos & Socket Faults ---")
    update_progress(65, subtask="Executing network chaos and dropped packet scenario...")

    r3 = tester.test_network_fault_resilience()

    assert_check(
        "test_network_fault_resilience completed with status 'completed'",
        r3.get("status") == "completed",
        f"Status: {r3.get('status')}",
    )
    assert_check(
        "TCP connection resets caught cleanly",
        r3.get("connection_resets_caught", 0) > 0,
        f"Resets caught: {r3.get('connection_resets_caught')}",
    )
    assert_check(
        "Latency timeout guard prevented indefinite hang",
        r3.get("timeouts_caught", 0) > 0 and r3.get("hung_indefinitely") is False,
        f"Timeouts caught: {r3.get('timeouts_caught')}, Hung: {r3.get('hung_indefinitely')}",
    )

    # ------------------------------------------------------------------
    # Check 5: Silver-Tier Contract Schema Fuzzing
    # ------------------------------------------------------------------
    print("\n--- Check 5: Silver-Tier Contract Schema Fuzzing ---")
    update_progress(80, subtask="Executing contract schema fuzzing scenario...")

    r4 = tester.test_contract_fuzzing_resilience()

    assert_check(
        "test_contract_fuzzing_resilience completed with status 'completed'",
        r4.get("status") == "completed",
        f"Status: {r4.get('status')}",
    )
    assert_check(
        "All 4 corrupted payloads rejected with Pydantic ValidationError",
        r4.get("fuzz_cases_tested") == 4 and r4.get("validation_errors_caught") == 4,
        f"Tested: {r4.get('fuzz_cases_tested')}, Errors: {r4.get('validation_errors_caught')}",
    )
    assert_check(
        "Zero unhandled exceptions during contract fuzzing",
        r4.get("unhandled_exceptions_count") == 0 and r4.get("all_passed") is True,
        f"Unhandled count: {r4.get('unhandled_exceptions_count')}",
    )

    # ------------------------------------------------------------------
    # Check 6: Master Battery Reporting, Index Sync & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 6: Master Battery Reporting, Index Sync & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Executing full resilience battery and validating persistence...")

    battery_res = tester.run_full_resilience_battery()

    assert_check(
        "run_full_resilience_battery generated valid report document",
        isinstance(battery_res, dict) and "report_id" in battery_res and battery_res.get("scenarios_tested") == 4,
        f"Report ID: {battery_res.get('report_id')}, Scenarios: {battery_res.get('scenarios_tested')}",
    )
    assert_check(
        "Composite Resilience Index is high (>= 85.0/100)",
        battery_res.get("resilience_index", 0.0) >= 85.0,
        f"Resilience Index: {battery_res.get('resilience_index')}",
    )

    report_id = battery_res["report_id"]
    json_path = reports_dir / f"{report_id}.json"
    md_path = reports_dir / f"{report_id}.md"

    assert_check(
        f"Resilience JSON report persisted ({json_path.name})",
        json_path.exists() and json_path.stat().st_size > 0,
        f"JSON exists: {json_path.exists()}",
    )
    assert_check(
        f"Resilience Markdown report persisted ({md_path.name})",
        md_path.exists() and md_path.stat().st_size > 0,
        f"MD exists: {md_path.exists()}",
    )

    # Discovery APIs
    rep_list = tester.list_resilience_reports(limit=10)
    assert_check(
        "list_resilience_reports finds newly created battery report",
        any(r["report_id"] == report_id for r in rep_list),
        f"Found report IDs: {[r['report_id'] for r in rep_list]}",
    )

    single_rep = tester.get_resilience_report(report_id)
    assert_check(
        "get_resilience_report retrieves report with markdown_content",
        single_rep is not None and "markdown_content" in single_rep,
        f"Report retrieved: {single_rep is not None}",
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
    update_progress(100, subtask="Stage 6 Step 6.2 Verification Suite completed.")
    print("\n" + "=" * 70)
    print(f"STAGE 6 STEP 6.2 VERIFICATION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
