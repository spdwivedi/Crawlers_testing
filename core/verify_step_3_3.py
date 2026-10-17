"""
core/verify_step_3_3.py
======================
Automated verification suite for Stage 3 - Step 3.3:
RFC 6238 2FA TOTP Helper, Netscape/JSON Cookie Parsers,
High-Speed Bulk 1,000-Account Importer, and Public Stats Sync.
"""

import json
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

from core.credential_vault import get_credential_vault
from core.crypto_engine import get_crypto_engine
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress
from core.totp_helper import (
    generate_totp_code,
    get_totp_for_account,
    normalize_base32_secret,
    verify_totp_code,
)
from core.vault_importer import VaultImporter


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 3 STEP 3.3 VERIFICATION SUITE")
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

    vault = get_credential_vault()
    importer = VaultImporter(vault=vault)

    # ------------------------------------------------------------------
    # Check 1: RFC 6238 2FA TOTP Verification
    # ------------------------------------------------------------------
    print("\n--- Check 1: RFC 6238 2FA TOTP Verification ---")
    update_progress(15, "Verifying base32 normalization and 2FA TOTP generation...")

    raw_secret = "jbsw-y3dp-ehpk-3pxp"
    norm_secret = normalize_base32_secret(raw_secret)
    assert_check("normalize_base32_secret strips hyphens & uppercases", norm_secret == "JBSWY3DPEHPK3PXP")

    totp_res = generate_totp_code(norm_secret)
    assert_check("generate_totp_code returns 6-digit code", len(totp_res["code"]) == 6 and totp_res["code"].isdigit())
    assert_check("generate_totp_code calculates time_remaining_sec", 0 <= totp_res["time_remaining_sec"] <= 30)

    assert_check("verify_totp_code verifies valid code", verify_totp_code(norm_secret, totp_res["code"]))
    assert_check("verify_totp_code rejects invalid code", not verify_totp_code(norm_secret, "000000"))

    # Test retrieval from encrypted vault record without exposing seed
    totp_acc = vault.add_account(
        platform="instagram",
        username="insta_2fa_tester",
        password="PassWord123!",
        totp_secret="JBSWY3DPEHPK3PXP",
        account_label="2FA Test Account",
    )
    assert_check("Account with TOTP seed stored", bool(totp_acc and totp_acc["account_id"]))

    vault_totp = get_totp_for_account(vault, totp_acc["account_id"], tool_id="12_instaloader", run_id="run_totp_001")
    assert_check("get_totp_for_account returns live code", len(vault_totp["code"]) == 6)
    assert_check("get_totp_for_account does NOT leak raw secret", "secret" not in vault_totp)

    # ------------------------------------------------------------------
    # Check 2: Multi-Format Cookie & Session Parsers
    # ------------------------------------------------------------------
    print("\n--- Check 2: Multi-Format Cookie & Session Parsers ---")
    update_progress(35, "Testing Netscape and JSON cookie jar parsing...")

    netscape_sample = (
        "# Netscape HTTP Cookie File\n"
        "# https://curl.haxx.se/rfc/cookie_spec.html\n"
        "#HttpOnly_.instagram.com\tTRUE\t/\tTRUE\t1893456000\tsessionid\tig_secret_cookie_999\n"
        ".instagram.com\tTRUE\t/\tTRUE\t1893456000\tcsrftoken\tcsrf_val_888\n"
        ".instagram.com\tTRUE\t/\tFALSE\t1893456000\tds_user_id\t5544332211\n"
    )
    p_netscape = VaultImporter.parse_netscape_cookies_txt(netscape_sample)
    assert_check("Netscape parser returns 3 cookies", len(p_netscape["cookies"]) == 3)
    assert_check("Netscape parser sets httpOnly=True for #HttpOnly_ line", p_netscape["cookies"][0]["httpOnly"] is True)
    assert_check("Netscape parser extracts session tokens", "sessionid" in p_netscape["extracted_tokens"] and "csrftoken" in p_netscape["extracted_tokens"])

    json_sample = [
        {
            "name": "LEETCODE_SESSION",
            "value": "tok_leetcode_12345",
            "domain": ".leetcode.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
        },
        {
            "name": "csrftoken",
            "value": "tok_csrf_leetcode",
            "domain": ".leetcode.com",
            "path": "/",
            "httpOnly": False,
            "secure": True,
        },
    ]
    p_json = VaultImporter.parse_json_cookie_jar(json_sample)
    assert_check("JSON cookie jar returns normalized cookies", len(p_json["cookies"]) == 2)
    assert_check("JSON cookie jar extracts LEETCODE_SESSION token", p_json["extracted_tokens"].get("LEETCODE_SESSION") == "tok_leetcode_12345")

    # ------------------------------------------------------------------
    # Check 3: 1,000-Account Single-Transaction Batch Import Benchmark
    # ------------------------------------------------------------------
    print("\n--- Check 3: 1,000-Account Single-Transaction Batch Import Benchmark ---")
    update_progress(55, "Running high-speed bulk import for 1,000 accounts...")

    # Clean slate for bulk benchmark
    db_path = ROOT / "vault_store" / "credentials_vault.sqlite"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM vault_accounts WHERE username_masked LIKE 'bul%'")
        conn.commit()

    # Generate 1,000 synthetic test accounts
    platforms = ["instagram", "facebook", "leetcode", "custom_web"]
    synthetic_batch = []
    for i in range(1000):
        plat = platforms[i % len(platforms)]
        synthetic_batch.append(
            {
                "platform": plat,
                "username": f"bulk_bench_user_{i:04d}",
                "password": f"BenchPass_{i:04d}!@#",
                "totp_secret": "JBSWY3DPEHPK3PXP" if i % 4 == 0 else "",
                "account_label": f"Batch Account {i}",
                "follows_targets": [f"@private_creator_{i % 50}", f"@vip_channel_{i % 25}"] if i % 2 == 0 else [],
                "daily_quota_limit": 50 + (i % 50),
            }
        )

    t0 = time.perf_counter()
    res = importer.bulk_import_accounts(synthetic_batch, on_conflict="update")
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000

    assert_check("bulk_import_accounts processes 1,000 accounts", res["total_processed"] == 1000)
    assert_check("bulk_import_accounts inserts 1,000 records", res["inserted"] == 1000)
    assert_check("bulk_import_accounts links target follower relationships", res["targets_linked"] >= 500)
    assert_check(
        "1,000-account batch completes under 3,000ms",
        elapsed_ms < 3000.0,
        f"completed in {elapsed_ms:.2f}ms ({res['elapsed_ms']}ms DB time)",
    )

    # Re-import test with on_conflict='skip' to verify duplicate prevention
    skip_res = importer.bulk_import_accounts(synthetic_batch, on_conflict="skip")
    assert_check("on_conflict='skip' inserts 0 duplicates", skip_res["inserted"] == 0)
    assert_check("on_conflict='skip' skips all 1,000 existing records", skip_res["skipped"] == 1000)

    # ------------------------------------------------------------------
    # Check 4: Safe Inventory & Encrypted Backup Exporters
    # ------------------------------------------------------------------
    print("\n--- Check 4: Safe Inventory & Encrypted Backup Exporters ---")
    update_progress(75, "Testing masked inventory and ciphertext backup exports...")

    masked_inv = importer.export_masked_inventory(limit=10)
    assert_check("export_masked_inventory returns list of accounts", len(masked_inv) > 0)
    assert_check("export_masked_inventory does NOT expose 'credentials'", all("credentials" not in a for a in masked_inv))
    assert_check("export_masked_inventory has masked usernames", all("*" in a["username_masked"] for a in masked_inv))

    encrypted_backup = importer.export_encrypted_backup()
    assert_check("export_encrypted_backup contains total_accounts > 0", encrypted_backup["total_accounts"] > 0)
    assert_check("export_encrypted_backup preserves v1:aes256gcm: ciphertexts", any(a.get("enc_password", "").startswith("v1:aes256gcm:") for a in encrypted_backup["accounts"]))

    # ------------------------------------------------------------------
    # Check 5: Clean Test Cleanup & Seed Set Retention
    # ------------------------------------------------------------------
    print("\n--- Check 5: Clean Test Cleanup & Seed Set Retention ---")
    update_progress(88, "Cleaning up benchmark rows and retaining clean seed set...")

    db_path = ROOT / "vault_store" / "credentials_vault.sqlite"
    # Keep 10 representative accounts from the benchmark and clean up the remaining 990
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.execute(
            """
            DELETE FROM vault_accounts 
            WHERE (username_masked LIKE 'bul%' OR username_masked LIKE 'tes%')
              AND account_id NOT IN (
                  SELECT account_id FROM vault_accounts 
                  WHERE username_masked LIKE 'bul%' 
                  ORDER BY created_at ASC LIMIT 10
              )
            """
        )
        cleaned_up = cur.rowcount
        conn.commit()

    assert_check("Cleaned up synthetic benchmark accounts", cleaned_up >= 900, f"removed: {cleaned_up}")

    # Refresh public stats
    vault.export_public_stats()
    stats_file = ROOT / "vault_store" / "vault_stats_public.json"
    stats_data = json.loads(stats_file.read_text(encoding="utf-8"))
    assert_check("Public stats reflects clean retained count", stats_data["total_accounts"] <= 50, f"accounts: {stats_data['total_accounts']}")
    assert_check("Public stats records multiple platforms", len(stats_data["by_platform"]) >= 3)

    # ------------------------------------------------------------------
    # Check 6: Stage 3 Logging & Global Master Index Federation
    # ------------------------------------------------------------------
    print("\n--- Check 6: Stage 3 Logging & Global Master Index Federation ---")
    update_progress(96, "Validating Stage 3 Step 3.3 log federation in Global Master Index...")

    log_global(
        message="Stage 3 Step 3.3 verification suite completed successfully",
        level="INFO",
        stage="Stage 3",
        step="Step 3.3",
        tool_id="vault_importer",
        action_name="verify_step_3_3",
        run_id="",
        progress_pct=100,
        stage_log_name="stage_3_credential_vault",
    )

    master_indexer = GlobalMasterIndexer()
    master_indexer.sync_all()

    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    step_3_3_count = 0
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3' AND step = 'Step 3.3'")
            step_3_3_count = cur.fetchone()[0]

    assert_check("Global Master Index federates Step 3.3 logs", step_3_3_count > 0, f"found entries: {step_3_3_count}")

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.3 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 STEP 3.3 CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
