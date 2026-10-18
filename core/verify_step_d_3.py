"""
Verification Suite for Documentation Milestone — Step D.3:
Folder Taxonomy, Core & API File Reference, and 20-Tool Adapter Catalog

Verifies:
1. File Presence & Completeness: All 3 Markdown files exist in docs/03_folder_and_file_reference/.
2. Character Count Thresholds:
   - 01_folder_structure_and_data_taxonomy.md >= 4,000 chars
   - 02_core_and_api_file_reference.md >= 10,000 chars
   - 03_20_tools_adapter_catalog.md >= 15,000 chars
3. Visuals & Diagrams: Valid Mermaid blocks (flowchart, classDiagram) in all files.
4. Content Coverage:
   - Bronze/Silver/Gold medallion architecture, manifest schema, 4-tier log store.
   - Core governance, indexing, crypto vault, and backend API / frontend reference.
   - 20-tool profiles (01_curl_cffi to 20_faster_whisper_scrapegraph).
5. Governance & Secret Guard: Pre-Commit Secret Guard confirms 0 secret violations.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.logger_engine import log_global
from core.state_tracker import update_progress
from core.git_manager import scan_staged_for_secrets

PASSED_COUNT = 0
FAILED_COUNT = 0

def assert_check(name: str, condition: bool, details: str = ""):
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  ✅ [PASS] {name}")
        log_global(
            message=f"CHECK PASSED: {name}",
            level="INFO",
            stage="Stage 3",
            step="Step D.3",
            tool_id="documentation",
            action_name="verify_folder_file_docs",
            stage_log_name="stage_3_credential_vault",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 3",
            step="Step D.3",
            tool_id="documentation",
            action_name="verify_folder_file_docs",
            stage_log_name="stage_3_credential_vault",
        )

def main():
    print("=" * 70)
    print("🚀 STARTING FOLDER & FILE REFERENCE VERIFICATION SUITE (STEP D.3)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Check 1: File Presence & Length Verification
    # ------------------------------------------------------------------
    print("\n--- Check 1: Document Presence & Length Metrics ---")
    update_progress(20, "Auditing document presence and length metrics in docs/03_folder_and_file_reference/...")

    ref_dir = ROOT / "docs" / "03_folder_and_file_reference"
    doc_specs = [
        ("01_folder_structure_and_data_taxonomy.md", 4000),
        ("02_core_and_api_file_reference.md", 10000),
        ("03_20_tools_adapter_catalog.md", 15000),
    ]

    file_contents = {}
    for filename, min_chars in doc_specs:
        fpath = ref_dir / filename
        exists = fpath.is_file()
        assert_check(f"Document file exists: {filename}", exists)
        if exists:
            content = fpath.read_text(encoding="utf-8")
            file_contents[filename] = content
            assert_check(
                f"{filename} exceeds {min_chars:,} characters (actual: {len(content):,} chars)",
                len(content) >= min_chars,
            )
            assert_check(
                f"{filename} contains valid Mermaid diagram block (```mermaid)",
                "```mermaid" in content,
            )

    # ------------------------------------------------------------------
    # Check 2: Content Audit for 01_folder_structure_and_data_taxonomy.md
    # ------------------------------------------------------------------
    print("\n--- Check 2: Content Audit - 01_folder_structure_and_data_taxonomy.md ---")
    update_progress(45, "Auditing folder structure and data taxonomy...")

    doc1 = file_contents.get("01_folder_structure_and_data_taxonomy.md", "")
    assert_check("Contains complete root directory taxonomy", "Root Directory Taxonomy" in doc1 and "vault_store/" in doc1)
    assert_check("Details Bronze Tier (raw/ immutable captures)", "BRONZE TIER" in doc1 and "raw/" in doc1)
    assert_check("Details Silver Tier (cleaned/ normalized outputs)", "SILVER TIER" in doc1 and "cleaned/" in doc1)
    assert_check("Details Gold Tier (index_store/ search aggregates)", "GOLD TIER" in doc1 and "index_store/" in doc1)
    assert_check("Includes run_manifest.json concrete schema specification", "run_manifest.json" in doc1 and "sha256" in doc1)
    assert_check("Explains 4-tier log store taxonomy", "4-Tier Simultaneous Logging Model" in doc1)
    assert_check("Documents vault_store/ and ephemeral cookie shredding", "temp_cookies/" in doc1 and "Zero-Fill" in doc1)

    # ------------------------------------------------------------------
    # Check 3: Content Audit for 02_core_and_api_file_reference.md
    # ------------------------------------------------------------------
    print("\n--- Check 3: Content Audit - 02_core_and_api_file_reference.md ---")
    update_progress(65, "Auditing core and API technical reference manual...")

    doc2 = file_contents.get("02_core_and_api_file_reference.md", "")
    assert_check("Contains Mermaid classDiagram", "classDiagram" in doc2)
    assert_check("Documents core/folder_manager.py (create_action_run, complete_action_run)",
                 "folder_manager.py" in doc2 and "create_action_run" in doc2 and "complete_action_run" in doc2)
    assert_check("Documents core/state_tracker.py & cli_tracker.py",
                 "state_tracker.py" in doc2 and "start_task" in doc2 and "update_progress" in doc2)
    assert_check("Documents core/logger_engine.py (LogEngine, 4-tier logging)",
                 "logger_engine.py" in doc2 and "LogEngine" in doc2)
    assert_check("Documents core/git_manager.py (commit, scan_staged_for_secrets)",
                 "git_manager.py" in doc2 and "scan_staged_for_secrets" in doc2)
    assert_check("Documents core/base_indexer.py and core/global_indexer.py",
                 "base_indexer.py" in doc2 and "global_indexer.py" in doc2 and "BaseToolIndexer" in doc2)
    assert_check("Documents core/crypto_engine.py (AES-256-GCM, PBKDF2)",
                 "crypto_engine.py" in doc2 and "AES-256-GCM" in doc2)
    assert_check("Documents core/credential_vault.py and account_router.py",
                 "credential_vault.py" in doc2 and "account_router.py" in doc2)
    assert_check("Documents core/totp_helper.py and vault_importer.py",
                 "totp_helper.py" in doc2 and "vault_importer.py" in doc2)
    assert_check("Documents core/browser_session_recorder.py and auth_injector.py",
                 "browser_session_recorder.py" in doc2 and "auth_injector.py" in doc2 and "authenticated_session" in doc2)
    assert_check("Documents backend/app.py REST endpoints and WebSockets",
                 "backend/app.py" in doc2 and "/ws/telemetry" in doc2 and "/ws/logs" in doc2)
    assert_check("Documents frontend dashboard (app.js, index.html, styles.css)",
                 "frontend/index.html" in doc2 and "frontend/app.js" in doc2)

    # ------------------------------------------------------------------
    # Check 4: Content Audit for 03_20_tools_adapter_catalog.md
    # ------------------------------------------------------------------
    print("\n--- Check 4: Content Audit - 03_20_tools_adapter_catalog.md ---")
    update_progress(85, "Auditing 20-tool adapter catalog profiles...")

    doc3 = file_contents.get("03_20_tools_adapter_catalog.md", "")
    assert_check("Contains 20-tool master overview matrix", "Master 20-Tool Overview Matrix" in doc3)
    assert_check("Contains Mermaid flowchart TB for tool cohorts", "flowchart TB" in doc3 and "20-Tool Scraping" in doc3)

    # Verify all 20 tools are profiled
    tool_ids = [
        "01_curl_cffi", "02_selectolax_lxml", "03_scrapy", "04_httpx_parsel", "05_trafilatura",
        "06_playwright", "07_patchright", "08_camoufox", "09_nodriver", "10_scrapling",
        "11_yt_dlp_ffmpeg", "12_instaloader", "13_gallery_dl", "14_singlefile_archive", "15_mitmproxy_interceptor",
        "16_crawl4ai", "17_surya_ocr", "18_paddleocr_img2table", "19_docling_pdf", "20_faster_whisper_scrapegraph"
    ]

    for tid in tool_ids:
        assert_check(f"Profiles tool: {tid}", tid in doc3)

    # ------------------------------------------------------------------
    # Check 5: Governance & Pre-Commit Secret Guard Scan
    # ------------------------------------------------------------------
    print("\n--- Check 5: Pre-Commit Secret Guard Scan ---")
    update_progress(95, "Running Pre-Commit Secret Guard scan on staged files...")

    subprocess.run(["git", "add", "-A"], check=True)
    scan_results = scan_staged_for_secrets()
    assert_check(
        "Pre-Commit Secret Guard reports zero blocked secrets",
        scan_results.get("blocked_secrets_count", 0) == 0,
        f"Blocked count: {scan_results.get('blocked_secrets_count')}",
    )
    assert_check(
        "Pre-Commit Secret Guard violations_found is False",
        scan_results.get("violations_found") is False,
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    total_checks = PASSED_COUNT + FAILED_COUNT
    print("\n" + "=" * 70)
    print(f"🏁 MASTER VERIFICATION SUMMARY: {PASSED_COUNT}/{total_checks} CHECKS PASSED")
    print("=" * 70)

    if FAILED_COUNT == 0:
        print("🎉 ALL FOLDER & FILE REFERENCE CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Documentation Milestone Step D.3 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
