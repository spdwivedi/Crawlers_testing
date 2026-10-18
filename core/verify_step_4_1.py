"""
core/verify_step_4_1.py
=======================
Focused Verification Suite for Stage 4 — Step 4.1:
Human Timing, Jitter & Pacing Engine, Stage 4 Logging, and Governance.

Verifies:
1. Statistical Properties of Distributions (Gaussian, Log-Normal, Exponential Backoff Jitter).
2. Contextual Action Delay Calculators (keystrokes, reading pauses, stream chunk pacing, burst delays).
3. Timing Profile Dispatch & Wall-Clock Execution (sleep execution matching calculated delay within tolerance).
4. Stage 4 Logging & Governance Audit (stage_4_working_ways.jsonl, FTS5 global master index federation, Pre-Commit Secret Guard, Rule 7).
"""

import math
import random
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.human_timing import HumanTimingEngine, TimingProfile
from core.logger_engine import log_global
from core.state_tracker import update_progress

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, condition: bool, details: str = "") -> None:
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  ✅ [PASS] {name}")
        log_global(
            message=f"CHECK PASSED: {name}",
            level="INFO",
            stage="Stage 4",
            step="Step 4.1",
            tool_id="human_timing",
            action_name="verify_human_timing",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.1",
            tool_id="human_timing",
            action_name="verify_human_timing",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("🚀 STARTING STAGE 4 STEP 4.1 VERIFICATION SUITE")
    print("   Human Timing Engine, Contextual Pacing & Stage 4 Governance")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 verification suite...")
    engine = HumanTimingEngine()

    # ------------------------------------------------------------------
    # Check 1: Statistical Properties of Distributions
    # ------------------------------------------------------------------
    print("--- Check 1: Statistical Properties of Distributions ---")
    update_progress(15, "Sampling 1,000 Gaussian delays...")

    target_mean = 5.0
    target_std = 1.0
    min_gauss = 1.0
    max_gauss = 10.0
    gauss_samples = [
        HumanTimingEngine.gaussian_delay(target_mean, target_std, min_gauss, max_gauss)
        for _ in range(1000)
    ]

    sample_mean = sum(gauss_samples) / len(gauss_samples)
    mean_diff_pct = abs(sample_mean - target_mean) / target_mean
    assert_check(
        "Gaussian distribution mean is within 5% of target",
        mean_diff_pct <= 0.05,
        f"Target: {target_mean}, Sample mean: {sample_mean:.4f} (diff: {mean_diff_pct*100:.2f}%)",
    )
    assert_check(
        "Gaussian samples strictly adhere to [min_val, max_val] clamps",
        all(min_gauss <= s <= max_gauss for s in gauss_samples),
        f"Out of bounds in 1,000 samples: min={min(gauss_samples):.3f}, max={max(gauss_samples):.3f}",
    )

    update_progress(30, "Sampling 1,000 Log-Normal delays & measuring skewness...")
    lognorm_samples = [
        HumanTimingEngine.log_normal_delay(median=2.5, sigma=0.6, min_val=0.5, max_val=15.0)
        for _ in range(1000)
    ]
    assert_check(
        "Log-Normal samples strictly adhere to [min_val, max_val] clamps",
        all(0.5 <= s <= 15.0 for s in lognorm_samples),
        f"Out of bounds: min={min(lognorm_samples):.3f}, max={max(lognorm_samples):.3f}",
    )

    ln_mean = sum(lognorm_samples) / len(lognorm_samples)
    m2 = sum((s - ln_mean) ** 2 for s in lognorm_samples) / len(lognorm_samples)
    m3 = sum((s - ln_mean) ** 3 for s in lognorm_samples) / len(lognorm_samples)
    skewness = m3 / (m2 ** 1.5)
    assert_check(
        "Log-Normal distribution exhibits positive skewness (right-tail human dwell modeling)",
        skewness > 0.0,
        f"Skewness was {skewness:.4f} (expected > 0)",
    )

    update_progress(45, "Testing Exponential Backoff with Decorrelated Jitter across 5 attempts...")
    prev_mean = 0.0
    exponential_growth_valid = True
    jitter_bounds_valid = True

    for attempt in range(1, 6):
        base = 1.0
        jitter_ratio = 0.5
        temp = min(60.0, base * (2 ** attempt))
        expected_low = temp * (1.0 - jitter_ratio)
        expected_high = temp * (1.0 + jitter_ratio)

        samples = [
            HumanTimingEngine.exponential_backoff_jitter(base=base, attempt=attempt, max_delay=60.0, jitter_ratio=jitter_ratio)
            for _ in range(50)
        ]

        if not all(expected_low <= s <= expected_high for s in samples):
            jitter_bounds_valid = False

        cur_mean = sum(samples) / len(samples)
        if attempt > 1 and cur_mean <= prev_mean:
            exponential_growth_valid = False
        prev_mean = cur_mean

    assert_check(
        "Exponential backoff delays grow monotonically across successive retry attempts",
        exponential_growth_valid,
    )
    assert_check(
        "Exponential backoff jitter remains strictly bounded within jitter_ratio bounds",
        jitter_bounds_valid,
    )

    # ------------------------------------------------------------------
    # Check 2: Contextual Action Delay Calculators
    # ------------------------------------------------------------------
    print("\n--- Check 2: Contextual Action Delay Calculators ---")
    update_progress(60, "Auditing contextual action calculators...")

    keystrokes = [HumanTimingEngine.keystroke_delay(wpm_target=65) for _ in range(100)]
    assert_check(
        "Keystroke delay returns realistic sub-second human typing intervals",
        all(0.04 <= k <= 0.70 for k in keystrokes),
        f"Min keystroke: {min(keystrokes):.4f}s, Max keystroke: {max(keystrokes):.4f}s",
    )
    avg_keystroke = sum(keystrokes) / len(keystrokes)
    assert_check(
        "Keystroke delay mean reflects realistic typing cadence (100ms - 350ms)",
        0.10 <= avg_keystroke <= 0.35,
        f"Average keystroke delay: {avg_keystroke:.4f}s",
    )

    read_50_samples = [HumanTimingEngine.reading_pause(word_count=50, reading_wpm=220) for _ in range(30)]
    read_250_samples = [HumanTimingEngine.reading_pause(word_count=250, reading_wpm=220) for _ in range(30)]
    avg_read_50 = sum(read_50_samples) / len(read_50_samples)
    avg_read_250 = sum(read_250_samples) / len(read_250_samples)
    assert_check(
        "Reading pause scales proportionally with document word count",
        avg_read_250 > avg_read_50 * 2.5,
        f"50 words avg: {avg_read_50:.2f}s, 250 words avg: {avg_read_250:.2f}s",
    )

    pacing_samples = [HumanTimingEngine.chunk_download_pacing(chunk_duration_sec=3.0, playback_rate=1.0) for _ in range(50)]
    assert_check(
        "Chunk download pacing returns bounded media stream buffer intervals",
        all(0.2 <= p <= 3.0 for p in pacing_samples),
        f"Min pacing: {min(pacing_samples):.3f}s, Max pacing: {max(pacing_samples):.3f}s",
    )

    burst_micro = [HumanTimingEngine.session_burst_delay(action_count_in_burst=1) for _ in range(20)]
    burst_pause = [HumanTimingEngine.session_burst_delay(action_count_in_burst=3) for _ in range(20)]
    assert_check(
        "Session burst delay provides rapid micro-bursts followed by deep comprehension pauses",
        all(0.4 <= b <= 1.2 for b in burst_micro) and all(4.0 <= b <= 12.0 for b in burst_pause),
        f"Micro avg: {sum(burst_micro)/len(burst_micro):.2f}s, Pause avg: {sum(burst_pause)/len(burst_pause):.2f}s",
    )

    # ------------------------------------------------------------------
    # Check 3: Profile Dispatch & Wall-Clock Execution
    # ------------------------------------------------------------------
    print("\n--- Check 3: Profile Dispatch & Wall-Clock Execution ---")
    update_progress(75, "Testing profile resolution & wall-clock execution...")

    fast_delay = engine.get_delay(TimingProfile.FAST_AUTOMATED)
    assert_check(
        "FAST_AUTOMATED profile returns minimized latency (0.10s - 0.50s)",
        0.10 <= fast_delay <= 0.50,
        f"Fast delay: {fast_delay:.4f}s",
    )

    balanced_delay = engine.get_delay(TimingProfile.BALANCED_HUMAN)
    assert_check(
        "BALANCED_HUMAN profile returns natural browsing delays (1.0s - 4.5s)",
        1.0 <= balanced_delay <= 4.5,
        f"Balanced delay: {balanced_delay:.4f}s",
    )

    stealth_delay = engine.get_delay(TimingProfile.STEALTH_PARANOID)
    assert_check(
        "STEALTH_PARANOID profile returns extended dwell intervals (2.5s - 25.0s)",
        2.5 <= stealth_delay <= 25.0,
        f"Stealth delay: {stealth_delay:.4f}s",
    )

    # Test wall-clock sleep execution
    t_target = 0.035
    elapsed = engine.sleep(target_delay=t_target)
    diff_ms = abs(elapsed - t_target) * 1000.0
    assert_check(
        "Wall-clock sleep execution matches calculated delay within 15ms tolerance",
        diff_ms <= 15.0,
        f"Target: {t_target*1000:.1f}ms, Elapsed: {elapsed*1000:.1f}ms (diff: {diff_ms:.2f}ms)",
    )
    assert_check(
        "HumanTimingEngine records last_delay attribute for auditing",
        engine.last_delay == t_target,
    )

    # ------------------------------------------------------------------
    # Check 4: Stage 4 Logging & Governance Audit
    # ------------------------------------------------------------------
    print("\n--- Check 4: Stage 4 Logging & Governance Audit ---")
    update_progress(85, "Auditing Stage 4 logs & FTS5 federation...")

    stage4_log = ROOT / "logs" / "stages" / "stage_4_working_ways.jsonl"
    assert_check(
        "Stage 4 log file exists: logs/stages/stage_4_working_ways.jsonl",
        stage4_log.exists(),
    )

    # Synchronize all logs into global SQLite FTS5 index
    indexer = GlobalMasterIndexer()
    indexer.sync_all()

    master_db = ROOT / "index_store" / "global_master_index.sqlite"
    assert_check("Global master SQLite database exists", master_db.exists())

    conn = sqlite3.connect(str(master_db))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 4'")
    stage4_indexed_count = cur.fetchone()[0]
    conn.close()

    assert_check(
        "GlobalMasterIndexer federated Stage 4 logs into global_logs table",
        stage4_indexed_count > 0,
        f"Indexed Stage 4 logs: {stage4_indexed_count}",
    )

    update_progress(95, "Scanning Git index for secret leaks & verifying Rule 7...")
    gemini_text = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    assert_check(
        "GEMINI.md header specifies Stage 4 and contains Rule 7 (Human Simulation & Timing Discipline)",
        ("Stage: 4" in gemini_text or "Stage:** 4" in gemini_text or "Stage 4" in gemini_text) and "Rule 7" in gemini_text,
        f"Stage 4 found: {'Stage:** 4' in gemini_text or 'Stage: 4' in gemini_text}, Rule 7 found: {'Rule 7' in gemini_text}",
    )

    # Check Pre-Commit Secret Guard
    subprocess.run(["git", "add", "-A"], cwd=str(ROOT), check=True)
    scan_results = scan_staged_for_secrets()
    subprocess.run(["git", "reset", "HEAD"], cwd=str(ROOT), capture_output=True, check=True)

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
        print("🎉 ALL STAGE 4 STEP 4.1 CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Stage 4 Step 4.1 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
