"""
Verification Suite for Documentation Milestone — Step D.4 (Final Milestone):
Operations Guides, Master Index, Flagship Root README, Subfolder READMEs & Full Git Security Audit

Verifies:
1. Documentation Presence & Length Metrics:
   - 3 files in docs/04_operations_and_guides/ >= 4,000 chars each.
   - Root README.md >= 8,000 chars.
   - 8 subfolder README.md files exist (core, backend, frontend, tools, index_store, vault_store, logs, docs).
2. Git Tracking & Secret Exclusion Audit:
   - git ls-files contains 0 forbidden files (.env, *.sqlite, *.db, *.pem, *.key, temp_cookies).
   - git check-ignore correctly ignores .env, credentials_vault.sqlite, and temp_cookies.
3. Git Commit History Leak Scan:
   - Historical commit tree contains 0 occurrences of .env or credentials_vault.sqlite.
4. Pre-Commit Secret Guard Scan:
   - scan_staged_for_secrets() confirms 0 violations.
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
            step="Step D.4",
            tool_id="documentation",
            action_name="verify_final_docs_security",
            stage_log_name="stage_3_credential_vault",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 3",
            step="Step D.4",
            tool_id="documentation",
            action_name="verify_final_docs_security",
            stage_log_name="stage_3_credential_vault",
        )

def main():
    print("=" * 70)
    print("🚀 STARTING FINAL DOCUMENTATION & SECURITY AUDIT SUITE (STEP D.4)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Check 1: Documentation Presence & Length Verification
    # ------------------------------------------------------------------
    print("\n--- Check 1: Operations Guides & Root README Metrics ---")
    update_progress(15, "Auditing operations guides and root README length metrics...")

    ops_dir = ROOT / "docs" / "04_operations_and_guides"
    ops_files = [
        ("01_developer_operations_and_runbook.md", 4000),
        ("02_troubleshooting_and_resilience_guide.md", 4000),
        ("03_documentation_master_index.md", 4000),
    ]

    for filename, min_chars in ops_files:
        fpath = ops_dir / filename
        exists = fpath.is_file()
        assert_check(f"Operations doc exists: {filename}", exists)
        if exists:
            content = fpath.read_text(encoding="utf-8")
            assert_check(
                f"{filename} exceeds {min_chars:,} characters (actual: {len(content):,} chars)",
                len(content) >= min_chars,
            )

    # Root README.md
    root_readme = ROOT / "README.md"
    assert_check("Root README.md exists", root_readme.is_file())
    if root_readme.is_file():
        readme_content = root_readme.read_text(encoding="utf-8")
        assert_check(
            f"Root README.md exceeds 8,000 characters (actual: {len(readme_content):,} chars)",
            len(readme_content) >= 8000,
        )
        assert_check("Root README.md contains Mermaid architecture diagram", "```mermaid" in readme_content)
        assert_check("Root README.md contains 20-tool matrix", "Master 20-Tool Capabilities Matrix" in readme_content)
        assert_check("Root README.md details Control Center (5 tabs)", "Antigravity Control Center Dashboard" in readme_content)
        assert_check("Root README.md details Zero-Plaintext Security", "Zero-Plaintext Security" in readme_content)

    # ------------------------------------------------------------------
    # Check 2: Subfolder README Files Verification
    # ------------------------------------------------------------------
    print("\n--- Check 2: Subfolder README Files Presence ---")
    update_progress(35, "Auditing subfolder README files across all 8 subsystems...")

    subfolders = ["core", "backend", "frontend", "tools", "index_store", "vault_store", "logs", "docs"]
    for s in subfolders:
        sub_readme = ROOT / s / "README.md"
        assert_check(f"Subfolder README exists: {s}/README.md", sub_readme.is_file())
        if sub_readme.is_file():
            content = sub_readme.read_text(encoding="utf-8")
            assert_check(f"{s}/README.md is substantive (> 1,000 chars, actual: {len(content):,})", len(content) >= 1000)

    # ------------------------------------------------------------------
    # Check 3: Git Tracking & Secret Exclusion Audit
    # ------------------------------------------------------------------
    print("\n--- Check 3: Git Tracking & Secret Exclusion Audit ---")
    update_progress(55, "Scanning Git index for accidentally tracked secrets or databases...")

    tracked_files = subprocess.check_output(["git", "ls-files"], cwd=str(ROOT), text=True).splitlines()
    
    forbidden_extensions = [".sqlite", ".db", ".pem", ".key"]
    forbidden_exact_files = [".env"]

    tracked_leaks = [
        f for f in tracked_files
        if any(f.endswith(ext) for ext in forbidden_extensions)
        or any(f == fb or f.endswith("/" + fb) for fb in forbidden_exact_files)
        or "temp_cookies" in f
    ]

    assert_check(
        "Zero forbidden secrets or databases tracked in Git index",
        len(tracked_leaks) == 0,
        f"Found tracked leaks: {tracked_leaks}",
    )

    # Check git check-ignore enforcement
    test_ignores = [
        ".env",
        "vault_store/credentials_vault.sqlite",
        "vault_store/temp_cookies/test.cookies.txt",
    ]

    for p in test_ignores:
        res = subprocess.run(["git", "check-ignore", "-q", p], cwd=str(ROOT))
        assert_check(f"Git correctly ignores {p}", res.returncode == 0)

    # ------------------------------------------------------------------
    # Check 4: Git Commit History Leak Scan
    # ------------------------------------------------------------------
    print("\n--- Check 4: Git Commit History Leak Scan ---")
    update_progress(75, "Scanning complete Git commit history for historical secret leaks...")

    history_log = subprocess.check_output(
        ["git", "log", "--name-only", "--all", "--oneline"],
        cwd=str(ROOT),
        text=True,
    )

    history_leaks = [
        line.strip()
        for line in history_log.splitlines()
        if line.strip() in [".env", "credentials_vault.sqlite", "vault_store/credentials_vault.sqlite"]
    ]

    assert_check(
        "Zero historical secret leaks in Git commit history",
        len(history_leaks) == 0,
        f"Found historical leaks: {history_leaks}",
    )

    # ------------------------------------------------------------------
    # Check 5: Pre-Commit Secret Guard Scan
    # ------------------------------------------------------------------
    print("\n--- Check 5: Pre-Commit Secret Guard Scan ---")
    update_progress(90, "Running Pre-Commit Secret Guard on all staged files...")

    subprocess.run(["git", "add", "-A"], cwd=str(ROOT), check=True)
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
        print("🎉 ALL FINAL DOCUMENTATION & SECURITY CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Documentation Milestone Step D.4 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
