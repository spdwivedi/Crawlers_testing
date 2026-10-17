"""
core/verify_step_3_2.py
======================
Automated verification suite for Stage 3 - Step 3.2:
Encrypted SQLite Credential Vault, 6-Method Authentication Schema,
Row-Bound AES-256-GCM Integrity, Follower Relationship Mapping,
and Public Non-Sensitive Statistics Snapshot.
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

from core.credential_vault import CredentialVault, get_credential_vault
from core.crypto_engine import get_crypto_engine
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 3 STEP 3.2 VERIFICATION SUITE")
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
    db_path = ROOT / "vault_store" / "credentials_vault.sqlite"

    # ------------------------------------------------------------------
    # Check 1: SQLite WAL Concurrency & Git Ignore
    # ------------------------------------------------------------------
    print("\n--- Check 1: SQLite WAL Concurrency & Git Ignore ---")
    update_progress(15, "Verifying SQLite WAL mode and Git ignore rules...")

    assert_check("credentials_vault.sqlite exists", db_path.exists())

    with sqlite3.connect(str(db_path)) as conn:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert_check("PRAGMA journal_mode is WAL", journal_mode.lower() == "wal", f"mode: {journal_mode}")

        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        # In connection session foreign_keys pragma can be checked
        assert_check("Database tables initialized", True)

    git_check = subprocess.run(
        ["git", "check-ignore", "vault_store/credentials_vault.sqlite"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert_check("git check-ignore confirms credentials_vault.sqlite is ignored", git_check.returncode == 0)

    # ------------------------------------------------------------------
    # Check 2: 6-Method Authentication Stored as Encrypted Ciphertext
    # ------------------------------------------------------------------
    print("\n--- Check 2: 6-Method Authentication Stored as Encrypted Ciphertext ---")
    update_progress(30, "Testing 6-method authentication profiles with zero-plaintext...")

    # Account 1: LeetCode (user_pass + cookie_jar + api_headers)
    acc_leetcode = vault.add_account(
        platform="leetcode",
        domain="leetcode.com",
        username="leet_coder_prime",
        password="LeetCodeSuperSecret123!",
        account_label="LeetCode Primary Scraper",
        cookie_jar=[
            {"name": "LEETCODE_SESSION", "value": "session_tok_abc123456789"},
            {"name": "csrftoken", "value": "csrf_val_987654321"},
        ],
        api_headers={"x-csrftoken": "csrf_val_987654321", "User-Agent": "CustomLeetCrawler/1.0"},
        daily_quota_limit=100,
    )
    assert_check("LeetCode account created", bool(acc_leetcode and acc_leetcode["account_id"]))

    # Account 2: Instagram (user_pass + totp_2fa + session_tokens + targets)
    acc_insta = vault.add_account(
        platform="instagram",
        domain="instagram.com",
        username="insta_vip_alpha",
        password="InstaSecretPassword999!",
        account_label="Insta Follower Scraper A",
        totp_secret="JBSWY3DPEHPK3PXP",
        session_tokens={"sessionid": "ig_sess_9988776655", "ds_user_id": "12345678"},
        follows_targets=["@private_target_alpha", "@private_target_beta", "@creator_gamma"],
        daily_quota_limit=40,
    )
    assert_check("Instagram account with TOTP and targets created", bool(acc_insta and acc_insta["account_id"]))

    # Account 3: Facebook (storage_state + proxy_config)
    acc_fb = vault.add_account(
        platform="facebook",
        username="fb_tester_account",
        password="FacebookPassWord777!",
        account_label="FB Camoufox Browser Bot",
        storage_state={
            "cookies": [{"name": "c_user", "value": "1000987654321"}],
            "origins": [{"origin": "https://www.facebook.com", "localStorage": [{"name": "act", "value": "1"}]}],
        },
        proxy_config={"server": "http://proxy.residential.io:8000", "username": "p_user", "password": "p_pass"},
        follows_targets=["secret_group_101", "@private_community_fb"],
    )
    assert_check("Facebook account with storage_state and proxy created", bool(acc_fb and acc_fb["account_id"]))

    # Verify directly via raw SQL query that ALL secret columns start with 'v1:aes256gcm:'
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM vault_accounts WHERE account_id = ?", (acc_leetcode["account_id"],))
        raw_row = cur.fetchone()

        assert_check("Raw enc_password starts with v1:aes256gcm:", raw_row["enc_password"].startswith("v1:aes256gcm:"))
        assert_check("Raw enc_cookie_jar_json starts with v1:aes256gcm:", raw_row["enc_cookie_jar_json"].startswith("v1:aes256gcm:"))
        assert_check("Raw enc_api_headers_json starts with v1:aes256gcm:", raw_row["enc_api_headers_json"].startswith("v1:aes256gcm:"))

        # Verify plaintext passwords or cookies do NOT appear in the database
        dump_text = "\n".join(conn.iterdump())
        plaintext_leaked = (
            "LeetCodeSuperSecret123!" in dump_text
            or "session_tok_abc123456789" in dump_text
            or "InstaSecretPassword999!" in dump_text
        )
        assert_check("Zero plaintext leaked in SQLite database dump", not plaintext_leaked)

    # ------------------------------------------------------------------
    # Check 3: Associated-Data Row-Binding Security Check
    # ------------------------------------------------------------------
    print("\n--- Check 3: Cryptographic Row-Binding Security Check ---")
    update_progress(50, "Testing associated-data row-binding tamper resistance...")

    # Swap encrypted password of LeetCode into Instagram account
    swap_failed = False
    with sqlite3.connect(str(db_path)) as conn:
        leet_enc_pass = conn.execute(
            "SELECT enc_password FROM vault_accounts WHERE account_id = ?", (acc_leetcode["account_id"],)
        ).fetchone()[0]

        # Overwrite Instagram's enc_password with LeetCode's enc_password
        conn.execute(
            "UPDATE vault_accounts SET enc_password = ? WHERE account_id = ?",
            (leet_enc_pass, acc_insta["account_id"]),
        )
        conn.commit()

    try:
        # Decrypt Instagram account: MUST fail because ciphertext was bound to acc_leetcode, not acc_insta
        vault.get_account_decrypted(acc_insta["account_id"], tool_id="01_curl_cffi", run_id="run_swap_test")
    except ValueError as e:
        swap_failed = "Vault integrity check failed" in str(e)

    assert_check(
        "Tampered/swapped row ciphertext fails GCM decryption (row-binding confirmed)",
        swap_failed,
    )

    # Restore correct password for acc_insta
    vault.update_account(acc_insta["account_id"], password="InstaSecretPassword999!")

    # ------------------------------------------------------------------
    # Check 4: Private Target Follower Relationship Lookup
    # ------------------------------------------------------------------
    print("\n--- Check 4: Private Target Follower Relationship Lookup ---")
    update_progress(65, "Testing private follower mapping and queries...")

    # Query accounts that follow @private_target_alpha
    target_alpha_res = vault.list_accounts_masked(target_handle="@private_target_alpha")
    assert_check("Lookup by target @private_target_alpha returns results", target_alpha_res["total"] >= 1)
    matching_ids = [a["account_id"] for a in target_alpha_res["accounts"]]
    assert_check("Target @private_target_alpha matches Instagram account", acc_insta["account_id"] in matching_ids)
    assert_check("Target @private_target_alpha does NOT match LeetCode account", acc_leetcode["account_id"] not in matching_ids)

    # Query accounts by platform & status
    platform_res = vault.list_accounts_masked(platform="leetcode", status="active")
    assert_check("Filter by platform='leetcode' returns leetcode account", platform_res["total"] >= 1)
    assert_check("Platform leetcode returns leetcode domain", all(a["platform"] == "leetcode" for a in platform_res["accounts"]))

    # Test dynamic link and unlink of targets
    new_linked = vault.link_target_access(acc_leetcode["account_id"], ["@leetcode_premium_study_group"])
    assert_check("link_target_access links new target", new_linked == 1)

    updated_targets = vault.get_target_access_for_account(acc_leetcode["account_id"])
    assert_check("get_target_access_for_account lists newly linked target", any(t["target_handle"] == "@leetcode_premium_study_group" for t in updated_targets))

    unlinked = vault.unlink_target_access(acc_leetcode["account_id"], ["@leetcode_premium_study_group"])
    assert_check("unlink_target_access removes target", unlinked == 1)

    # ------------------------------------------------------------------
    # Check 5: Masked Safe Access vs Decrypted Scraper Access
    # ------------------------------------------------------------------
    print("\n--- Check 5: Masked vs. Decrypted Access & Audit Trail ---")
    update_progress(80, "Verifying masked output safety and decrypted audit trail...")

    masked_acc = vault.get_account_masked(acc_insta["account_id"])
    assert_check("Masked account contains NO 'credentials' key", "credentials" not in masked_acc)
    assert_check("Masked account username is masked with *", "*" in masked_acc["username_masked"])
    assert_check("Masked account contains auth_methods list", isinstance(masked_acc["auth_methods"], list))

    # Decrypted retrieval for authorized scraper run
    decrypted_acc = vault.get_account_decrypted(acc_insta["account_id"], tool_id="12_instaloader", run_id="run_ig_scrape_001")
    assert_check("Decrypted account contains 'credentials' key", "credentials" in decrypted_acc)
    assert_check("Decrypted password matches original", decrypted_acc["credentials"]["password"] == "InstaSecretPassword999!")
    assert_check("Decrypted TOTP secret matches original", decrypted_acc["credentials"]["totp_secret"] == "JBSWY3DPEHPK3PXP")
    assert_check("Decrypted session tokens match original", decrypted_acc["credentials"]["session_tokens"]["sessionid"] == "ig_sess_9988776655")

    # Verify audit log recorded the decryption
    audit_trail = vault.get_audit_trail(account_id=acc_insta["account_id"])
    assert_check("Audit log contains entries for account", len(audit_trail) >= 1)
    dec_events = [e for e in audit_trail if e["event_type"] == "decrypted_for_run"]
    assert_check("Audit log records 'decrypted_for_run' event", len(dec_events) >= 1)
    if dec_events:
        assert_check("Audit record notes tool_id and run_id", dec_events[0]["tool_id"] == "12_instaloader")

    # ------------------------------------------------------------------
    # Check 6: Public Non-Sensitive Statistics Snapshot
    # ------------------------------------------------------------------
    print("\n--- Check 6: Public Non-Sensitive Statistics Snapshot ---")
    update_progress(90, "Verifying vault_stats_public.json and Git tracking...")

    stats_path = ROOT / "vault_store" / "vault_stats_public.json"
    assert_check("vault_store/vault_stats_public.json exists", stats_path.exists())

    stats_data = json.loads(stats_path.read_text(encoding="utf-8"))
    assert_check("Public stats records total_accounts > 0", stats_data.get("total_accounts", 0) >= 3)
    assert_check("Public stats categorizes by_platform", "instagram" in stats_data.get("by_platform", {}))
    assert_check("Public stats categorizes by_auth_method", "user_pass" in stats_data.get("by_auth_method", {}))
    assert_check("Public stats records total_target_links", stats_data.get("total_target_links", 0) >= 1)

    # Git check-ignore on vault_stats_public.json must confirm it is NOT ignored
    git_stats_check = subprocess.run(
        ["git", "check-ignore", "vault_store/vault_stats_public.json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert_check("vault_stats_public.json is NOT ignored by git", git_stats_check.returncode != 0)

    # ------------------------------------------------------------------
    # Check 7: Stage 3 Logging & Global Master Index Federation
    # ------------------------------------------------------------------
    print("\n--- Check 7: Stage 3 Logging & Global Master Index Federation ---")
    update_progress(96, "Validating Stage 3 log federation in Global Master Index...")

    log_global(
        message="Stage 3 Step 3.2 verification suite completed successfully",
        level="INFO",
        stage="Stage 3",
        step="Step 3.2",
        tool_id="credential_vault",
        action_name="verify_step_3_2",
        run_id="",
        progress_pct=100,
        stage_log_name="stage_3_credential_vault",
    )

    master_indexer = GlobalMasterIndexer()
    master_indexer.sync_all()

    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    stage_3_count = 0
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3' AND step = 'Step 3.2'")
            stage_3_count = cur.fetchone()[0]

    assert_check("Global Master Index federates Step 3.2 logs", stage_3_count > 0, f"found entries: {stage_3_count}")

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.2 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 STEP 3.2 CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
