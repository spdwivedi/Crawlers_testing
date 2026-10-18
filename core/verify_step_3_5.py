"""
core/verify_step_3_5.py
======================
Automated verification suite for Stage 3 - Step 3.5:
Browser Session Recorder, Universal 20-Tool Auth Injector, and Ephemeral Cookie Shredder.
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

import curl_cffi.requests as requests
from playwright.sync_api import sync_playwright

from core.auth_injector import (
    TEMP_COOKIE_DIR,
    AuthInjector,
    format_netscape_cookies_txt,
    get_auth_injector,
)
from core.browser_session_recorder import (
    BrowserSessionRecorder,
    get_browser_session_recorder,
)
from core.credential_vault import VAULT_DB_PATH, get_credential_vault
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress


class LocalAuthTestHandler(http.server.BaseHTTPRequestHandler):
    """Deterministic local HTTP endpoint to test cookie transmission & DOM rendering."""

    def do_GET(self) -> None:
        cookie_header = self.headers.get("Cookie", "")
        csrf_header = self.headers.get("X-CSRFToken", "")
        ua_header = self.headers.get("User-Agent", "")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        html = f"""<!DOCTYPE html>
<html>
<head><title>Auth Verification Target</title></head>
<body>
<h1>Local Test Auth Receiver</h1>
<div id="cookie-data">{cookie_header}</div>
<div id="csrf-data">{csrf_header}</div>
<div id="ua-data">{ua_header}</div>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        pass  # Suppress console log spam


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
    print("🚀 STARTING STAGE 3 STEP 3.5 VERIFICATION SUITE")
    print("=" * 70)

    # Start deterministic local test server
    server = http.server.HTTPServer(("127.0.0.1", 0), LocalAuthTestHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{port}"
    print(f"  🌐 Local verification server active at {base_url}")

    vault = get_credential_vault()
    recorder = get_browser_session_recorder(vault=vault)
    injector = get_auth_injector(vault=vault)

    # Unique test parameters
    uniq = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
    test_target = f"@private_reel_creator_{uniq}"
    test_platform = "instagram"
    login_url = f"{base_url}/auth/login"

    # ------------------------------------------------------------------
    # Check 1: Programmatic Browser Session Capture into Encrypted Vault
    # ------------------------------------------------------------------
    print("\n--- Check 1: Programmatic Browser Session Capture & Storage State ---")
    update_progress(20, "Testing BrowserSessionRecorder headless capture and encryption...")

    seed_cookies = [
        {"name": "sessionid", "value": f"sess_val_{uniq}", "domain": "127.0.0.1", "path": "/", "secure": False, "httpOnly": True},
        {"name": "csrftoken", "value": f"csrf_val_{uniq}", "domain": "127.0.0.1", "path": "/", "secure": False, "httpOnly": False},
        {"name": "c_user", "value": "1000999888", "domain": "127.0.0.1", "path": "/", "secure": False, "httpOnly": False},
    ]
    seed_storage = {
        "theme": "dark",
        "auth_state": "verified",
        "device_id": f"dev_{uniq}",
    }

    summary = recorder.record_browser_session(
        platform=test_platform,
        login_url=login_url,
        account_label=f"Session Test Bot {uniq}",
        interactive=False,
        engine="playwright",
        wait_seconds=5,
        follows_targets=[test_target],
        seed_cookies=seed_cookies,
        seed_local_storage=seed_storage,
    )

    rec_account_id = summary["account_id"]
    assert_check("BrowserSessionRecorder returns non-empty account_id", bool(rec_account_id))
    assert_check("Captured cookies count >= 3", summary["cookies_captured_count"] >= 3, f"count: {summary['cookies_captured_count']}")
    assert_check("Captured origins count >= 1", summary["origins_captured_count"] >= 1, f"count: {summary['origins_captured_count']}")
    assert_check("Extracted high-value token keys include sessionid", "sessionid" in summary["extracted_token_keys"])
    assert_check("Extracted high-value token keys include csrftoken", "csrftoken" in summary["extracted_token_keys"])
    assert_check("Fingerprint profile captured User-Agent", bool(summary["fingerprint_profile"].get("userAgent")))
    assert_check("Follows private target registered", test_target in summary["follows_targets"])

    # Directly inspect database to confirm authenticated AES-256-GCM row-bound encryption
    with sqlite3.connect(str(VAULT_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        raw_row = conn.execute("SELECT * FROM vault_accounts WHERE account_id = ?", (rec_account_id,)).fetchone()
        assert_check("Row exists in vault_accounts", raw_row is not None)
        if raw_row:
            assert_check("enc_cookie_jar_json starts with v1:aes256gcm: (zero plaintext)", str(raw_row["enc_cookie_jar_json"]).startswith("v1:aes256gcm:"))
            assert_check("enc_storage_state_json starts with v1:aes256gcm:", str(raw_row["enc_storage_state_json"]).startswith("v1:aes256gcm:"))
            assert_check("enc_session_tokens_json starts with v1:aes256gcm:", str(raw_row["enc_session_tokens_json"]).startswith("v1:aes256gcm:"))

        target_row = conn.execute(
            "SELECT * FROM account_target_access WHERE account_id = ? AND target_handle = ?",
            (rec_account_id, test_target.lower()),
        ).fetchone()
        assert_check("Target access mapping persisted in account_target_access", target_row is not None)

        audit_entry = conn.execute(
            "SELECT * FROM vault_audit_log WHERE account_id = ? AND event_type = 'browser_session_recorded'",
            (rec_account_id,),
        ).fetchone()
        assert_check("browser_session_recorded event written to vault_audit_log", audit_entry is not None)

    # ------------------------------------------------------------------
    # Check 2: Universal 20-Tool Auth Bundle Generation Across Batches
    # ------------------------------------------------------------------
    print("\n--- Check 2: Universal Auth Bundles Across All 4 Batches ---")
    update_progress(45, "Testing universal auth bundles for representative tools across 4 batches...")

    sample_tools = [
        ("01_curl_cffi", "Batch 1: HTTP Client"),
        ("03_scrapy", "Batch 1: Scrapy Middleware"),
        ("06_playwright", "Batch 2: Browser Automation"),
        ("09_nodriver", "Batch 2: CDP Browser"),
        ("11_yt_dlp_ffmpeg", "Batch 3: CLI Media"),
        ("12_instaloader", "Batch 3: Specialized Scraper"),
        ("13_gallery_dl", "Batch 3: Image / Media Scraper"),
        ("16_crawl4ai", "Batch 4: AI Web Crawler"),
    ]

    for tool_id, tool_desc in sample_tools:
        auth_bundle = injector.prepare_tool_auth(
            tool_id=tool_id,
            platform=test_platform,
            required_target=test_target,
            run_id=f"run_check2_{tool_id}",
            write_ephemeral_cookie_file=True,
        )

        assert_check(f"[{tool_desc}] authenticated is True", auth_bundle["authenticated"] is True)
        assert_check(f"[{tool_desc}] account_id matches recorded session", auth_bundle["account_id"] == rec_account_id)

        # Validate HTTP bundle
        http_b = auth_bundle["http_bundle"]
        assert_check(f"[{tool_desc}] HTTP bundle cookies_dict has sessionid", "sessionid" in http_b["cookies_dict"])
        assert_check(f"[{tool_desc}] HTTP bundle headers has Cookie and User-Agent", "Cookie" in http_b["headers"] and "User-Agent" in http_b["headers"])
        assert_check(f"[{tool_desc}] HTTP bundle impersonate is chrome124", http_b["impersonate"] == "chrome124")

        # Validate Scrapy bundle
        scrapy_b = auth_bundle["scrapy_bundle"]
        assert_check(f"[{tool_desc}] Scrapy bundle has cookies dict and headers (without raw Cookie)", "cookies" in scrapy_b and "Cookie" not in scrapy_b["headers"])

        # Validate Playwright bundle
        pw_b = auth_bundle["playwright_bundle"]
        assert_check(f"[{tool_desc}] Playwright storage_state has cookies & origins", "cookies" in pw_b["context_kwargs"]["storage_state"] and "origins" in pw_b["context_kwargs"]["storage_state"])

        # Validate CDP bundle
        cdp_b = auth_bundle["cdp_bundle"]
        assert_check(f"[{tool_desc}] CDP bundle has cdp_cookies and browser_args", len(cdp_b["cdp_cookies"]) >= 3 and len(cdp_b["browser_args"]) >= 2)

        # Validate CLI media bundle
        cli_b = auth_bundle["cli_media_bundle"]
        assert_check(f"[{tool_desc}] CLI media bundle has instaloader_cookies", "sessionid" in cli_b["instaloader_cookies"])

        # Validate Safe Summary
        safe_s = auth_bundle["safe_summary"]
        assert_check(f"[{tool_desc}] Safe summary masks username and reports token keys", bool(safe_s.get("username_masked")) and len(safe_s.get("token_keys", [])) >= 2)

        # Clean up any ephemeral files created in this probe
        injector.shred_ephemeral_artifacts(auth_bundle)

    # ------------------------------------------------------------------
    # Check 3: Live End-to-End Cookie & Storage Injection (Playwright & curl_cffi)
    # ------------------------------------------------------------------
    print("\n--- Check 3: Live End-to-End Cookie & Storage Injection Proof ---")
    update_progress(65, "Testing live execution with curl_cffi and Playwright context...")

    # A) Test Playwright Live Injection via context manager
    with injector.authenticated_session(tool_id="06_playwright", platform=test_platform, required_target=test_target) as auth_pw:
        assert_check("Playwright session authenticated", auth_pw["authenticated"])
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(**auth_pw["playwright_bundle"]["context_kwargs"])
            page = ctx.new_page()
            page.goto(f"{base_url}/auth/dashboard", wait_until="domcontentloaded")

            # Check cookies in context
            live_cookies = ctx.cookies()
            live_cookie_names = {c["name"] for c in live_cookies}
            assert_check("Live Playwright context contains sessionid", "sessionid" in live_cookie_names)
            assert_check("Live Playwright context contains csrftoken", "csrftoken" in live_cookie_names)

            # Check localStorage restoration
            dom_cookie_text = page.inner_text("#cookie-data")
            assert_check("Server received injected session cookies in request", f"sess_val_{uniq}" in dom_cookie_text)

            theme_val = page.evaluate("() => window.localStorage.getItem('theme')")
            auth_st = page.evaluate("() => window.localStorage.getItem('auth_state')")
            assert_check("Injected localStorage 'theme' is restored as 'dark'", theme_val == "dark")
            assert_check("Injected localStorage 'auth_state' is restored as 'verified'", auth_st == "verified")

            browser.close()

    # B) Test curl_cffi Live Injection
    with injector.authenticated_session(tool_id="01_curl_cffi", platform=test_platform, required_target=test_target) as auth_curl:
        assert_check("curl_cffi session authenticated", auth_curl["authenticated"])
        http_info = auth_curl["http_bundle"]
        resp = requests.get(
            f"{base_url}/auth/curl-test",
            cookies=http_info["cookies_dict"],
            headers=http_info["headers"],
            impersonate="chrome124",
            timeout=5,
        )
        assert_check("curl_cffi GET request succeeded (status 200)", resp.status_code == 200)
        assert_check("curl_cffi transmitted sessionid to server", f"sess_val_{uniq}" in resp.text)
        assert_check("curl_cffi transmitted csrftoken to server", f"csrf_val_{uniq}" in resp.text)

    # ------------------------------------------------------------------
    # Check 4: Ephemeral Netscape cookies.txt Creation & Automatic Shredding
    # ------------------------------------------------------------------
    print("\n--- Check 4: Ephemeral Netscape cookies.txt Creation & Secure Shredding ---")
    update_progress(80, "Testing ephemeral Netscape cookie file generation and secure zero-fill shredder...")

    ephemeral_file_captured: Path | None = None

    with injector.authenticated_session(tool_id="11_yt_dlp_ffmpeg", platform=test_platform, required_target=test_target) as auth_cli:
        cookie_path_str = auth_cli["cli_media_bundle"]["cookiefile_path"]
        assert_check("cookiefile_path is non-empty inside authenticated_session", bool(cookie_path_str))
        ephemeral_file = Path(cookie_path_str)
        ephemeral_file_captured = ephemeral_file

        assert_check("Ephemeral cookie file exists on disk inside scope", ephemeral_file.exists())
        content = ephemeral_file.read_text(encoding="utf-8")
        assert_check("File begins with Netscape HTTP Cookie File header", content.startswith("# Netscape HTTP Cookie File"))
        assert_check("File contains sessionid token and value", f"sess_val_{uniq}" in content)
        assert_check("File contains tab-separated column structure", "\t" in content)

    # Outside with block — file MUST be shredded and deleted immediately
    assert_check(
        "Ephemeral cookie file is securely unlinked upon context exit",
        ephemeral_file_captured is not None and not ephemeral_file_captured.exists(),
    )
    leftover_files = list(TEMP_COOKIE_DIR.glob("*.cookies.txt"))
    assert_check("Zero leftover .cookies.txt files remain in temp_cookies/", len(leftover_files) == 0, f"found: {leftover_files}")

    # ------------------------------------------------------------------
    # Check 5: Zero-Secret Leak & Git Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Zero-Secret Leak & Git Pre-Commit Secret Guard ---")
    update_progress(90, "Testing secret guard and logging...")

    # Verify safe_summary does not leak plaintext passwords or cookie secrets
    safe_str = json.dumps(auth_cli["safe_summary"])
    assert_check("Safe summary does not contain plaintext password", "BotPassword" not in safe_str)
    assert_check("Safe summary does not contain raw sessionid secret value", f"sess_val_{uniq}" not in safe_str)

    # Scan staged files for secrets
    guard_status = scan_staged_for_secrets(stage="Stage 3", step="Step 3.5")
    assert_check("Git Pre-Commit Secret Guard reports 0 violations", guard_status["violations_found"] is False)

    # Shut down local test server
    server.shutdown()

    # ------------------------------------------------------------------
    # Check 6: Stage 3 Logging & Global Master Index Federation
    # ------------------------------------------------------------------
    print("\n--- Check 6: Stage 3 Logging & Global Master Index Federation ---")
    update_progress(96, "Validating Stage 3 Step 3.5 log federation in Global Master Index...")

    log_global(
        message="Stage 3 Step 3.5 verification suite completed successfully",
        level="INFO",
        stage="Stage 3",
        step="Step 3.5",
        tool_id="auth_injector",
        action_name="verify_step_3_5",
        run_id="",
        progress_pct=100,
        stage_log_name="stage_3_credential_vault",
    )

    master_indexer = GlobalMasterIndexer()
    master_indexer.sync_all()

    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    step_3_5_count = 0
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3' AND step = 'Step 3.5'")
            step_3_5_count = cur.fetchone()[0]

    assert_check("Global Master Index federates Step 3.5 logs", step_3_5_count > 0, f"found entries: {step_3_5_count}")

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.5 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 STEP 3.5 CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
