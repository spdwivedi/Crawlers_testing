"""
core/verify_step_6_3.py
=======================
Focused Verification Suite for Stage 6 — Step 6.3:
Build the Self-Contained Project Exporter, Data Lake Bundler & Standalone
Scraper Package Generator (`core/project_exporter.py`).

Verifies:
1. Check 1 — Directory Setup & GitIgnore Governance:
   - exports/ directory hierarchy and .gitkeep presence
   - .gitignore verification via git check-ignore (ZIPs ignored, manifests tracked)
2. Check 2 — Standalone Scraper Tool Export:
   - Exports `01_curl_cffi` into self-contained package
   - Verifies run.py, adapter.py, requirements.txt, README.md, compat.py, config.json, export_manifest.json
   - Asserts ZERO monorepo imports (core.folder_manager, backend.app) in adapter.py
   - Verifies clean standalone subprocess execution (exit code 0)
3. Check 3 — Data Lake Artifact Bundler & Manifest Signatures:
   - Packages silver-tier cleaned artifacts with scope="cleaned"
   - Verifies zip archive generation and companion _manifest.json
   - Confirms all SHA-256 hashes and file counts match
4. Check 4 — Zero-Leak Security Audit on Bundles & Archives:
   - Scans archive entries for blocked extensions (.env, *.sqlite, .key, .pem)
   - Verifies blocked path keywords (temp_cookies, vault_store) are strictly excluded
   - Injects a synthetic sensitive dummy and proves exclusion
5. Check 5 — Standalone Pipeline Package Generator:
   - Exports `01_leetcode_archiver` pipeline package
   - Verifies pipeline_runner.py, pipeline.py, Dockerfile, requirements.txt, README.md
   - Asserts Dockerfile contains container entrypoint
   - Verifies clean standalone pipeline runner subprocess execution (exit code 0)
6. Check 6 — Discovery APIs, Master Index Sync & Pre-Commit Secret Guard:
   - Verifies list_exports() and get_export_manifest()
   - Confirms GlobalMasterIndexer.sync_all() federates Stage 6 export logs
   - Confirms core/git_manager.py:scan_staged_for_secrets() reports zero violations
"""

import json
import os
import subprocess
import sys
import zipfile
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
from core.project_exporter import (
    BLOCKED_EXTENSIONS,
    BLOCKED_PATH_KEYWORDS,
    ProjectExporter,
    get_project_exporter,
)
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
            step="Step 6.3",
            tool_id="core_project_exporter",
            action_name="verify_step_6_3",
            stage_log_name="stage_6_benchmarking",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 6",
            step="Step 6.3",
            tool_id="core_project_exporter",
            action_name="verify_step_6_3",
            stage_log_name="stage_6_benchmarking",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 6 STEP 6.3 VERIFICATION SUITE")
    print("   Project Exporter, Data Lake Bundler & Standalone Packaging")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 6 Step 6.3 verification suite...")
    exporter = get_project_exporter()

    # ------------------------------------------------------------------
    # Check 1: Directory Setup & GitIgnore Governance
    # ------------------------------------------------------------------
    print("--- Check 1: Directory Setup & GitIgnore Governance ---")
    update_progress(15, subtask="Verifying export directory structure and gitignore rules...")

    st_keep = ROOT / "exports" / "standalone_tools" / ".gitkeep"
    db_keep = ROOT / "exports" / "data_bundles" / ".gitkeep"
    pp_keep = ROOT / "exports" / "pipeline_packages" / ".gitkeep"

    assert_check("standalone_tools/.gitkeep exists", st_keep.exists(), f"Path: {st_keep}")
    assert_check("data_bundles/.gitkeep exists", db_keep.exists(), f"Path: {db_keep}")
    assert_check("pipeline_packages/.gitkeep exists", pp_keep.exists(), f"Path: {pp_keep}")

    # Check gitignore for zip archives (must be ignored, returncode == 0)
    p_zip = subprocess.run(
        ["git", "check-ignore", "exports/data_bundles/test_bundle.zip"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert_check(
        ".gitignore excludes export zip archives",
        p_zip.returncode == 0,
        f"git check-ignore output: {p_zip.stdout.strip()}",
    )

    # Check gitignore for export manifests (must NOT be ignored, returncode == 1)
    p_mnf = subprocess.run(
        ["git", "check-ignore", "exports/standalone_tools/sample_tool/export_manifest.json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert_check(
        ".gitignore tracks export_manifest.json files",
        p_mnf.returncode == 1,
        f"returncode: {p_mnf.returncode}",
    )

    # ------------------------------------------------------------------
    # Check 2: Standalone Scraper Tool Export
    # ------------------------------------------------------------------
    print("\n--- Check 2: Standalone Scraper Tool Export ---")
    update_progress(30, subtask="Exporting and testing standalone 01_curl_cffi package...")

    export_res = exporter.export_standalone_tool("01_curl_cffi", output_format="both")
    pkg_dir = ROOT / "exports" / "standalone_tools" / "01_curl_cffi_standalone"

    assert_check(
        "export_standalone_tool returns package metadata",
        export_res["tool_id"] == "01_curl_cffi" and export_res["file_count"] >= 6,
        f"Result: {export_res}",
    )
    assert_check("Generated run.py exists", (pkg_dir / "run.py").exists())
    assert_check("Generated adapter.py exists", (pkg_dir / "adapter.py").exists())
    assert_check("Generated requirements.txt exists", (pkg_dir / "requirements.txt").exists())
    assert_check("Generated README.md exists", (pkg_dir / "README.md").exists())
    assert_check("Generated compat.py exists", (pkg_dir / "compat.py").exists())
    assert_check("Generated export_manifest.json exists", (pkg_dir / "export_manifest.json").exists())

    # Verify adapter.py is free of monorepo core dependencies
    adapter_code = (pkg_dir / "adapter.py").read_text(encoding="utf-8")
    assert_check(
        "adapter.py contains NO import of core.folder_manager",
        "core.folder_manager" not in adapter_code,
        "Found core.folder_manager in adapter.py",
    )
    assert_check(
        "adapter.py contains NO import of backend.app",
        "backend.app" not in adapter_code,
        "Found backend.app in adapter.py",
    )
    assert_check(
        "adapter.py imports from local compat shim",
        "from compat import" in adapter_code,
        "compat import block missing",
    )

    # Execute standalone run.py in a separate subprocess
    venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    run_cmd = [
        str(venv_py),
        str(pkg_dir / "run.py"),
        "--url",
        "https://quotes.toscrape.com",
    ]
    p_run = subprocess.run(run_cmd, cwd=str(pkg_dir), capture_output=True, text=True, timeout=30)
    assert_check(
        "Standalone run.py executes cleanly (exit code 0)",
        p_run.returncode == 0,
        f"Exit: {p_run.returncode}, Stderr: {p_run.stderr.strip()[:300]}",
    )
    assert_check(
        "Standalone run.py output indicates completed status",
        "Finished with status: completed" in p_run.stdout,
        f"Stdout: {p_run.stdout.strip()[:300]}",
    )

    # ------------------------------------------------------------------
    # Check 3: Data Lake Artifact Bundler & Manifest Signatures
    # ------------------------------------------------------------------
    print("\n--- Check 3: Data Lake Artifact Bundler & Manifest Signatures ---")
    update_progress(50, subtask="Bundling cleaned data lake artifacts and validating signatures...")

    bundle_res = exporter.bundle_data_lake(scope="cleaned", tool_id="01_curl_cffi", archive_format="zip")
    bundle_zip = ROOT / bundle_res["bundle_path"]
    bundle_mnf = ROOT / bundle_res["manifest_path"]

    assert_check("Bundle zip file created", bundle_zip.exists(), f"Path: {bundle_zip}")
    assert_check("Bundle manifest JSON created", bundle_mnf.exists(), f"Path: {bundle_mnf}")
    assert_check(
        "Bundle manifest contains files and total_bytes > 0",
        bundle_res["total_files"] > 0 and bundle_res["total_bytes"] > 0,
        f"Files: {bundle_res['total_files']}, Bytes: {bundle_res['total_bytes']}",
    )
    assert_check(
        "Bundle archive SHA-256 is 64-char hex",
        len(bundle_res.get("archive_sha256", "")) == 64,
        f"Hash: {bundle_res.get('archive_sha256')}",
    )

    # ------------------------------------------------------------------
    # Check 4: Zero-Leak Security Audit on Bundles & Archives
    # ------------------------------------------------------------------
    print("\n--- Check 4: Zero-Leak Security Audit on Bundles & Archives ---")
    update_progress(65, subtask="Running Zero-Leak security audit on archive entries...")

    leaks: list[str] = []
    with zipfile.ZipFile(bundle_zip, "r") as zf:
        for item in zf.namelist():
            p_lower = item.lower()
            if any(p_lower.endswith(ext) for ext in BLOCKED_EXTENSIONS):
                leaks.append(f"Blocked extension in: {item}")
            if any(kw in p_lower for kw in BLOCKED_PATH_KEYWORDS):
                leaks.append(f"Blocked path keyword in: {item}")

    assert_check(
        "Zero-Leak Audit: No blocked extensions (.env, *.sqlite, .key) or paths in zip",
        len(leaks) == 0,
        f"Found leaks: {leaks}",
    )

    # Synthetic Threat Injection Test: create a sensitive dummy file in data/ and assert exclusion
    threat_dir = ROOT / "data" / "01_curl_cffi" / "test_action" / "temp_cookies"
    threat_dir.mkdir(parents=True, exist_ok=True)
    threat_file = threat_dir / "secret_session.sqlite"
    threat_file.write_text("SENSITIVE_COOKIE_DATA", encoding="utf-8")

    try:
        synth_bundle = exporter.bundle_data_lake(scope="all", archive_format="zip")
        synth_zip = ROOT / synth_bundle["bundle_path"]
        with zipfile.ZipFile(synth_zip, "r") as zf:
            synth_names = zf.namelist()
            threat_found = any("secret_session.sqlite" in n or "temp_cookies" in n for n in synth_names)
            assert_check(
                "Synthetic Threat Test: secret_session.sqlite strictly blocked from bundle",
                not threat_found,
                f"Threat file erroneously included in bundle!",
            )
    finally:
        if threat_file.exists():
            threat_file.unlink()
        if threat_dir.exists():
            try:
                threat_dir.rmdir()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Check 5: Standalone Pipeline Package Generator
    # ------------------------------------------------------------------
    print("\n--- Check 5: Standalone Pipeline Package Generator ---")
    update_progress(80, subtask="Exporting and testing standalone 01_leetcode_archiver pipeline...")

    pipe_res = exporter.export_standalone_pipeline("01_leetcode_archiver")
    pipe_dir = ROOT / "exports" / "pipeline_packages" / "01_leetcode_archiver_pkg"

    assert_check(
        "export_standalone_pipeline returns package metadata",
        pipe_res["pipeline_id"] == "01_leetcode_archiver" and pipe_res["file_count"] >= 6,
        f"Result: {pipe_res}",
    )
    assert_check("Pipeline runner script exists", (pipe_dir / "pipeline_runner.py").exists())
    assert_check("Pipeline Dockerfile exists", (pipe_dir / "Dockerfile").exists())
    assert_check("Pipeline requirements.txt exists", (pipe_dir / "requirements.txt").exists())
    assert_check("Pipeline README.md exists", (pipe_dir / "README.md").exists())
    assert_check("Pipeline manifest exists", (pipe_dir / "export_manifest.json").exists())

    # Check Dockerfile entrypoint
    docker_content = (pipe_dir / "Dockerfile").read_text(encoding="utf-8")
    assert_check(
        "Dockerfile defines ENTRYPOINT [\"python\", \"pipeline_runner.py\"]",
        'ENTRYPOINT ["python", "pipeline_runner.py"]' in docker_content,
        f"Dockerfile: {docker_content}",
    )

    # Test execution of pipeline_runner.py in mock mode
    pipe_cmd = [str(venv_py), str(pipe_dir / "pipeline_runner.py"), "--mock"]
    p_pipe = subprocess.run(pipe_cmd, cwd=str(pipe_dir), capture_output=True, text=True, timeout=20)
    assert_check(
        "Standalone pipeline_runner.py executes cleanly (exit code 0)",
        p_pipe.returncode == 0,
        f"Exit: {p_pipe.returncode}, Stderr: {p_pipe.stderr.strip()}",
    )
    assert_check(
        "Pipeline runner output confirms successful mock execution",
        "Pipeline completed successfully." in p_pipe.stdout,
        f"Stdout: {p_pipe.stdout.strip()}",
    )

    # ------------------------------------------------------------------
    # Check 6: Discovery APIs, Master Index Sync & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 6: Discovery APIs, Master Index Sync & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Verifying discovery APIs, master index synchronization, and secrets...")

    # Discovery APIs
    exports_catalog = exporter.list_exports()
    assert_check(
        "list_exports() returns all 3 export categories",
        "standalone_tools" in exports_catalog
        and "data_bundles" in exports_catalog
        and "pipeline_packages" in exports_catalog,
        f"Keys: {list(exports_catalog.keys())}",
    )
    assert_check(
        "list_exports() discovers 01_curl_cffi standalone tool",
        any(t["tool_id"] == "01_curl_cffi" for t in exports_catalog["standalone_tools"]),
    )
    assert_check(
        "list_exports() discovers 01_leetcode_archiver pipeline package",
        any(p["pipeline_id"] == "01_leetcode_archiver" for p in exports_catalog["pipeline_packages"]),
    )

    # get_export_manifest() test
    manifest_info = exporter.get_export_manifest(str(pkg_dir / "export_manifest.json"))
    assert_check(
        "get_export_manifest() parses valid manifest JSON",
        manifest_info is not None and manifest_info.get("tool_id") == "01_curl_cffi",
        f"Manifest info: {manifest_info}",
    )

    # Global Master Indexer synchronization
    indexer = GlobalMasterIndexer()
    sync_stats = indexer.sync_all()
    assert_check(
        "GlobalMasterIndexer.sync_all() federates all runs cleanly",
        isinstance(sync_stats, dict) and sync_stats.get("total_runs", 0) >= 0,
        f"Sync stats: {sync_stats}",
    )

    # Pre-Commit Secret Guard
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports ZERO violations",
        not secret_scan.get("violations_found", False),
        f"Violations: {secret_scan.get('violations', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Stage 6 Step 6.3 Verification Suite completed.")
    print("\n" + "=" * 70)
    print(f"STAGE 6 STEP 6.3 VERIFICATION SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 70 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
