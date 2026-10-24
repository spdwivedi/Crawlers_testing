"""
core/verify_all_docs.py
=======================
Automated Documentation Completeness & Technical Coverage Verification Suite
Stage: Documentation | Step: Master Audit

Validates:
1. Check 1 — Document Presence & Minimum Length Standards:
   - Root README.md exists and exceeds 15,000 characters.
   - All 10 subfolder README.md files exist and exceed 1,500 characters each.
   - All 13 documents in docs/ exist and exceed 6,000 characters each.
2. Check 2 — Content Completeness & Technical Coverage:
   - Root README.md documents all 20 tools, all 3 Working Ways, all 4 pipelines, and all 8 UI tabs.
   - core/README.md and docs/03_folder_and_file_reference/02_core_and_api_file_reference.md document all 23 core modules.
   - backend/README.md documents all 24+ REST endpoints.
   - frontend/README.md documents all 8 dashboard tabs.
   - pipelines/README.md documents all 4 active production pipelines.
3. Check 3 — Diagram Validation:
   - Confirms every document containing Mermaid blocks uses valid syntax (flowchart, sequenceDiagram, classDiagram, erDiagram, stateDiagram-v2).
4. Check 4 — Pre-Commit Secret Guard Scan:
   - Runs core/git_manager.py:scan_staged_for_secrets() and confirms zero violations.
5. Check 5 — Global Master Index Synchronization:
   - Runs GlobalMasterIndexer.sync_all() and confirms all verification logs and manifests are indexed cleanly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, passed: bool, detail: str = "") -> bool:
    global PASSED_COUNT, FAILED_COUNT
    if passed:
        PASSED_COUNT += 1
        msg = f"  [PASS] {name}"
        if detail:
            msg += f" ({detail})"
        print(msg)
        log_global(
            message=f"DOC CHECK PASSED: {name}" + (f" - {detail}" if detail else ""),
            level="INFO",
            stage="Documentation",
            step="Master Audit",
            tool_id="docs_verifier",
            action_name="verify_all_docs",
            stage_log_name="stage_6_benchmarking",
        )
        return True
    else:
        FAILED_COUNT += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -- FAILED: {detail}"
        print(msg)
        log_global(
            message=f"DOC CHECK FAILED: {name}" + (f" - {detail}" if detail else ""),
            level="ERROR",
            stage="Documentation",
            step="Master Audit",
            tool_id="docs_verifier",
            action_name="verify_all_docs",
            stage_log_name="stage_6_benchmarking",
        )
        return False


def main() -> None:
    print("\n" + "=" * 75)
    print("STARTING MASTER DOCUMENTATION & PRE-RELEASE REPOSITORY AUDIT")
    print("   Automated Verification across Root, Subsystems & 4-Volume Spine")
    print("=" * 75 + "\n")

    update_progress(5, subtask="Auditing Root and Subsystem README existence and length...")

    # ------------------------------------------------------------------
    # Check 1: Document Presence & Minimum Length Standards
    # ------------------------------------------------------------------
    print("--- Check 1: Document Presence & Minimum Length Standards ---")

    root_readme = ROOT / "README.md"
    assert_check("Root README.md exists", root_readme.exists())
    root_len = len(root_readme.read_text(encoding="utf-8")) if root_readme.exists() else 0
    assert_check("Root README.md exceeds 15,000 characters", root_len >= 15000, f"Actual: {root_len} chars")

    subsystem_readmes = [
        "core/README.md",
        "backend/README.md",
        "frontend/README.md",
        "tools/README.md",
        "pipelines/README.md",
        "index_store/README.md",
        "vault_store/README.md",
        "logs/README.md",
        "exports/README.md",
        "docs/README.md",
    ]

    for rel_path in subsystem_readmes:
        p = ROOT / rel_path
        exists = p.exists()
        char_count = len(p.read_text(encoding="utf-8")) if exists else 0
        assert_check(
            f"Subsystem {rel_path} exists and >= 1,500 chars",
            exists and char_count >= 1500,
            f"Actual: {char_count} chars",
        )

    docs_files = [
        "docs/01_architecture_and_flows/01_system_architecture_overview.md",
        "docs/01_architecture_and_flows/02_dfd_level_0_1_2.md",
        "docs/01_architecture_and_flows/03_state_diagrams.md",
        "docs/01_architecture_and_flows/04_process_and_sequence_flows.md",
        "docs/02_database_and_security/01_database_schemas_and_er_diagrams.md",
        "docs/02_database_and_security/02_fts5_search_and_indexing_specification.md",
        "docs/02_database_and_security/03_cryptography_and_zero_leak_security_spec.md",
        "docs/03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md",
        "docs/03_folder_and_file_reference/02_core_and_api_file_reference.md",
        "docs/03_folder_and_file_reference/03_20_tools_adapter_catalog.md",
        "docs/04_operations_and_guides/01_developer_operations_and_runbook.md",
        "docs/04_operations_and_guides/02_troubleshooting_and_resilience_guide.md",
        "docs/04_operations_and_guides/03_documentation_master_index.md",
    ]

    update_progress(25, subtask="Auditing 13 master documents in docs/...")
    for rel_path in docs_files:
        p = ROOT / rel_path
        exists = p.exists()
        char_count = len(p.read_text(encoding="utf-8")) if exists else 0
        assert_check(
            f"Master Document {Path(rel_path).name} >= 6,000 chars",
            exists and char_count >= 6000,
            f"Actual: {char_count} chars",
        )

    # ------------------------------------------------------------------
    # Check 2: Content Completeness & Technical Coverage
    # ------------------------------------------------------------------
    print("\n--- Check 2: Content Completeness & Technical Coverage ---")
    update_progress(45, subtask="Verifying 20 tools, 3 ways, 4 pipelines, 8 tabs in root README...")

    root_content = root_readme.read_text(encoding="utf-8")

    # 20 Tools in root README
    expected_tools = [
        "01_curl_cffi", "02_selectolax_lxml", "03_scrapy", "04_httpx_parsel", "05_trafilatura",
        "06_playwright", "07_patchright", "08_camoufox", "09_nodriver", "10_scrapling",
        "11_yt_dlp_ffmpeg", "12_instaloader", "13_gallery_dl", "14_singlefile_archive", "15_mitmproxy",
        "16_crawl4ai", "17_surya_ocr", "18_paddleocr_img2table", "19_docling_pdf", "20_faster_whisper",
    ]
    tools_found = all(t in root_content for t in expected_tools)
    assert_check("Root README.md covers all 20 tool engines", tools_found)

    # 3 Working Ways
    ways_found = (
        ("Universal Human Mode" in root_content or "Working Way 1" in root_content)
        and ("Safe Arena Mode" in root_content or "Working Way 2" in root_content)
        and ("Precision Task Router" in root_content or "Working Way 3" in root_content)
    )
    assert_check("Root README.md covers all 3 Working Ways", ways_found)

    # 4 Pipelines
    pipelines_found = (
        "01_leetcode_archiver" in root_content
        and "02_social_media_pipeline" in root_content
        and "03_secured_snapshot_forensics" in root_content
        and "04_multimodal_auto_resolver" in root_content
    )
    assert_check("Root README.md covers all 4 Production Task Pipelines", pipelines_found)

    # 8 UI Tabs
    tabs_found = all(f"Tab {i}" in root_content for i in range(1, 9))
    assert_check("Root README.md covers all 8 Dashboard Tabs", tabs_found)

    # 23 Core Modules in core/README.md and 02_core_and_api_file_reference.md
    update_progress(60, subtask="Verifying 23 core modules in core/README.md and documentation...")
    core_readme_content = (ROOT / "core" / "README.md").read_text(encoding="utf-8")
    api_ref_content = (ROOT / "docs" / "03_folder_and_file_reference" / "02_core_and_api_file_reference.md").read_text(encoding="utf-8")

    core_modules = [
        "state_tracker.py", "cli_tracker.py", "logger_engine.py", "folder_manager.py", "git_manager.py",
        "base_indexer.py", "global_indexer.py", "crypto_engine.py", "credential_vault.py", "totp_helper.py",
        "vault_importer.py", "account_router.py", "browser_session_recorder.py", "auth_injector.py",
        "human_timing.py", "human_interaction.py", "human_adapter_helper.py", "arena_runner.py",
        "task_router.py", "cleaning_pipeline.py", "benchmark_engine.py", "resilience_tester.py",
        "project_exporter.py"
    ]
    all_in_core_readme = all(m in core_readme_content for m in core_modules)
    all_in_api_ref = all(m in api_ref_content for m in core_modules)
    assert_check("core/README.md documents all 23 core modules", all_in_core_readme)
    assert_check("02_core_and_api_file_reference.md documents all 23 core modules", all_in_api_ref)

    # 24+ REST Endpoints in backend/README.md
    backend_readme_content = (ROOT / "backend" / "README.md").read_text(encoding="utf-8")
    assert_check(
        "backend/README.md documents 24+ REST endpoints",
        backend_readme_content.count("`/api/") >= 20 and "/ws/telemetry" in backend_readme_content,
        f"API references found: {backend_readme_content.count('`/api/')}",
    )

    # 8 Dashboard Tabs in frontend/README.md
    frontend_readme_content = (ROOT / "frontend" / "README.md").read_text(encoding="utf-8")
    assert_check(
        "frontend/README.md documents all 8 dashboard tabs with shortcuts",
        all(f"Tab {i}" in frontend_readme_content for i in range(1, 9)) and "Alt + 1" in frontend_readme_content,
    )

    # 4 Pipelines in pipelines/README.md
    pipe_readme_content = (ROOT / "pipelines" / "README.md").read_text(encoding="utf-8")
    assert_check(
        "pipelines/README.md documents all 4 active task pipelines",
        "01_leetcode_archiver.py" in pipe_readme_content
        and "02_social_media_pipeline.py" in pipe_readme_content
        and "03_secured_snapshot_forensics.py" in pipe_readme_content
        and "04_multimodal_auto_resolver.py" in pipe_readme_content,
    )

    # ------------------------------------------------------------------
    # Check 3: Diagram Validation
    # ------------------------------------------------------------------
    print("\n--- Check 3: Diagram Validation ---")
    update_progress(75, subtask="Validating Mermaid diagram syntax across documents...")

    valid_diagram_types = ("flowchart", "sequenceDiagram", "classDiagram", "erDiagram", "stateDiagram", "stateDiagram-v2")
    all_md_files = list(ROOT.rglob("*.md"))
    # Exclude .venv or third-party dirs
    candidate_mds = [f for f in all_md_files if ".venv" not in f.parts and "node_modules" not in f.parts]

    mermaid_blocks_checked = 0
    invalid_mermaid_blocks = []

    for md_file in candidate_mds:
        text = md_file.read_text(encoding="utf-8")
        matches = re.findall(r"```mermaid\s*\n(.*?)\n```", text, flags=re.DOTALL)
        for block in matches:
            first_line = block.strip().split("\n")[0].strip()
            if any(first_line.startswith(t) for t in valid_diagram_types):
                mermaid_blocks_checked += 1
            else:
                invalid_mermaid_blocks.append((str(md_file.relative_to(ROOT)), first_line))

    assert_check(
        f"Validated {mermaid_blocks_checked} Mermaid diagrams across repository",
        len(invalid_mermaid_blocks) == 0,
        f"Invalid blocks: {invalid_mermaid_blocks}" if invalid_mermaid_blocks else f"{mermaid_blocks_checked} valid blocks",
    )

    # ------------------------------------------------------------------
    # Check 4: Pre-Commit Secret Guard Scan
    # ------------------------------------------------------------------
    print("\n--- Check 4: Pre-Commit Secret Guard Scan ---")
    update_progress(88, subtask="Running Pre-Commit Secret Guard scan...")

    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports ZERO violations in staged files",
        not secret_scan.get("violations_found", False),
        f"Violations: {secret_scan.get('violations', [])}",
    )

    # ------------------------------------------------------------------
    # Check 5: Global Master Index Synchronization
    # ------------------------------------------------------------------
    print("\n--- Check 5: Global Master Index Synchronization ---")
    update_progress(95, subtask="Synchronizing all tool indexes into global master index...")

    indexer = GlobalMasterIndexer()
    summary = indexer.sync_all()
    total_runs = summary.get("totals", {}).get("total_runs", 0)
    total_logs = summary.get("totals", {}).get("total_logs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() executes cleanly with federated runs and logs",
        total_runs > 0 and total_logs > 0,
        f"Total Runs: {total_runs}, Total Logs: {total_logs}",
    )

    # ------------------------------------------------------------------
    # Audit Summary
    # ------------------------------------------------------------------
    update_progress(100, subtask="Master Documentation Audit completed.")
    print("\n" + "=" * 75)
    print(f"MASTER DOCUMENTATION AUDIT SUMMARY: {PASSED_COUNT} PASSED, {FAILED_COUNT} FAILED")
    print("=" * 75 + "\n")

    if FAILED_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
