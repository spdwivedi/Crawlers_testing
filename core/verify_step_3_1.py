"""
core/verify_step_3_1.py
======================
Automated verification suite for Stage 3 - Step 3.1:
Stage 3 Governance, AES-256-GCM Cryptographic Engine, .env Master Key Provisioning,
and Git Pre-Commit Secret Guard.
"""

import base64
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.crypto_engine import (
    CryptoEngine,
    blind_index_hash,
    decrypt_json,
    decrypt_str,
    encrypt_json,
    encrypt_str,
    ensure_master_key,
    get_crypto_engine,
    mask_secret,
)
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 3 STEP 3.1 VERIFICATION SUITE")
    print("=" * 70)

    passed = 0
    total = 0

    def assert_check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [PASS] {name}" + (f" ({detail})" if detail else ""))
        else:
            print(f"  ❌ [FAIL] {name}" + (f" - {detail}" if detail else ""))

    # ------------------------------------------------------------------
    # Check 1: Master Key Provisioning & Git Ignore Hardening
    # ------------------------------------------------------------------
    print("\n--- Check 1: Master Key Provisioning & Git Exclusions ---")
    update_progress(20, "Verifying .env master key and Git ignore rules...")

    env_path = ROOT / ".env"
    assert_check(".env file exists", env_path.exists())

    m_key, kdf_salt = ensure_master_key()
    assert_check("VAULT_MASTER_KEY is provisioned", bool(m_key and len(m_key) >= 32), f"length: {len(m_key)}")
    assert_check("VAULT_KDF_SALT is provisioned", bool(kdf_salt and len(kdf_salt) >= 16), f"length: {len(kdf_salt)}")

    # Test git check-ignore for .env and vault sqlite files
    git_env_check = subprocess.run(
        ["git", "check-ignore", ".env"], cwd=str(ROOT), capture_output=True, text=True
    )
    assert_check("git check-ignore confirms .env is ignored", git_env_check.returncode == 0)

    git_db_check = subprocess.run(
        ["git", "check-ignore", "vault_store/accounts.sqlite"], cwd=str(ROOT), capture_output=True, text=True
    )
    assert_check("git check-ignore confirms vault_store/*.sqlite is ignored", git_db_check.returncode == 0)

    # ------------------------------------------------------------------
    # Check 2: Safe Tracking Exceptions
    # ------------------------------------------------------------------
    print("\n--- Check 2: Safe Tracking Exceptions ---")
    update_progress(35, "Verifying safe tracking exceptions (.env.example, README)...")

    env_example = ROOT / ".env.example"
    assert_check(".env.example template exists", env_example.exists())
    example_text = env_example.read_text(encoding="utf-8") if env_example.exists() else ""
    assert_check(".env.example contains placeholder keys only", "placeholder" in example_text and m_key not in example_text)

    readme_vault = ROOT / "vault_store" / "README_VAULT.md"
    assert_check("vault_store/README_VAULT.md exists", readme_vault.exists())

    gitkeep_vault = ROOT / "vault_store" / ".gitkeep"
    assert_check("vault_store/.gitkeep exists", gitkeep_vault.exists())

    # Ensure exceptions are NOT ignored
    git_check_example = subprocess.run(
        ["git", "check-ignore", ".env.example"], cwd=str(ROOT), capture_output=True, text=True
    )
    assert_check(".env.example is NOT ignored by git", git_check_example.returncode != 0)

    git_check_readme = subprocess.run(
        ["git", "check-ignore", "vault_store/README_VAULT.md"], cwd=str(ROOT), capture_output=True, text=True
    )
    assert_check("vault_store/README_VAULT.md is NOT ignored by git", git_check_readme.returncode != 0)

    # ------------------------------------------------------------------
    # Check 3: Cryptographic Engine Round-Trips
    # ------------------------------------------------------------------
    print("\n--- Check 3: Cryptographic Round-Trips ---")
    update_progress(50, "Testing AES-256-GCM round-trips...")

    engine = get_crypto_engine()
    test_str = "super_secret_password_xyz!@#$"
    token = engine.encrypt_str(test_str)
    assert_check("encrypt_str produces token with v1:aes256gcm: prefix", token.startswith("v1:aes256gcm:"))

    recovered = engine.decrypt_str(token)
    assert_check("decrypt_str recovers exact plaintext", recovered == test_str)

    # Associated data binding test
    ad_context = "tool_01:account_42"
    token_ad = engine.encrypt_str(test_str, associated_data=ad_context)
    recovered_ad = engine.decrypt_str(token_ad, associated_data=ad_context)
    assert_check("decrypt_str with associated data binding recovers plaintext", recovered_ad == test_str)

    # JSON encrypt/decrypt
    test_json = {
        "cookies": [
            {"name": "session_id", "value": "xyz1234567890", "domain": ".example.com"},
            {"name": "csrftoken", "value": "abc987654321", "domain": ".example.com"},
        ],
        "user_id": 9901,
        "is_active": True,
        "metadata": {"tags": ["crawler", "vip"]},
    }
    json_token = engine.encrypt_json(test_json, associated_data="session_state")
    assert_check("encrypt_json returns v1 token", json_token.startswith("v1:aes256gcm:"))
    recovered_json = engine.decrypt_json(json_token, associated_data="session_state")
    assert_check("decrypt_json recovers exact dictionary payload", recovered_json == test_json)

    # ------------------------------------------------------------------
    # Check 4: Tamper Detection & Integrity Verification
    # ------------------------------------------------------------------
    print("\n--- Check 4: Tamper Detection & Integrity Verification ---")
    update_progress(65, "Testing tamper detection and GCM authentication tag validation...")

    # Wrong associated data should fail
    ad_failed = False
    try:
        engine.decrypt_str(token_ad, associated_data="wrong_context")
    except ValueError as e:
        ad_failed = "Vault integrity check failed" in str(e)
    assert_check("Decryption with altered associated data raises ValueError", ad_failed)

    # Tampered ciphertext payload
    tamper_failed = False
    prefix = "v1:aes256gcm:"
    raw_payload = base64.urlsafe_b64decode(token[len(prefix):])
    # Flip one byte in the middle of ciphertext/tag
    tampered_bytes = bytearray(raw_payload)
    tampered_bytes[15] ^= 0xFF
    tampered_token = prefix + base64.urlsafe_b64encode(bytes(tampered_bytes)).decode("ascii")

    try:
        engine.decrypt_str(tampered_token)
    except ValueError as e:
        tamper_failed = "Vault integrity check failed" in str(e)
    assert_check("Tampered ciphertext raises ValueError (GCM tag verification)", tamper_failed)

    # Corrupted / invalid prefix
    invalid_prefix_failed = False
    try:
        engine.decrypt_str("v0:aes128:someinvalidpayload")
    except ValueError:
        invalid_prefix_failed = True
    assert_check("Invalid token prefix raises ValueError", invalid_prefix_failed)

    # ------------------------------------------------------------------
    # Check 5: Secret Masking & Blind Index Hash
    # ------------------------------------------------------------------
    print("\n--- Check 5: Secret Masking & Blind Index Hashing ---")
    update_progress(75, "Testing secret masking and blind indexing...")

    masked = engine.mask_secret("session_token_1234567890", visible_prefix=3, visible_suffix=2)
    assert_check("mask_secret preserves prefix and suffix", masked.startswith("ses") and masked.endswith("90"))
    assert_check("mask_secret masks intermediate characters with *", "*" in masked and "token" not in masked)

    short_masked = engine.mask_secret("abc", visible_prefix=3, visible_suffix=2)
    assert_check("mask_secret handles short strings safely", short_masked == "***" or short_masked == "****")

    blind_h1 = engine.blind_index_hash("user_alpha@crawler.test")
    blind_h2 = engine.blind_index_hash("user_alpha@crawler.test")
    blind_h3 = engine.blind_index_hash("user_beta@crawler.test")
    assert_check("blind_index_hash produces 64-character hex digest", len(blind_h1) == 64)
    assert_check("blind_index_hash is deterministic for identical input", blind_h1 == blind_h2)
    assert_check("blind_index_hash produces distinct digests for different inputs", blind_h1 != blind_h3)

    # ------------------------------------------------------------------
    # Check 6: 1,000-Account Encryption Performance Benchmark
    # ------------------------------------------------------------------
    print("\n--- Check 6: 1,000-Account Encryption Performance Benchmark ---")
    update_progress(85, "Running 1,000-account encryption/decryption speed test...")

    t0 = time.perf_counter()
    for i in range(1000):
        tok = engine.encrypt_str(f"pass_batch_{i:04d}", associated_data=f"user_{i}")
        dec = engine.decrypt_str(tok, associated_data=f"user_{i}")
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000

    benchmark_pass = elapsed_ms < 500.0
    assert_check(
        "1,000-record encrypt/decrypt completes under 500ms",
        benchmark_pass,
        f"completed in {elapsed_ms:.2f}ms"
    )

    # ------------------------------------------------------------------
    # Check 7: Git Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 7: Git Pre-Commit Secret Guard ---")
    update_progress(92, "Testing Git pre-commit secret interception...")

    dummy_db = ROOT / "vault_store" / "test_dummy_db.sqlite"
    dummy_db.write_text("DUMMY_DATABASE_CONTENT", encoding="utf-8")

    try:
        # Force stage the forbidden sqlite file
        subprocess.run(["git", "add", "-f", str(dummy_db)], cwd=str(ROOT), capture_output=True, check=False)

        # Run secret guard scanner
        guard_result = scan_staged_for_secrets(stage="Stage 3", step="Step 3.1")

        assert_check("Secret guard detects staged forbidden file", guard_result["violations_found"])
        assert_check("Offending file is recorded in unstaged_files", any("test_dummy_db.sqlite" in f for f in guard_result["unstaged_files"]))

        # Verify git status confirms the file is no longer staged
        staged_check = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), capture_output=True, text=True
        )
        assert_check("Git staging area was automatically un-staged", "test_dummy_db.sqlite" not in staged_check.stdout)

    finally:
        if dummy_db.exists():
            dummy_db.unlink()

    # ------------------------------------------------------------------
    # Check 8: Stage 3 Logging & Master Index Federation
    # ------------------------------------------------------------------
    print("\n--- Check 8: Stage 3 Logging & Global Master Index Federation ---")
    update_progress(96, "Validating Stage 3 log federation in Global Master Index...")

    stage_3_log = ROOT / "logs" / "stages" / "stage_3_credential_vault.jsonl"
    assert_check("stage_3_credential_vault.jsonl exists", stage_3_log.exists())

    # Log a verification milestone entry
    log_global(
        message="Verification suite completed for Stage 3 Step 3.1",
        level="INFO",
        stage="Stage 3",
        step="Step 3.1",
        tool_id="crypto_engine",
        action_name="verify_step_3_1",
        run_id="",
        progress_pct=98,
        stage_log_name="stage_3_credential_vault",
    )

    # Trigger global index sync
    master_indexer = GlobalMasterIndexer()
    master_indexer.sync_all()

    # Check global index has Stage 3 logs
    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    stage_3_found = False
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3'")
            count = cur.fetchone()[0]
            stage_3_found = count > 0

    assert_check("Global Master Index federates Stage 3 logs", stage_3_found, f"found entries: {count if stage_3_found else 0}")

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.1 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 STEP 3.1 CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
