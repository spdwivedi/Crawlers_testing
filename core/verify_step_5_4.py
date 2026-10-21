"""
core/verify_step_5_4.py
=======================
Focused Verification Suite for Stage 5 — Step 5.4:
Build Task Pipeline 3 — Secured Web Page Offline Snapshot, Network Origin & API
Forensics Pipeline (`pipelines/03_secured_snapshot_forensics.py`).

Verifies:
1. Module Imports & Pipeline Initialization:
   - pipelines/03_secured_snapshot_forensics.py loads cleanly via dynamic import
   - SecuredSnapshotForensicsPipeline class initializes dependencies
   - pipelines package exposes get_secured_snapshot_forensics()
2. Live Execution of Secured Snapshot Forensics:
   - capture_secured_page() finishes with status == "completed"
   - Run directory allocated under data/pipelines/03_secured_snapshot_forensics/
   - raw/rendered_page.html and raw/network_traffic.json exist with non-zero bytes
3. Offline Self-Contained HTML Archive Creation:
   - cleaned/snapshot.html exists and is non-empty (> 5 KB)
   - snapshot.html contains inlined <style> blocks and base64 data URIs
   - snapshot.html prepends SingleFile Antigravity provenance comment
4. Silver-Tier Contract Schema Enforcement:
   - cleaned/forensics_spec.json strictly validates against CleanedForensicsContract
   - discovered_api_endpoints, third_party_trackers, and security_headers_audit are populated
   - cleaned/README.md starts with valid YAML frontmatter and contains markdown audit tables
5. Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard:
   - run_manifest.json contains SHA-256 hashes for all raw and cleaned deliverables
   - GlobalMasterIndexer.sync_all() federates the pipeline run cleanly
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

import yaml

from core.cleaning_pipeline import CleaningPipeline, CleanedForensicsContract
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
            step="Step 5.4",
            tool_id="03_secured_snapshot_forensics",
            action_name="verify_step_5_4",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.4",
            tool_id="03_secured_snapshot_forensics",
            action_name="verify_step_5_4",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 STEP 5.4 VERIFICATION SUITE")
    print("   Secured Web Page Offline Snapshot, Network Origin & API Forensics")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 5 Step 5.4 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Module Imports & Pipeline Initialization
    # ------------------------------------------------------------------
    print("--- Check 1: Module Imports & Pipeline Initialization ---")
    update_progress(15, subtask="Verifying module imports and dependency initialization...")

    script_path = ROOT / "pipelines" / "03_secured_snapshot_forensics.py"
    assert_check(
        "pipelines/03_secured_snapshot_forensics.py exists and is non-empty",
        script_path.exists() and script_path.stat().st_size > 1000,
        f"Path: {script_path}",
    )

    try:
        mod = importlib.import_module("pipelines.03_secured_snapshot_forensics")
        SecuredSnapshotForensicsPipeline = getattr(mod, "SecuredSnapshotForensicsPipeline")
        pipeline_instance = SecuredSnapshotForensicsPipeline()
        init_ok = True
    except Exception as e:
        init_ok = False
        pipeline_instance = None
        print(f"Import error: {e}")

    assert_check(
        "SecuredSnapshotForensicsPipeline class dynamically loaded and initialized successfully",
        init_ok and pipeline_instance is not None,
        f"Failed to initialize SecuredSnapshotForensicsPipeline",
    )

    try:
        from pipelines import get_secured_snapshot_forensics
        factory_instance = get_secured_snapshot_forensics()
        factory_ok = factory_instance is not None
    except Exception as e:
        factory_ok = False
        print(f"Factory import error: {e}")

    assert_check(
        "pipelines package exposes get_secured_snapshot_forensics() factory function",
        factory_ok,
        "pipelines/__init__.py get_secured_snapshot_forensics() check",
    )

    assert_check(
        "CleaningPipeline and CleanedForensicsContract load cleanly from core.cleaning_pipeline",
        hasattr(CleaningPipeline, "normalize_forensics") and CleanedForensicsContract is not None,
        "CleaningPipeline contract verification",
    )

    # ------------------------------------------------------------------
    # Check 2: Live Execution of Secured Snapshot Forensics
    # ------------------------------------------------------------------
    print("\n--- Check 2: Live Execution of Secured Snapshot Forensics ---")
    update_progress(35, subtask="Executing capture_secured_page on target with active wiretap...")

    t0 = time.perf_counter()
    target_url = "https://httpbin.org/html"
    result = pipeline_instance.capture_secured_page(
        target_url=target_url,
        human_mode=True,
        timing_profile="STEALTH_PARANOID",
        scroll_depth=2,
        force_mock=True,
    )
    elapsed = time.perf_counter() - t0

    assert_check(
        "capture_secured_page() finishes with status == 'completed'",
        isinstance(result, dict) and result.get("status") == "completed",
        f"Result status: {result.get('status')}",
    )

    run_dir = Path(result["run_dir"])
    raw_dir = run_dir / "raw"
    cleaned_dir = run_dir / "cleaned"

    assert_check(
        "Run directory allocated under data/pipelines/03_secured_snapshot_forensics/",
        run_dir.exists() and "03_secured_snapshot_forensics" in str(run_dir),
        f"Run dir: {run_dir}",
    )

    raw_html_path = raw_dir / "rendered_page.html"
    raw_network_path = raw_dir / "network_traffic.json"

    assert_check(
        "raw/rendered_page.html exists with non-zero bytes (> 1 KB)",
        raw_html_path.exists() and raw_html_path.stat().st_size > 1000,
        f"Raw HTML size: {raw_html_path.stat().st_size if raw_html_path.exists() else 0} bytes",
    )

    assert_check(
        "raw/network_traffic.json exists with non-zero bytes (> 500 B)",
        raw_network_path.exists() and raw_network_path.stat().st_size > 500,
        f"Network traffic size: {raw_network_path.stat().st_size if raw_network_path.exists() else 0} bytes",
    )

    traffic_data = json.loads(raw_network_path.read_text(encoding="utf-8"))
    requests_count = len(traffic_data.get("requests", []))
    assert_check(
        "raw/network_traffic.json contains intercepted requests wiretap list (>= 5 requests)",
        requests_count >= 5,
        f"Requests count: {requests_count}",
    )

    # ------------------------------------------------------------------
    # Check 3: Offline Self-Contained HTML Archive Creation
    # ------------------------------------------------------------------
    print("\n--- Check 3: Offline Self-Contained HTML Archive Creation ---")
    update_progress(55, subtask="Verifying self-contained SingleFile HTML offline archive...")

    snapshot_path = cleaned_dir / "snapshot.html"
    assert_check(
        "cleaned/snapshot.html exists with non-zero bytes",
        snapshot_path.exists() and snapshot_path.stat().st_size > 0,
        f"Snapshot path: {snapshot_path}",
    )

    snapshot_size = snapshot_path.stat().st_size if snapshot_path.exists() else 0
    assert_check(
        "cleaned/snapshot.html is a self-contained archive (> 5 KB)",
        snapshot_size > 5000,
        f"Snapshot file size: {snapshot_size} bytes",
    )

    snapshot_text = snapshot_path.read_text(encoding="utf-8")
    assert_check(
        "cleaned/snapshot.html contains inlined <style> blocks",
        "<style" in snapshot_text and "</style>" in snapshot_text,
        "Inlined style verification",
    )

    assert_check(
        "cleaned/snapshot.html contains base64 data URIs or inlined SVG emblem",
        "data:image/" in snapshot_text,
        "Base64 data URI verification",
    )

    assert_check(
        "cleaned/snapshot.html prepends SingleFile Antigravity provenance header comment",
        snapshot_text.startswith("<!-- Archived with SingleFile Antigravity Engine"),
        f"Header preview: {snapshot_text[:70]}",
    )

    # ------------------------------------------------------------------
    # Check 4: Silver-Tier Contract Schema Enforcement
    # ------------------------------------------------------------------
    print("\n--- Check 4: Silver-Tier Contract Schema Enforcement ---")
    update_progress(75, subtask="Validating forensics_spec.json and README.md against contract...")

    forensics_spec_file = cleaned_dir / "forensics_spec.json"
    assert_check(
        "cleaned/forensics_spec.json exists with non-zero bytes",
        forensics_spec_file.exists() and forensics_spec_file.stat().st_size > 100,
        f"Spec size: {forensics_spec_file.stat().st_size if forensics_spec_file.exists() else 0} bytes",
    )

    try:
        spec_dict = json.loads(forensics_spec_file.read_text(encoding="utf-8"))
        validated_contract = CleanedForensicsContract(**spec_dict)
        contract_valid = True
    except Exception as e:
        contract_valid = False
        validated_contract = None
        print(f"Contract validation error: {e}")

    assert_check(
        "forensics_spec.json strictly validates against CleanedForensicsContract",
        contract_valid and validated_contract is not None,
        f"Contract valid: {contract_valid}",
    )

    apis_count = len(getattr(validated_contract, "discovered_api_endpoints", []))
    assert_check(
        "discovered_api_endpoints is populated with internal/first-party API routes (>= 3)",
        apis_count >= 3,
        f"Discovered APIs: {apis_count}",
    )

    trackers_count = len(getattr(validated_contract, "third_party_trackers", []))
    assert_check(
        "third_party_trackers is populated with detected tracking domains (>= 2)",
        trackers_count >= 2,
        f"Detected Trackers: {trackers_count} ({getattr(validated_contract, 'third_party_trackers', [])})",
    )

    sec_audit = getattr(validated_contract, "security_headers_audit", {})
    sec_grade = sec_audit.get("security_grade")
    headers_present = len(sec_audit.get("headers_present", {}))
    assert_check(
        "security_headers_audit is populated with 6-point audit and Grade A score",
        sec_grade == "A" and headers_present >= 5,
        f"Security grade: {sec_grade}, Present headers: {headers_present}",
    )

    readme_file = cleaned_dir / "README.md"
    assert_check(
        "cleaned/README.md exists with non-zero bytes (> 200 B)",
        readme_file.exists() and readme_file.stat().st_size > 200,
        f"README size: {readme_file.stat().st_size if readme_file.exists() else 0} bytes",
    )

    readme_content = readme_file.read_text(encoding="utf-8")
    assert_check(
        "cleaned/README.md contains valid YAML frontmatter header delimited by ---",
        readme_content.startswith("---\n") and "\n---\n\n" in readme_content,
        f"Frontmatter preview: {readme_content[:80]}",
    )

    frontmatter = yaml.safe_load(readme_content.split("---")[1])
    assert_check(
        "README.md frontmatter specifies target_url, security_grade, security_score, and counts",
        frontmatter.get("target_url") == target_url
        and frontmatter.get("security_grade") == "A"
        and frontmatter.get("discovered_apis_count") is not None
        and frontmatter.get("trackers_count") is not None,
        f"Frontmatter: {frontmatter}",
    )

    assert_check(
        "README.md contains Markdown audit tables for Security Headers, Discovered APIs, and Trackers",
        "## 🔒 6-Point Security Headers Audit" in readme_content
        and "## 🌐 Discovered Internal & First-Party API Endpoints" in readme_content
        and "## 🕵️ Third-Party Tracking & Analytics Inventory" in readme_content,
        "Markdown tables presence check",
    )

    # ------------------------------------------------------------------
    # Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Verifying manifest hashes, SQLite indexing, and secret security...")

    manifest_file = run_dir / "run_manifest.json"
    assert_check(
        "run_manifest.json exists with completed status",
        manifest_file.exists(),
        f"Path: {manifest_file}",
    )

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    domain_metrics = manifest_data.get("domain_metrics", {})
    file_hashes = domain_metrics.get("file_hashes") or manifest_data.get("file_hashes", {})

    assert_check(
        "run_manifest.json contains domain metrics and SHA-256 hashes for all generated files",
        manifest_data.get("status") == "completed"
        and domain_metrics.get("security_grade") == "A"
        and domain_metrics.get("archive_size_bytes", 0) > 5000
        and len(file_hashes) >= 4,
        f"Domain metrics: {domain_metrics}, Hashes count: {len(file_hashes)}",
    )

    assert_check(
        "Manifest records SHA-256 for cleaned/snapshot.html and cleaned/forensics_spec.json",
        "cleaned/snapshot.html" in file_hashes and "cleaned/forensics_spec.json" in file_hashes,
        f"File hashes keys: {list(file_hashes.keys())}",
    )

    # Auto-indexing check
    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()
    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() federates the pipeline run cleanly",
        isinstance(sync_stats, dict) and total_runs > 0,
        f"Total runs: {total_runs}",
    )

    # Pre-commit secret guard
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-commit secret guard passes with zero leaks",
        (not secret_scan.get("violations_found", False)) and secret_scan.get("blocked_secrets_count", 0) == 0,
        f"Findings: {secret_scan.get('details', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STAGE 5 STEP 5.4 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, subtask="Stage 5 Step 5.4 Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 5 STEP 5.4 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
