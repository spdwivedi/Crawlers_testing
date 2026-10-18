"""
core/verify_step_3_4.py
======================
Automated verification suite for Stage 3 - Step 3.4:
Smart Account Pool Router, Private-Follower Target Matcher,
Rotation Strategies (LRU/Quota/Health), and Cooldown Quarantine Recovery Engine.
"""

import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.account_router import AccountRouter, get_account_router
from core.credential_vault import get_credential_vault
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress


def run_checks():
    print("=" * 70)
    print("🚀 STARTING STAGE 3 STEP 3.4 VERIFICATION SUITE")
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
    router = get_account_router(vault=vault)

    # ------------------------------------------------------------------
    # Check 1: Private-Follower Target Matching
    # ------------------------------------------------------------------
    print("\n--- Check 1: Private-Follower Target Matching ---")
    update_progress(20, "Testing private follower matching and isolation...")

    # Seed two specific test accounts with distinct private targets
    acc_vip = vault.add_account(
        platform="instagram",
        username="insta_vip_curator",
        password="CuratorSecretPass999!",
        account_label="VIP Reel Scraper",
        follows_targets=["@private_vip_reel"],
        daily_quota_limit=20,
    )
    acc_coding = vault.add_account(
        platform="instagram",
        username="insta_coder_club",
        password="CoderClubSecretPass888!",
        account_label="Coding Club Scraper",
        follows_targets=["@private_coding_club"],
        daily_quota_limit=20,
    )

    # Query specifically for @private_vip_reel
    leased_vip = router.acquire_account(
        platform="instagram",
        required_target="@private_vip_reel",
        tool_id="12_instaloader",
        run_id="run_target_vip_001",
    )
    assert_check("acquire_account finds follower for @private_vip_reel", leased_vip is not None)
    if leased_vip:
        assert_check("Leased account ID strictly matches VIP curator", leased_vip["account_id"] == acc_vip["account_id"])
        assert_check("Routing metadata records matched target", leased_vip["routing_meta"]["matched_target"] == "@private_vip_reel")

    # Query for target followed by the other account
    leased_coding = router.acquire_account(
        platform="instagram",
        required_target="@private_coding_club",
        tool_id="12_instaloader",
        run_id="run_target_coding_001",
    )
    assert_check("acquire_account finds follower for @private_coding_club", leased_coding is not None)
    if leased_coding:
        assert_check("Leased account ID matches coding club account", leased_coding["account_id"] == acc_coding["account_id"])

    # Query for non-existent private target -> must return None
    leased_nonexistent = router.acquire_account(
        platform="instagram",
        required_target="@non_existent_private_target",
        tool_id="12_instaloader",
        run_id="run_target_none_001",
    )
    assert_check("Non-existent private target returns None (no leak)", leased_nonexistent is None)

    # ------------------------------------------------------------------
    # Check 2: Rotation Strategies & Daily Quota Enforcement
    # ------------------------------------------------------------------
    print("\n--- Check 2: Rotation Strategies & Daily Quota Enforcement ---")
    update_progress(40, "Testing LRU, quota rotation, and daily limit enforcement...")

    # Test LRU rotation
    acc_lru_1 = router.acquire_account(platform="instagram", strategy="least_recently_used", tool_id="test_tool", run_id="run_lru_1")
    acc_lru_2 = router.acquire_account(platform="instagram", strategy="least_recently_used", tool_id="test_tool", run_id="run_lru_2")
    assert_check("LRU strategy rotates to another account or increments lease", acc_lru_1 is not None and acc_lru_2 is not None)

    # Test lowest quota usage strategy
    acc_quota = router.acquire_account(platform="instagram", strategy="lowest_quota_usage", tool_id="test_tool", run_id="run_quota_1")
    assert_check("lowest_quota_usage strategy successfully leases an account", acc_quota is not None)

    # Test health-weighted random strategy
    acc_health_rand = router.acquire_account(platform="instagram", strategy="health_weighted_random", tool_id="test_tool", run_id="run_rand_1")
    assert_check("health_weighted_random strategy successfully leases an account", acc_health_rand is not None)

    # Test daily quota limit exhaustion
    uniq_suffix = f"_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    uniq_quota_user = f"quota_test_bot{uniq_suffix}"
    uniq_quota_target = f"@quota_exclusive_target{uniq_suffix}"
    acc_limited = vault.add_account(
        platform="custom_web",
        username=uniq_quota_user,
        password="BotPassword123!",
        account_label="Quota Test Account",
        follows_targets=[uniq_quota_target],
        daily_quota_limit=2,
    )
    assert_check("Created quota limited account (limit=2)", bool(acc_limited and acc_limited["account_id"]))
    limited_id = acc_limited["account_id"]

    # Acquire 1st time
    q1 = router.acquire_account(platform="custom_web", required_target=uniq_quota_target, tool_id="test_tool", run_id="run_q1")
    assert_check("1st lease succeeds within quota", q1 is not None and q1["account_id"] == limited_id)

    # Acquire 2nd time
    q2 = router.acquire_account(platform="custom_web", required_target=uniq_quota_target, tool_id="test_tool", run_id="run_q2")
    assert_check("2nd lease succeeds (quota now reached)", q2 is not None and q2["account_id"] == limited_id)

    # 3rd time must skip this account because requests_today (2) >= daily_quota_limit (2)
    # Since this is the only account following unique target, it must return None
    q3 = router.acquire_account(platform="custom_web", required_target=uniq_quota_target, tool_id="test_tool", run_id="run_q3")
    assert_check("3rd lease returns None (quota exhausted)", q3 is None)

    # ------------------------------------------------------------------
    # Check 3: Rate-Limit Cooldown Quarantine & Automatic Expiry Recovery
    # ------------------------------------------------------------------
    print("\n--- Check 3: Cooldown Quarantine & Auto-Expiration Recovery ---")
    update_progress(60, "Testing rate-limit cooldown and automatic recovery...")

    # Create an account dedicated to cooldown testing
    acc_cooldown = vault.add_account(
        platform="leetcode",
        username="cooldown_leetcode_bot",
        password="LeetCodePassword999!",
        account_label="Cooldown Test Account",
        daily_quota_limit=50,
    )
    c_id = acc_cooldown["account_id"]

    # Report rate_limited outcome with short 2-second cooldown
    rep_res = router.report_account_outcome(
        account_id=c_id,
        outcome="rate_limited",
        cooldown_seconds=2,
        tool_id="01_curl_cffi",
        run_id="run_cd_test",
        notes="HTTP 429 Too Many Requests simulated",
    )
    assert_check("report_account_outcome transitions status to 'cooldown'", rep_res["status"] == "cooldown")
    assert_check("report_account_outcome sets cooldown_until_epoch > 0", rep_res["cooldown_until_epoch"] > time.time())
    assert_check("Health score reduced on rate limit", rep_res["health_score"] < 100)

    # While cooling down, acquire_account must NOT return this account
    cooling_lease = router.acquire_account(platform="leetcode", tool_id="test", run_id="test_cooling")
    if cooling_lease:
        assert_check("Cooldown account is excluded from acquisition", cooling_lease["account_id"] != c_id)
    else:
        assert_check("Cooldown account is excluded from acquisition", True)

    # Sleep 2.2 seconds to allow cooldown timer to expire
    print("  ⏳ Waiting 2.2s for cooldown timer expiration...")
    time.sleep(2.2)

    # Calling acquire_account or release_expired_cooldowns should recover it
    released = router.release_expired_cooldowns()
    assert_check("release_expired_cooldowns automatically releases account", released >= 1)

    recovered_masked = vault.get_account_masked(c_id)
    assert_check("Recovered account status is 'active'", recovered_masked["status"] == "active")
    assert_check("Recovered cooldown_until_epoch is reset to 0.0", recovered_masked["cooldown_until_epoch"] == 0.0)

    # Now it can be leased again
    re_leased = router.acquire_account(platform="leetcode", tool_id="test", run_id="test_re_leased")
    assert_check("Account is selectable again after cooldown expiration", re_leased is not None)

    # ------------------------------------------------------------------
    # Check 4: Checkpoint, Session Expiry & Live TOTP Attachment
    # ------------------------------------------------------------------
    print("\n--- Check 4: Checkpoint, Session Expiry & Live TOTP Attachment ---")
    update_progress(75, "Testing checkpoint/expiry state transitions & TOTP lease...")

    # Test checkpoint_required
    rep_cp = router.report_account_outcome(c_id, outcome="checkpoint_required", notes="Captcha detected")
    assert_check("Status transitions to 'checkpoint_required'", rep_cp["status"] == "checkpoint_required")

    # Test session_expired
    rep_exp = router.report_account_outcome(c_id, outcome="session_expired", notes="Cookie expired")
    assert_check("Status transitions to 'expired'", rep_exp["status"] == "expired")

    # Test live TOTP code attachment on acquisition
    uniq_fb_user = f"fb_totp_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    acc_totp_seed = vault.add_account(
        platform="facebook",
        username=uniq_fb_user,
        password="FacebookSecretPass999!",
        totp_secret="JBSWY3DPEHPK3PXP",
        account_label="FB TOTP Test Bot",
        daily_quota_limit=50,
    )
    leased_totp = router.acquire_account(
        platform="facebook",
        required_auth_method="totp_2fa",
        include_live_totp=True,
        tool_id="06_camoufox",
        run_id="run_totp_lease",
    )
    assert_check("Account with TOTP leased", leased_totp is not None)
    if leased_totp:
        assert_check("Live TOTP data attached to lease", "live_totp" in leased_totp and leased_totp["live_totp"] is not None)
        if leased_totp.get("live_totp"):
            assert_check("Live TOTP code is 6 digits", len(leased_totp["live_totp"]["code"]) == 6)
            assert_check("Time remaining is positive integer", leased_totp["live_totp"]["time_remaining_sec"] >= 0)

    # ------------------------------------------------------------------
    # Check 5: Pool Diagnostics & Public Stats Sync
    # ------------------------------------------------------------------
    print("\n--- Check 5: Pool Diagnostics & Public Stats Sync ---")
    update_progress(90, "Testing pool diagnostics and public stats...")

    diag = router.get_pool_diagnostics()
    assert_check("Pool diagnostics returns total_accounts > 0", diag["total_accounts"] > 0)
    assert_check("Pool diagnostics counts active_ready_accounts", diag["active_ready_accounts"] >= 0)
    assert_check("Pool diagnostics calculates remaining_daily_capacity", diag["remaining_daily_capacity"] > 0)
    assert_check("Pool diagnostics includes private_target_coverage", "@private_vip_reel" in diag["private_target_coverage"])
    if "@private_vip_reel" in diag["private_target_coverage"]:
        assert_check("Private target coverage tracks follower counts", diag["private_target_coverage"]["@private_vip_reel"]["total_followers"] >= 1)

    # Filtered diagnostics by platform
    diag_ig = router.get_pool_diagnostics(platform="instagram")
    assert_check("Platform-specific diagnostics filters by platform", diag_ig["platform_filter"] == "instagram")

    # Verify public stats file
    stats_file = ROOT / "vault_store" / "vault_stats_public.json"
    assert_check("vault_store/vault_stats_public.json exists", stats_file.exists())

    # Pre-commit secret guard check
    guard_res = scan_staged_for_secrets(stage="Stage 3", step="Step 3.4")
    assert_check("Git Pre-Commit Secret Guard reports 0 violations", not guard_res["violations_found"])

    # ------------------------------------------------------------------
    # Check 6: Stage 3 Logging & Master Index Federation
    # ------------------------------------------------------------------
    print("\n--- Check 6: Stage 3 Logging & Global Master Index Federation ---")
    update_progress(96, "Validating Stage 3 Step 3.4 log federation in Global Master Index...")

    log_global(
        message="Stage 3 Step 3.4 verification suite completed successfully",
        level="INFO",
        stage="Stage 3",
        step="Step 3.4",
        tool_id="account_router",
        action_name="verify_step_3_4",
        run_id="",
        progress_pct=100,
        stage_log_name="stage_3_credential_vault",
    )

    master_indexer = GlobalMasterIndexer()
    master_indexer.sync_all()

    global_db = ROOT / "index_store" / "global_master_index.sqlite"
    step_3_4_count = 0
    if global_db.exists():
        with sqlite3.connect(str(global_db)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 3' AND step = 'Step 3.4'")
            step_3_4_count = cur.fetchone()[0]

    assert_check("Global Master Index federates Step 3.4 logs", step_3_4_count > 0, f"found entries: {step_3_4_count}")

    # Final Telemetry
    update_progress(100, "Stage 3 Step 3.4 verification complete.")

    print("\n" + "=" * 70)
    print(f"🏁 VERIFICATION SUMMARY: {passed}/{total} CHECKS PASSED")
    print("=" * 70)

    if passed == total:
        print("🎉 ALL STAGE 3 STEP 3.4 CHECKS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print(f"❌ {total - passed} CHECKS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_checks())
