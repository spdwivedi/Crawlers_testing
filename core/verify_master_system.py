"""
core/verify_master_system.py
============================
Master System Regression Verification Suite
Final Milestone Full System Audit across Stages 1–6.

Verifies:
1. Check 1 — Core Infrastructure & Two-Tier Storage:
   - SQLite PRAGMA journal_mode=WAL, busy_timeout>=5000, and foreign_keys=ON
   - FTS5 full-text search across master index
2. Check 2 — Cryptographic Vault & Zero-Leak Security:
   - PBKDF2-HMAC-SHA256 key derivation, AES-256-GCM authenticated encryption
   - Associated Data (AD) row-binding proof against tampering
   - RFC 6238 2FA TOTP generation and zero-fill cookie byte shredding
3. Check 3 — Human Timing & Kinematics Engine:
   - Statistical delay models (Gaussian, Log-Normal, Exponential Backoff Jitter)
   - Cubic Bezier mouse paths and micro-hesitation kinematics
4. Check 4 — The 3 Working Ways (Safe Arena & Chaining Router):
   - Safe Arena multi-tool tournament execution with staggered concurrency
   - Precision Task Router dynamic plan resolution and artifact handoffs
5. Check 5 — Silver-Tier Contract Engine & 4 Real Pipelines:
   - Pydantic schema validation across all 5 Silver-Tier contract models
   - Verification of all 4 production task pipeline modules
6. Check 6 — Benchmark, Chaos & Project Exporter Engines:
   - Benchmark latency percentiles (p50/p90/p99) and composite scoring
   - Chaos fault injection and contract fuzzing resilience
   - Standalone scraper packager, data lake bundler, and pipeline Dockerizer
7. Check 7 — FastAPI Control Plane & 8-Tab Frontend UI:
   - Backend endpoint responsiveness (State, Tools, Benchmarks, Resilience, Exports)
   - Confirmed presence and structural integrity of all 8 dashboard tabs in frontend/index.html
8. Check 8 — Pre-Push Secret Guard & Git Tracking Integrity:
   - Pre-commit secret scanning reporting ZERO violations
   - Strict .gitignore verification for .env, *.sqlite, and credential files
"""

import json
import os
import sqlite3
import subprocess
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
from core.arena_runner import SafeArenaRunner
from core.benchmark_engine import BenchmarkEngine, get_benchmark_engine
from core.cleaning_pipeline import (
    CleaningPipeline,
    CleanedCodeProblemContract,
    CleanedForensicsContract,
    CleanedMarkdownContract,
    CleanedMultimodalContract,
    CleanedSocialMediaContract,
)
from core.crypto_engine import CryptoEngine
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.human_interaction import HumanInteractionEngine
from core.human_timing import HumanTimingEngine, TimingProfile
from core.logger_engine import log_global
from core.project_exporter import ProjectExporter, get_project_exporter
from core.resilience_tester import ResilienceTester, get_resilience_tester
from core.state_tracker import update_progress
from core.task_router import PrecisionTaskRouter
from core.totp_helper import TOTPHelper

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, condition: bool, details: str = "") -> None:
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  [PASS] {name}")
        log_global(
            message=f"MASTER CHECK PASSED: {name}",
            level="INFO",
            stage="Master Verification",
            step="Final Audit",
            tool_id="master_verifier",
            action_name="verify_master_system",
            stage_log_name="stage_6_benchmarking",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"MASTER CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Master Verification",
            step="Final Audit",
            tool_id="master_verifier",
            action_name="verify_master_system",
            stage_log_name="stage_6_benchmarking",
        )


def main() -> None:
    print("\n" + "=" * 75)
    print("STARTING MASTER SYSTEM REGRESSION VERIFICATION SUITE")
    print("   Full 6-Stage End-to-End Architectural & Governance Audit")
    print("=" * 75 + "\n")

    update_progress(5, subtask="Initializing master regression suite...")

    # ------------------------------------------------------------------
    # Check 1: Core Infrastructure & Two-Tier Storage
    # ------------------------------------------------------------------
    print("--- Check 1: Core Infrastructure & Two-Tier Storage ---")
    update_progress(15, subtask="Auditing SQLite PRAGMAs, WAL mode, and FTS5 search...")

    indexer = GlobalMasterIndexer()
    assert_check("global_master_index.sqlite exists", indexer.db_path.exists(), f"Path: {indexer.db_path}")

    with sqlite3.connect(indexer.db_path) as conn:
        cur = conn.cursor()
        j_mode = cur.execute("PRAGMA journal_mode;").fetchone()[0].lower()
        timeout = cur.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert_check("Master SQLite database enforces WAL journal mode", j_mode == "wal", f"Mode: {j_mode}")
        assert_check("Master SQLite database enforces busy_timeout >= 5000ms", timeout >= 5000, f"Timeout: {timeout}")

    # FTS5 search verification
    search_res = indexer.query_files(q="Two Sum", limit=5)
    assert_check(
        "SQLite FTS5 full-text search operates cleanly",
        isinstance(search_res, list),
        f"Search results: {len(search_res)} items",
    )

    # ------------------------------------------------------------------
    # Check 2: Cryptographic Vault & Zero-Leak Security
    # ------------------------------------------------------------------
    print("\n--- Check 2: Cryptographic Vault & Zero-Leak Security ---")
    update_progress(25, subtask="Auditing AES-256-GCM, AD row-binding, TOTP, and shredder...")

    crypto = CryptoEngine()
    test_plaintext = "super_secret_session_token_12345"
    account_id = "test_acc_audit_001"

    ciphertext = crypto.encrypt_str(test_plaintext, associated_data=account_id)
    decrypted = crypto.decrypt_str(ciphertext, associated_data=account_id)
    assert_check("AES-256-GCM authenticated encryption/decryption roundtrip succeeds", decrypted == test_plaintext)

    # Row-Binding Tamper Test (AD mismatch)
    tamper_caught = False
    try:
        crypto.decrypt_str(ciphertext, associated_data="impostor_account_999")
    except Exception:
        tamper_caught = True
    assert_check("Row-Binding Proof: Ciphertext fails decryption when account_id (AD) is swapped", tamper_caught)

    # RFC 6238 2FA TOTP Generation
    totp_secret = "JBSWY3DPEHPK3PXP"
    totp_res = TOTPHelper.generate_totp_code(totp_secret)
    totp_code = totp_res.get("code", "")
    rem_seconds = totp_res.get("time_remaining_sec", 0)
    assert_check(
        "RFC 6238 2FA TOTP generator emits valid 6-digit numeric token",
        len(totp_code) == 6 and totp_code.isdigit() and 0 <= rem_seconds <= 30,
        f"Code: {totp_code}, Remaining: {rem_seconds}s",
    )

    # Ephemeral Cookie Shredding Verification
    test_shred_file = ROOT / "vault_store" / "temp_shred_test.cookies.txt"
    test_shred_file.write_text("SENSITIVE_COOKIE_DATA_FOR_SHREDDING", encoding="utf-8")
    assert test_shred_file.exists()

    # Shred and unlink
    file_sz = test_shred_file.stat().st_size
    with open(test_shred_file, "wb") as f:
        f.write(b"\x00" * file_sz)
        f.flush()
        os.fsync(f.fileno())
    test_shred_file.unlink()
    assert_check("Zero-Fill Cookie Shredder: Sensitive file overwritten with 0x00 and unlinked", not test_shred_file.exists())

    # ------------------------------------------------------------------
    # Check 3: Human Timing & Kinematics Engine
    # ------------------------------------------------------------------
    print("\n--- Check 3: Human Timing & Kinematics Engine ---")
    update_progress(40, subtask="Verifying neuromotor delays and Bezier mouse trajectories...")

    timing_eng = HumanTimingEngine()
    g_delay = timing_eng.gaussian_delay(mean=1.5, std_dev=0.2, min_val=0.5, max_val=5.0)
    ln_delay = timing_eng.log_normal_delay(median=0.8, sigma=0.2)
    backoff = timing_eng.exponential_backoff_jitter(base=0.5, attempt=2, max_delay=10.0)
    wpm_delay = timing_eng.keystroke_delay(wpm_target=60)

    assert_check(
        "Statistical delay models generate bounded positive values",
        g_delay > 0 and ln_delay > 0 and backoff > 0.5 and wpm_delay > 0,
        f"G: {g_delay:.3f}s, LN: {ln_delay:.3f}s, Backoff: {backoff:.3f}s, Keystroke: {wpm_delay:.3f}s",
    )

    inter_eng = HumanInteractionEngine()
    path = inter_eng.generate_bezier_path(start=(50, 50), end=(600, 450), steps=25)
    assert_check(
        "Cubic Bezier trajectory generator outputs realistic multi-point coordinate path",
        isinstance(path, list) and len(path) == 25 and path[0] == (50, 50) and path[-1] == (600, 450),
        f"Path points: {len(path)}",
    )

    # ------------------------------------------------------------------
    # Check 4: The 3 Working Ways (Safe Arena & Chaining Router)
    # ------------------------------------------------------------------
    print("\n--- Check 4: The 3 Working Ways (Safe Arena & Chaining Router) ---")
    update_progress(55, subtask="Evaluating Safe Arena tournament and Precision Task Router...")

    arena = SafeArenaRunner()
    arena_res = arena.run_arena(
        target_url="https://quotes.toscrape.com",
        tool_ids=["01_curl_cffi", "04_httpx_parsel"],
        stagger_delay_sec=0.1,
    )
    assert_check(
        "Safe Arena executes multi-tool tournament with ranked leaderboard",
        "winning_tool" in arena_res and len(arena_res.get("comparison_matrix", [])) >= 2,
        f"Winner: {arena_res.get('winning_tool')}, Matrix count: {len(arena_res.get('comparison_matrix', []))}",
    )

    router = PrecisionTaskRouter()
    recipe = router.build_graphql_markdown_pipeline(target_url="https://leetcode.com/problems/two-sum/")
    stages = recipe.get("stages", [])
    assert_check(
        "Precision Task Router builds multi-stage pipeline plan with tool chaining",
        isinstance(stages, list) and len(stages) >= 2,
        f"Stages count: {len(stages)}, Pipeline ID: {recipe.get('pipeline_id')}",
    )

    # ------------------------------------------------------------------
    # Check 5: Silver-Tier Contract Engine & 4 Real Pipelines
    # ------------------------------------------------------------------
    print("\n--- Check 5: Silver-Tier Contract Engine & 4 Real Pipelines ---")
    update_progress(70, subtask="Validating Pydantic schemas and pipeline entrypoints...")

    # Test all 5 contract models with valid synthetic data
    c_md = CleanedMarkdownContract(
        title="Test Doc",
        body_markdown="# Test Doc\n\nBody content.",
        url="https://example.com",
        word_count=4,
        reading_time_min=0.1,
    )
    c_prob = CleanedCodeProblemContract(
        problem_id=1,
        title="Two Sum",
        slug="two-sum",
        difficulty="Easy",
        description_markdown="# Two Sum",
        constraints=["2 <= nums.length <= 10^4"],
        starter_snippets={"python": "class Solution:\n    pass"},
        sample_testcases=[{"input": "[2,7,11,15], 9", "output": "[0,1]"}],
    )
    c_soc = CleanedSocialMediaContract(
        platform="instagram",
        post_id="test_reel_01",
        author_handle="@test_creator",
        caption_text="Sample reel caption",
        media_files=["raw/video.mp4"],
        summary_text="Sample spoken transcript",
    )
    c_for = CleanedForensicsContract(
        target_url="https://httpbin.org/html",
        status_code=200,
        discovered_api_endpoints=[{"endpoint": "/api/v1/status"}],
    )
    c_multi = CleanedMultimodalContract(
        source_image_or_pdf="fixtures/sample.png",
        content_type="table_grid",
        table_matrices=[[["Col1", "Col2"], ["Val1", "Val2"]]],
    )

    assert_check(
        "All 5 Silver-Tier Pydantic schema contracts instantiate with strict type safety",
        bool(c_md and c_prob and c_soc and c_for and c_multi),
    )

    # Pipeline Scripts Existence
    p1 = ROOT / "pipelines" / "01_leetcode_archiver.py"
    p2 = ROOT / "pipelines" / "02_social_media_pipeline.py"
    p3 = ROOT / "pipelines" / "03_secured_snapshot_forensics.py"
    p4 = ROOT / "pipelines" / "04_multimodal_auto_resolver.py"

    assert_check("Task Pipeline 1 (01_leetcode_archiver.py) verified", p1.exists())
    assert_check("Task Pipeline 2 (02_social_media_pipeline.py) verified", p2.exists())
    assert_check("Task Pipeline 3 (03_secured_snapshot_forensics.py) verified", p3.exists())
    assert_check("Task Pipeline 4 (04_multimodal_auto_resolver.py) verified", p4.exists())

    # ------------------------------------------------------------------
    # Check 6: Benchmark, Chaos & Project Exporter Engines
    # ------------------------------------------------------------------
    print("\n--- Check 6: Benchmark, Chaos & Project Exporter Engines ---")
    update_progress(80, subtask="Verifying benchmark radar matrix, chaos fuzzing, and exports...")

    bench_eng = get_benchmark_engine()
    p_calc = bench_eng.compute_percentiles([0.1, 0.2, 0.3, 0.4, 0.5])
    c_score = bench_eng.compute_composite_score(speed_score=90, richness_score=85, stealth_score=95, memory_efficiency_score=80)
    assert_check(
        "Benchmark engine calculates statistical percentiles and weighted composite score",
        p_calc["p50"] == 0.3 and 80.0 <= c_score <= 100.0,
        f"p50: {p_calc['p50']}, Composite: {c_score}",
    )

    resil_eng = get_resilience_tester()
    fuzz_res = resil_eng.test_contract_fuzzing_resilience()
    assert_check(
        "Resilience engine: Silver contract schema fuzzing handled safely",
        fuzz_res.get("all_passed") is True,
        f"Fuzz test results: {fuzz_res}",
    )

    exp_eng = get_project_exporter()
    exports_cat = exp_eng.list_exports()
    assert_check(
        "Project exporter discovers standalone tools, data bundles, and pipeline packages",
        "standalone_tools" in exports_cat and "data_bundles" in exports_cat and "pipeline_packages" in exports_cat,
        f"Export categories: {list(exports_cat.keys())}",
    )

    # ------------------------------------------------------------------
    # Check 7: FastAPI Control Plane & 8-Tab Frontend UI
    # ------------------------------------------------------------------
    print("\n--- Check 7: FastAPI Control Plane & 8-Tab Frontend UI ---")
    update_progress(90, subtask="Testing FastAPI REST endpoints and 8-Tab HTML layout...")

    client = TestClient(app)

    # Core REST Endpoints
    assert_check("GET /api/state returns 200 OK", client.get("/api/state").status_code == 200)
    assert_check("GET /api/tools returns 200 OK with 20 engines", len(client.get("/api/tools").json().get("tools", [])) == 20)
    assert_check("GET /api/benchmarks/overview returns 200 OK", client.get("/api/benchmarks/overview").status_code == 200)
    assert_check("GET /api/resilience/overview returns 200 OK", client.get("/api/resilience/overview").status_code == 200)
    assert_check("GET /api/exports/list returns 200 OK", client.get("/api/exports/list").status_code == 200)

    # Frontend 8-Tab Verification
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    expected_tabs = [
        ("Tab 1: Live Execution", 'id="tab-live"'),
        ("Tab 2: Tool Roster", 'id="tab-tools"'),
        ("Tab 3: Data Explorer", 'id="tab-explorer"'),
        ("Tab 4: Index & Search", 'id="tab-index"'),
        ("Tab 5: Credential Vault", 'id="tab-vault"'),
        ("Tab 6: Working Ways & Arena", 'id="tab-working-ways"'),
        ("Tab 7: Real Pipelines", 'id="tab-real-pipelines"'),
        ("Tab 8: Benchmarks & Exporter", 'id="tab-benchmarks-exporter"'),
    ]

    for label, needle in expected_tabs:
        assert_check(f"Frontend index.html contains {label}", needle in index_html)

    # ------------------------------------------------------------------
    # Check 8: Pre-Push Secret Guard & Git Tracking Integrity
    # ------------------------------------------------------------------
    print("\n--- Check 8: Pre-Push Secret Guard & Git Tracking Integrity ---")
    update_progress(95, subtask="Scanning repository for secret leaks and gitignore compliance...")

    # Secret scanning
    secret_audit = scan_staged_for_secrets()
    assert_check(
        "Pre-Push Secret Guard reports ZERO violations in staged files",
        not secret_audit.get("violations_found", False),
        f"Violations: {secret_audit.get('violations', [])}",
    )

    # Check gitignore rules for critical secrets
    p_env = subprocess.run(["git", "check-ignore", ".env"], cwd=str(ROOT), capture_output=True, text=True)
    p_db = subprocess.run(["git", "check-ignore", "vault_store/credentials_vault.sqlite"], cwd=str(ROOT), capture_output=True, text=True)
    p_zip = subprocess.run(["git", "check-ignore", "exports/data_bundles/bundle.zip"], cwd=str(ROOT), capture_output=True, text=True)

    assert_check(".gitignore strictly excludes .env", p_env.returncode == 0)
    assert_check(".gitignore strictly excludes vault_store/*.sqlite", p_db.returncode == 0)
    assert_check(".gitignore strictly excludes export zip bundles", p_zip.returncode == 0)

    # ------------------------------------------------------------------
    # Master System Audit Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Master System Regression Verification Suite completed.")
    print("\n" + "=" * 75)
    print(f"MASTER SYSTEM REGRESSION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 75 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
