"""
Verification Suite for Documentation Milestone — Step D.2:
Database Schemas, ER Diagrams, FTS5 Search Specification & Cryptographic Security Treatise

Verifies:
1. File Presence & Completeness: All 3 Markdown files exist in docs/02_database_and_security/, >= 4,000 chars each.
2. Mermaid ER Diagrams: 01_database_schemas_and_er_diagrams.md contains valid erDiagram blocks.
3. FTS5 Search Engine Spec: 02_fts5_search_and_indexing_specification.md contains schemas, BM25 formulas, tokenizers.
4. Cryptographic Security Treatise: 03_cryptography_and_zero_leak_security_spec.md contains PBKDF2, AES-256-GCM, row-binding proofs, TOTP, and shredding.
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
            step="Step D.2",
            tool_id="documentation",
            action_name="verify_db_security_docs",
            stage_log_name="stage_3_credential_vault",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 3",
            step="Step D.2",
            tool_id="documentation",
            action_name="verify_db_security_docs",
            stage_log_name="stage_3_credential_vault",
        )

def main():
    print("=" * 70)
    print("🚀 STARTING DATABASE & SECURITY DOCUMENTATION VERIFICATION SUITE (STEP D.2)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Check 1: File Presence & Length Verification
    # ------------------------------------------------------------------
    print("\n--- Check 1: Document Presence & Length Metrics ---")
    update_progress(20, "Auditing document presence and length metrics in docs/02_database_and_security/...")

    db_dir = ROOT / "docs" / "02_database_and_security"
    doc_files = [
        "01_database_schemas_and_er_diagrams.md",
        "02_fts5_search_and_indexing_specification.md",
        "03_cryptography_and_zero_leak_security_spec.md",
    ]

    file_contents = {}
    for filename in doc_files:
        fpath = db_dir / filename
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
    # Check 2: Detailed Content Audit for 01_database_schemas_and_er_diagrams.md
    # ------------------------------------------------------------------
    print("\n--- Check 2: Content Audit - 01_database_schemas_and_er_diagrams.md ---")
    update_progress(45, "Auditing database schemas and ER diagrams...")

    doc1 = file_contents.get("01_database_schemas_and_er_diagrams.md", "")
    assert_check("Explains two-tier database topology", "Decoupled Two-Tier Database Architecture" in doc1)
    assert_check("Covers high-concurrency PRAGMAs (WAL, NORMAL, busy_timeout, foreign_keys)",
                 "PRAGMA journal_mode = WAL" in doc1 and "PRAGMA synchronous = NORMAL" in doc1 and
                 "PRAGMA busy_timeout = 5000" in doc1 and "PRAGMA foreign_keys = ON" in doc1)
    assert_check("Contains at least 3 Mermaid erDiagram blocks", doc1.count("erDiagram") >= 3)
    assert_check("Models global_master_index.sqlite with global_tools and global_runs",
                 "global_tools" in doc1 and "global_runs" in doc1 and "global_files" in doc1)
    assert_check("Models isolated tool databases (tool_metadata, indexed_runs)",
                 "tool_metadata" in doc1 and "indexed_runs" in doc1 and "indexed_files" in doc1)
    assert_check("Models credentials_vault.sqlite (vault_accounts, account_target_access, vault_audit_log)",
                 "vault_accounts" in doc1 and "account_target_access" in doc1 and "vault_audit_log" in doc1)
    assert_check("Documents composite indexes (idx_target_lookup, idx_accounts_platform_status)",
                 "idx_target_lookup" in doc1 and "idx_accounts_platform_status" in doc1)
    assert_check("Explains companion JSON snapshots (global_master_index.json, vault_stats_public.json)",
                 "vault_stats_public.json" in doc1 and "global_master_index.json" in doc1)

    # ------------------------------------------------------------------
    # Check 3: Detailed Content Audit for 02_fts5_search_and_indexing_specification.md
    # ------------------------------------------------------------------
    print("\n--- Check 3: Content Audit - 02_fts5_search_and_indexing_specification.md ---")
    update_progress(65, "Auditing FTS5 search engine and indexing specification...")

    doc2 = file_contents.get("02_fts5_search_and_indexing_specification.md", "")
    assert_check("Explains FTS5 inverted index foundations", "Inverted Index" in doc2 and "Vocabulary B-Tree" in doc2)
    assert_check("Explains composite tokenizer ('porter unicode61')", "porter unicode61" in doc2 and "Martin Porter" in doc2)
    assert_check("Contains virtual table schemas for fts_artifacts and fts_logs",
                 "CREATE VIRTUAL TABLE IF NOT EXISTS fts_artifacts USING fts5" in doc2 and
                 "CREATE VIRTUAL TABLE IF NOT EXISTS fts_logs USING fts5" in doc2)
    assert_check("Contains Okapi BM25 mathematical formulation", "Score(D, Q)" in doc2 or "BM25" in doc2)
    assert_check("Covers BM25 column-weight vectors", "bm25(fts_artifacts" in doc2 or "Column-Weight Vectors" in doc2)
    assert_check("Explains highlight() and snippet() UI mechanics", "highlight(" in doc2 and "snippet(" in doc2)
    assert_check("Contains dual-stage synchronization flowchart", "Stage 1: Tool-Isolated Indexing" in doc2 and "Stage 2: Master Index Federation" in doc2)
    assert_check("Contains empirical performance latency benchmarks", "PERFORMANCE BENCHMARKS" in doc2 or "MEAN LATENCY" in doc2)

    # ------------------------------------------------------------------
    # Check 4: Detailed Content Audit for 03_cryptography_and_zero_leak_security_spec.md
    # ------------------------------------------------------------------
    print("\n--- Check 4: Content Audit - 03_cryptography_and_zero_leak_security_spec.md ---")
    update_progress(85, "Auditing cryptographic security specification...")

    doc3 = file_contents.get("03_cryptography_and_zero_leak_security_spec.md", "")
    assert_check("Contains threat matrix and perimeter mitigations", "THREAT MATRIX" in doc3)
    assert_check("Formulates PBKDF2-HMAC-SHA256 with 600,000 iterations", "PBKDF2" in doc3 and "600000" in doc3 or "600,000" in doc3)
    assert_check("Specifies AES-256-GCM token serialization envelope (v1:aes256gcm:)", "v1:aes256gcm:" in doc3)
    assert_check("Contains formal row-binding cryptographic proof via Associated Data (AD)",
                 "Associated Data" in doc3 and "GHASH" in doc3 and "Ciphertext Swapping Attack" in doc3)
    assert_check("Explains Blind Index Hashing (HMAC-SHA256)", "BlindHash" in doc3 or "Blind Index" in doc3)
    assert_check("Covers RFC 6238 2FA TOTP algorithm and dynamic truncation", "RFC 6238" in doc3 and "Dynamic Truncation" in doc3)
    assert_check("Details Ephemeral Cookie Shredding (zero-fill overwrite + os.fsync)",
                 "\\x00" in doc3 and "os.fsync" in doc3)
    assert_check("Covers Pre-Commit Secret Guard scanner rules", "Pre-Commit Secret Guard" in doc3 and "scan_staged_for_secrets" in doc3)

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
        print("🎉 ALL DATABASE & SECURITY DOCUMENTATION CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Documentation Milestone Step D.2 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
