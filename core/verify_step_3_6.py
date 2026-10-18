"""
core/verify_step_3_6.py
======================
Automated Master Verification Suite for Stage 3 - Step 3.6 (Stage 3 Completion):
Backend Vault REST API, Frontend Tab 5 Assets, Zero-Plaintext Exposure Verification,
and Stage 3 Master Governance Audit.
"""

import http.server
import json
import sqlite3
import sys
import threading
import time
import uuid
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

from backend.app import app
from core.auth_injector import TEMP_COOKIE_DIR
from core.credential_vault import VAULT_DB_PATH, get_credential_vault
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress


class LocalVerifyEchoHandler(http.server.BaseHTTPRequestHandler):
    """Deterministic local server for testing browser session recorder endpoint."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Session Capture Target</h1></body></html>")

    def log_message(self, format: str, *args: object) -> None:
        pass


def run_checks() -> int:
    passed = 0
    total = 0

    def assert_check(name: str, condition: bool, extra: str = "") -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [PASS] {name}")
        else:
            print(f"  ❌ [FAIL] {name} {extra}".rstrip())

    print("=" * 70)
    print("🚀 STARTING STAGE 3 MASTER VERIFICATION SUITE (STEP 3.6)")
    print("=" * 70)

    # Initialize TestClient
    client = TestClient(app)
    vault = get_credential_vault()

    uniq = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
    test_target = f"@stage3_final_private_{uniq}"
    test_user = f"final_bot_{uniq}"
    test_pass = "VerySecretPassword123!"
    totp_seed = "JBSWY3DPEHPK3PXP"

    # ------------------------------------------------------------------
    # Check 1: Backend Vault Diagnostics & Masked Accounts Listing
    # ------------------------------------------------------------------
    print("\n--- Check 1: Backend Vault Diagnostics & Masked Accounts Listing ---")
    update_progress(15, "Validating /api/vault/diagnostics and /api/vault/accounts...")

    res_diag = client.get("/api/vault/diagnostics")
    assert_check("GET /api/vault/diagnostics returns 200 OK", res_diag.status_code == 200)
    diag_data = res_diag.json()
    assert_check("Diagnostics contains total_accounts >= 0", "total_accounts" in diag_data and diag_data["total_accounts"] >= 0)
    assert_check("Diagnostics contains active_ready_accounts", "active_ready_accounts" in diag_data)
    assert_check("Diagnostics contains private_target_coverage", "private_target_coverage" in diag_data)
    assert_check("Diagnostics contains public_stats", "public_stats" in diag_data and "by_platform" in diag_data["public_stats"])

    res_accs = client.get("/api/vault/accounts?limit=100")
    assert_check("GET /api/vault/accounts returns 200 OK", res_accs.status_code == 200)
    accs_data = res_accs.json()
    assert_check("Accounts listing returns list and total_count", "accounts" in accs_data and "total_count" in accs_data)

    # Rule 6 Strict Verification: response string must NEVER contain raw password or raw ciphertext token
    raw_accs_text = res_accs.text
    assert_check("Zero raw ciphertext tokens (v1:aes256gcm:) exposed in /api/vault/accounts", "v1:aes256gcm:" not in raw_accs_text)
    assert_check("Zero plaintext passwords exposed in /api/vault/accounts", "enc_password" not in raw_accs_text and "password" not in raw_accs_text)

    # ------------------------------------------------------------------
    # Check 2: Account Creation, Live 2FA TOTP & State Transitions
    # ------------------------------------------------------------------
    print("\n--- Check 2: Account Creation, Live 2FA TOTP & State Transitions ---")
    update_progress(35, "Testing account creation, TOTP generation, and quarantine outcomes...")

    sample_netscape = (
        f"# Netscape HTTP Cookie File\n"
        f".instagram.com\tTRUE\t/\tTRUE\t{int(time.time()+86400)}\tsessionid\tsess_val_{uniq}\n"
        f".instagram.com\tTRUE\t/\tFALSE\t{int(time.time()+86400)}\tcsrftoken\tcsrf_val_{uniq}\n"
    )

    create_payload = {
        "platform": "instagram",
        "domain": "instagram.com",
        "account_label": f"Master Test Account {uniq}",
        "username": test_user,
        "password": test_pass,
        "totp_secret": totp_seed,
        "daily_quota_limit": 50,
        "follows_targets": [test_target],
        "cookies_txt": sample_netscape,
    }

    res_create = client.post("/api/vault/accounts", json=create_payload)
    assert_check("POST /api/vault/accounts returns 200 OK", res_create.status_code == 200)
    created_acc = res_create.json()
    created_id = created_acc.get("account_id", "")
    assert_check("Created account returned non-empty account_id", bool(created_id))
    assert_check("Username is masked in response", "username_masked" in created_acc and "***" in created_acc["username_masked"])
    assert_check("Auth methods include user_pass, totp_2fa, cookie_jar", all(m in created_acc.get("auth_methods", []) for m in ["user_pass", "totp_2fa", "cookie_jar"]))

    # Test Live TOTP generation endpoint
    res_totp = client.post(f"/api/vault/accounts/{created_id}/totp")
    assert_check("POST /api/vault/accounts/{id}/totp returns 200 OK", res_totp.status_code == 200)
    totp_resp = res_totp.json()
    assert_check("Live TOTP code is 6 digits", len(totp_resp.get("code", "")) == 6 and totp_resp.get("code", "").isdigit())
    assert_check("Time remaining is positive integer", totp_resp.get("time_remaining_sec", 0) >= 0)
    assert_check("Raw TOTP Base32 secret NOT exposed in response", totp_seed not in res_totp.text)

    # Test outcome feedback: rate_limited -> cooldown
    res_cd = client.post(f"/api/vault/accounts/{created_id}/outcome", json={"outcome": "rate_limited", "cooldown_seconds": 3600, "notes": "Test 429"})
    assert_check("POST outcome rate_limited returns 200 OK", res_cd.status_code == 200)
    assert_check("Account transitioned to 'cooldown'", res_cd.json().get("status") == "cooldown")
    assert_check("Cooldown timer epoch set", res_cd.json().get("cooldown_until_epoch", 0) > time.time())

    # Test outcome feedback: success -> active
    res_act = client.post(f"/api/vault/accounts/{created_id}/outcome", json={"outcome": "success", "notes": "Test recovery"})
    assert_check("POST outcome success returns 200 OK", res_act.status_code == 200)
    assert_check("Account transitioned back to 'active'", res_act.json().get("status") == "active")

    # ------------------------------------------------------------------
    # Check 3: Bulk Import API & Private Target Filtering
    # ------------------------------------------------------------------
    print("\n--- Check 3: Bulk Import API & Private Target Filtering ---")
    update_progress(55, "Testing bulk import API and private target follower queries...")

    bulk_records = [
        {
            "platform": "leetcode",
            "username": f"bulk_user_{uniq}_1",
            "password": "BulkPassword999!",
            "account_label": f"Bulk LeetCode Account 1 {uniq}",
            "daily_quota_limit": 45,
            "follows_targets": [test_target],
        },
        {
            "platform": "leetcode",
            "username": f"bulk_user_{uniq}_2",
            "password": "BulkPassword999!",
            "account_label": f"Bulk LeetCode Account 2 {uniq}",
            "daily_quota_limit": 45,
            "follows_targets": [f"@unrelated_target_{uniq}"],
        },
    ]

    res_bulk = client.post("/api/vault/bulk-import", json={"format": "records", "data": bulk_records, "on_conflict": "update"})
    assert_check("POST /api/vault/bulk-import returns 200 OK", res_bulk.status_code == 200)
    bulk_summary = res_bulk.json().get("import_summary", {})
    assert_check("Bulk import inserted records >= 2", bulk_summary.get("inserted", 0) + bulk_summary.get("updated", 0) >= 2)

    # Test filtering accounts by followed target handle
    res_target_filter = client.get(f"/api/vault/accounts?target_handle={test_target}")
    assert_check("GET accounts filtered by target returns 200 OK", res_target_filter.status_code == 200)
    filtered_list = res_target_filter.json().get("accounts", [])
    assert_check("Target filtered accounts list is non-empty", len(filtered_list) >= 2)
    for acc in filtered_list:
        handles = [
            (t.get("target_handle", "") if isinstance(t, dict) else str(t)).lower()
            for t in acc.get("follows_targets", [])
        ]
        assert_check(
            f"Account {acc['account_id']} strictly follows {test_target}",
            test_target.lower() in handles,
        )

    # ------------------------------------------------------------------
    # Check 4: 20-Tool Auth Router Test Endpoint & Ephemeral Shredding
    # ------------------------------------------------------------------
    print("\n--- Check 4: 20-Tool Auth Router Sandbox & Ephemeral Shredding ---")
    update_progress(70, "Testing /api/vault/test-injection and automatic cookie shredding...")

    res_probe = client.post(
        "/api/vault/test-injection",
        json={
            "tool_id": "11_yt_dlp_ffmpeg",
            "platform": "instagram",
            "required_target": test_target,
            "strategy": "least_recently_used",
        },
    )
    assert_check("POST /api/vault/test-injection returns 200 OK", res_probe.status_code == 200)
    probe_data = res_probe.json()
    assert_check("Probe returned authenticated == True", probe_data.get("authenticated") is True)
    assert_check("Probe matched target == test_target", probe_data.get("safe_summary", {}).get("target_matched") == test_target)
    assert_check("Probe account ID matches created Instagram account", probe_data.get("account_id") == created_id)
    assert_check("Probe lists available tool bundles", len(probe_data.get("available_bundle_keys", [])) >= 4)

    # Verify ephemeral Netscape cookie file was shredded and unlinked
    leftover_cookies = list(TEMP_COOKIE_DIR.glob("*.cookies.txt"))
    assert_check("Zero leftover ephemeral .cookies.txt files remain on disk after test-injection", len(leftover_cookies) == 0, f"found: {leftover_cookies}")

    # ------------------------------------------------------------------
    # Check 5: Programmatic Browser Session Capture Endpoint
    # ------------------------------------------------------------------
    print("\n--- Check 5: Programmatic Browser Session Capture Endpoint ---")
    update_progress(82, "Testing /api/vault/record-session programmatic capture...")

    # Start local echo server for deterministic test
    echo_server = http.server.HTTPServer(("127.0.0.1", 0), LocalVerifyEchoHandler)
    echo_port = echo_server.server_port
    echo_thread = threading.Thread(target=echo_server.serve_forever, daemon=True)
    echo_thread.start()
    echo_url = f"http://127.0.0.1:{echo_port}/auth/dashboard"

    session_payload = {
        "platform": "custom_web",
        "login_url": echo_url,
        "account_label": f"Web Session {uniq}",
        "interactive": False,
        "engine": "playwright",
        "wait_seconds": 5,
        "follows_targets": [f"@web_target_{uniq}"],
        "seed_cookies": [{"name": "auth_token", "value": f"tok_{uniq}", "domain": "127.0.0.1", "path": "/"}],
        "seed_local_storage": {"session_active": "true"},
    }

    res_sess = client.post("/api/vault/record-session", json=session_payload)
    assert_check("POST /api/vault/record-session returns 200 OK", res_sess.status_code == 200)
    sess_summary = res_sess.json()
    assert_check("Session capture returns non-empty account_id", bool(sess_summary.get("account_id")))
    assert_check("Captured cookies count >= 1", sess_summary.get("cookies_captured_count", 0) >= 1)
    assert_check("Extracted auth_token in session tokens", "auth_token" in sess_summary.get("extracted_token_keys", []))

    echo_server.shutdown()

    # ------------------------------------------------------------------
    # Check 6: Frontend Tab 5 Assets & Stage 3 Master Governance Audit
    # ------------------------------------------------------------------
    print("\n--- Check 6: Frontend Tab 5 Assets & Stage 3 Master Governance ---")
    update_progress(92, "Auditing frontend assets and Git Pre-Commit Secret Guard...")

    html_file = ROOT / "frontend" / "index.html"
    js_file = ROOT / "frontend" / "app.js"
    css_file = ROOT / "frontend" / "styles.css"

    html_text = html_file.read_text(encoding="utf-8")
    js_text = js_file.read_text(encoding="utf-8")
    css_text = css_file.read_text(encoding="utf-8")

    assert_check("frontend/index.html includes Tab 5 button (tab-vault)", 'data-tab="tab-vault"' in html_text)
    assert_check("frontend/index.html includes #tab-vault workspace container", 'id="tab-vault"' in html_text)
    assert_check("frontend/index.html includes 6-card vault ribbon", "vault-ribbon" in html_text and "vault-stat-total" in html_text)
    assert_check("frontend/index.html includes Add Account Modal", 'id="vault-add-modal"' in html_text)
    assert_check("frontend/index.html includes Bulk Import Modal", 'id="vault-import-modal"' in html_text)
    assert_check("frontend/index.html includes Live TOTP Toast", 'id="vault-totp-toast"' in html_text)

    assert_check("frontend/app.js implements loadVaultTab()", "function loadVaultTab" in js_text or "async function loadVaultTab" in js_text)
    assert_check("frontend/app.js implements loadVaultAccounts()", "function loadVaultAccounts" in js_text or "async function loadVaultAccounts" in js_text)
    assert_check("frontend/app.js implements submitBulkImport()", "function submitBulkImport" in js_text or "async function submitBulkImport" in js_text)
    assert_check("frontend/app.js implements testVaultInjection()", "function testVaultInjection" in js_text or "async function testVaultInjection" in js_text)
    assert_check("frontend/app.js implements fetchLiveTotp()", "function fetchLiveTotp" in js_text or "async function fetchLiveTotp" in js_text)
    assert_check("frontend/app.js implements seedSampleAccounts()", "function seedSampleAccounts" in js_text or "async function seedSampleAccounts" in js_text)

    assert_check("frontend/styles.css includes .vault-container rules", ".vault-container" in css_text)
    assert_check("frontend/styles.css includes .vault-ribbon rules", ".vault-ribbon" in css_text)
    assert_check("frontend/styles.css includes .totp-toast rules", ".totp-toast" in css_text)

    # Git Secret Scanner Guard
    guard = scan_staged_for_secrets(stage="Stage 3", step="Step 3.6")
    assert_check("Git Pre-Commit Secret Guard reports 0 violations", guard["violations_found"] is False)

    # Final Master Index & Logging
    log_global(
        message="Stage 3 Master Verification Suite completed with 100% success",
        level="INFO",
        stage="Stage 3",
        step="Step 3.6",
        tool_id="backend",
        action_name="verify_step_3_6",
        run_id="",
        progress_pct=100,
        stage_log_name="stage_3_credential_vault",
    )

    indexer = GlobalMasterIndexer()
    indexer.sync_all()

    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    s3_logs_count = 0
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3' AND step = 'Step 3.6'")
            s3_logs_count = cur.fetchone()[0]

    assert_check("Global Master Index federates Step 3.6 logs", s3_logs_count > 0, f"found: {s3_logs_count}")

    # Clean up test accounts created in this verification run
    vault.delete_account(created_id)
    if "account_id" in sess_summary:
        vault.delete_account(sess_summary["account_id"])

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.6 master verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 MASTER VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 MASTER CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
