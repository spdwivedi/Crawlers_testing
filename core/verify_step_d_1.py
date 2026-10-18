"""
Verification Suite for Documentation Milestone — Step D.1:
Master Documentation Spine (docs/01_architecture_and_flows/)

Verifies:
1. Directory Structure: docs/01_..., docs/02_..., docs/03_..., docs/04_...
2. File completeness: All 4 Markdown files exist, >= 4,000 chars each.
3. Visuals & Diagrams: Mermaid.js blocks in each file (flowcharts, stateDiagram-v2, sequenceDiagram).
4. Content Coverage: DFD Levels 0, 1, 2; State machines; Sequence flows.
5. Governance & Secret Guard: Pre-Commit Secret Guard confirms zero staged secrets.
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
from core.state_tracker import update_progress, complete_task
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
            step="Step D.1",
            tool_id="documentation",
            action_name="verify_docs",
            stage_log_name="stage_3_credential_vault",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 3",
            step="Step D.1",
            tool_id="documentation",
            action_name="verify_docs",
            stage_log_name="stage_3_credential_vault",
        )

def main():
    print("=" * 70)
    print("🚀 STARTING DOCUMENTATION MILESTONE VERIFICATION SUITE (STEP D.1)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Check 1: Directory Spine Verification
    # ------------------------------------------------------------------
    print("\n--- Check 1: Documentation Directory Spine ---")
    update_progress(15, "Verifying documentation directory structure...")

    expected_dirs = [
        ROOT / "docs" / "01_architecture_and_flows",
        ROOT / "docs" / "02_database_and_security",
        ROOT / "docs" / "03_folder_and_file_reference",
        ROOT / "docs" / "04_operations_and_guides",
    ]

    for d in expected_dirs:
        assert_check(f"Directory exists: {d.relative_to(ROOT)}", d.is_dir())

    # ------------------------------------------------------------------
    # Check 2: File Presence & Length Verification
    # ------------------------------------------------------------------
    print("\n--- Check 2: Architectural Documents Presence & Completeness ---")
    update_progress(35, "Auditing document presence and length metrics...")

    arch_dir = ROOT / "docs" / "01_architecture_and_flows"
    doc_files = [
        "01_system_architecture_overview.md",
        "02_dfd_level_0_1_2.md",
        "03_state_diagrams.md",
        "04_process_and_sequence_flows.md",
    ]

    file_contents = {}
    for filename in doc_files:
        fpath = arch_dir / filename
        exists = fpath.is_file()
        assert_check(f"Document file exists: {filename}", exists)
        if exists:
            content = fpath.read_text(encoding="utf-8")
            file_contents[filename] = content
            assert_check(
                f"{filename} exceeds 4,000 characters (actual: {len(content)} chars)",
                len(content) >= 4000,
            )
            assert_check(
                f"{filename} contains valid Mermaid diagram block (```mermaid)",
                "```mermaid" in content,
            )

    # ------------------------------------------------------------------
    # Check 3: Detailed Content Audit for 01_system_architecture_overview.md
    # ------------------------------------------------------------------
    print("\n--- Check 3: Content Audit - 01_system_architecture_overview.md ---")
    update_progress(50, "Auditing system architecture overview coverage...")

    doc1 = file_contents.get("01_system_architecture_overview.md", "")
    assert_check("Contains 6-layer architecture description", "LAYER 1:" in doc1 and "LAYER 6:" in doc1)
    assert_check("Contains Mermaid flowchart TB", "flowchart TB" in doc1)
    assert_check("Covers Paradigm 1 (TLS / JA3 / JA4 Impersonation)", "TLS / JA3 / JA4 Fingerprint Impersonation" in doc1)
    assert_check("Covers Paradigm 2 (C-Engine DOM Tree & Boilerplate Slicers)", "C-Engine DOM Tree & Boilerplate Slicers" in doc1)
    assert_check("Covers Paradigm 3 (Standard vs. Binary-Patched Stealth Browsers)", "Standard vs. Binary-Patched Stealth Browsers" in doc1)
    assert_check("Covers Paradigm 4 (Heuristic Self-Healing DOM Relocation)", "Heuristic Self-Healing DOM Relocation" in doc1)
    assert_check("Covers Paradigm 5 (Stream Chunk Demuxing & Social Graph Archivers)", "Stream Chunk Demuxing & Social Graph Archivers" in doc1)
    assert_check("Covers Paradigm 6 (Deep Wire MITM Interception)", "Deep Wire MITM Interception" in doc1)
    assert_check("Covers Paradigm 7 (Multimodal Visual OCR, Table Grid, PDF Layout)", "Multimodal Visual OCR" in doc1)
    assert_check("Explains all 6 Antigravity Governance Rules", all(f"Rule {i}" in doc1 for i in range(1, 7)))

    # ------------------------------------------------------------------
    # Check 4: Detailed Content Audit for 02_dfd_level_0_1_2.md
    # ------------------------------------------------------------------
    print("\n--- Check 4: Content Audit - 02_dfd_level_0_1_2.md ---")
    update_progress(65, "Auditing DFD Level 0, Level 1, and Level 2 specifications...")

    doc2 = file_contents.get("02_dfd_level_0_1_2.md", "")
    assert_check("Contains Master DFD Data Dictionary", "MASTER DFD DATA DICTIONARY" in doc2)
    assert_check("Contains DFD Level 0 (Context Diagram)", "DFD Level 0" in doc2 and "flowchart LR" in doc2)
    assert_check("Contains DFD Level 1 (Major System Subsystems)", "DFD Level 1" in doc2 and "P1: Task & Telemetry Controller" in doc2)
    assert_check("Contains DFD Level 2.1 (Scrape & Folder Creation)", "DFD Level 2.1" in doc2)
    assert_check("Contains DFD Level 2.2 (Auto-Indexing & FTS5 Federation)", "DFD Level 2.2" in doc2)
    assert_check("Contains DFD Level 2.3 (Credential Vault & Ephemeral Shredding)", "DFD Level 2.3" in doc2)
    assert_check("Contains DFD Level 2.4 (4-Tier Logging & Telemetry Streaming)", "DFD Level 2.4" in doc2)

    # ------------------------------------------------------------------
    # Check 5: Detailed Content Audit for 03_state_diagrams.md
    # ------------------------------------------------------------------
    print("\n--- Check 5: Content Audit - 03_state_diagrams.md ---")
    update_progress(80, "Auditing State Machine diagrams and transition tables...")

    doc3 = file_contents.get("03_state_diagrams.md", "")
    assert_check("Contains Global Telemetry State Machine & Table", "Global Telemetry & HUD Task State Machine" in doc3)
    assert_check("Contains Account Lifecycle & Quarantine State Machine & Table", "Credential Vault Account Lifecycle & Quarantine State Machine" in doc3)
    assert_check("Contains Action Run & Data Lifecycle State Machine & Table", "Action Run & Data Lifecycle State Machine" in doc3)
    assert_check("Contains Index Synchronization State Machine", "20-Pipeline Index Synchronization State Machine" in doc3)
    assert_check("Contains at least 4 stateDiagram-v2 blocks", doc3.count("stateDiagram-v2") >= 4)

    # ------------------------------------------------------------------
    # Check 6: Detailed Content Audit for 04_process_and_sequence_flows.md
    # ------------------------------------------------------------------
    print("\n--- Check 6: Content Audit - 04_process_and_sequence_flows.md ---")
    update_progress(90, "Auditing Process & Sequence Flows...")

    doc4 = file_contents.get("04_process_and_sequence_flows.md", "")
    assert_check("Contains Sequence 1 (Full Tool Execution Lifecycle)", "Sequence 1" in doc4 and "POST /api/run-tool/{tool_id}" in doc4)
    assert_check("Contains Sequence 2 (Browser Session Recording)", "Sequence 2" in doc4 and "record-session" in doc4)
    assert_check("Contains Sequence 3 (Private Target & Ephemeral Shredding)", "Sequence 3" in doc4 and "authenticated_session" in doc4)
    assert_check("Contains Sequence 4 (Background Concurrency Architecture)", "Sequence 4" in doc4 and "asyncio.to_thread" in doc4)
    assert_check("Contains at least 4 sequenceDiagram blocks", doc4.count("sequenceDiagram") >= 4)

    # ------------------------------------------------------------------
    # Check 7: Governance & Pre-Commit Secret Guard Scan
    # ------------------------------------------------------------------
    print("\n--- Check 7: Pre-Commit Secret Guard Scan ---")
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
        print("🎉 ALL DOCUMENTATION MILESTONE CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Documentation Milestone Step D.1 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
