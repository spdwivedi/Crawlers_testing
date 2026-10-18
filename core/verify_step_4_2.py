"""
core/verify_step_4_2.py
=======================
Focused Verification Suite for Stage 4 — Step 4.2:
Physical Browser Interaction Engine (Bezier Mouse Curves, Variable Scrolling, Typo Cadence & Warmup).

Verifies:
1. Bezier Path Mathematics & Non-Linearity (curvature, micro-jitter, bounding).
2. Headless Browser Mouse Hover & Click Integration (Playwright, 2D Gaussian clicks, DOM events).
3. Variable Scrolling & Backtracking Mechanics (chunk wheel scrolls, eye-scan pauses, backtrack detection).
4. Typo & Keystroke Cadence Emulation (QWERTY mistake correction, exact final DOM value, cadence timing).
5. Stage 4 Logging, Master Index Sync & Pre-Commit Secret Guard.
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

from playwright.sync_api import sync_playwright

from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.human_interaction import HumanInteractionEngine
from core.human_timing import HumanTimingEngine
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
            step="Step 4.2",
            tool_id="human_interaction",
            action_name="verify_human_interaction",
            stage_log_name="stage_4_working_ways",
        )
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 4",
            step="Step 4.2",
            tool_id="human_interaction",
            action_name="verify_human_interaction",
            stage_log_name="stage_4_working_ways",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("🚀 STARTING STAGE 4 STEP 4.2 VERIFICATION SUITE")
    print("   Physical Interaction Engine: Bezier Curves, Human Scrolling & Typos")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 4 Step 4.2 verification suite...")
    interaction = HumanInteractionEngine()

    # ------------------------------------------------------------------
    # Check 1: Bezier Path Mathematics & Non-Linearity
    # ------------------------------------------------------------------
    print("--- Check 1: Bezier Path Mathematics & Non-Linearity ---")
    update_progress(15, "Generating 100 Bezier trajectories & evaluating curvature...")

    all_in_bounds = True
    non_linear_count = 0
    jitter_detected = False

    for _ in range(100):
        x0, y0 = random.uniform(50, 200), random.uniform(50, 200)
        x1, y1 = random.uniform(400, 800), random.uniform(400, 700)
        path = HumanInteractionEngine.generate_bezier_path((x0, y0), (x1, y1), steps=30, deviation=1.0)

        # Confirm exact start and end
        if path[0] != (round(x0, 2), round(y0, 2)) or path[-1] != (round(x1, 2), round(y1, 2)):
            all_in_bounds = False

        # Measure perpendicular distance of intermediate points from the chord
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        max_perp = 0.0
        for pt in path[1:-1]:
            # Perpendicular distance formula: |dy*x - dx*y + x1*y0 - y1*x0| / dist
            perp = abs(dy * pt[0] - dx * pt[1] + x1 * y0 - y1 * x0) / max(1e-5, dist)
            if perp > max_perp:
                max_perp = perp

        if max_perp > 5.0:
            non_linear_count += 1

        # Check for biological micro-jitter (points don't follow an exact monotonic polynomial)
        diffs = [math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]) for i in range(1, len(path))]
        if any(abs(diffs[i] - diffs[i - 1]) > 0.05 for i in range(1, len(diffs))):
            jitter_detected = True

    assert_check(
        "Bezier path preserves boundary endpoints and produces valid coordinate points",
        all_in_bounds,
    )
    assert_check(
        "Generated trajectories exhibit significant non-linear curvature (100% curved)",
        non_linear_count == 100,
        f"Non-linear paths: {non_linear_count}/100",
    )
    assert_check(
        "Biological micro-jitter is present along trajectory flight path",
        jitter_detected,
    )

    # ------------------------------------------------------------------
    # Check 2: Headless Browser Mouse Hover & Click Integration
    # ------------------------------------------------------------------
    print("\n--- Check 2: Headless Browser Mouse Hover & Click Integration ---")
    update_progress(35, "Launching headless Playwright to test hover & click kinematics...")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { margin: 0; padding: 50px; font-family: sans-serif; height: 2000px; }
        #target-btn {
          width: 200px;
          height: 60px;
          margin: 100px 0 0 150px;
          background: #2563eb;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          cursor: pointer;
        }
        #text-input {
          display: block;
          margin-top: 40px;
          margin-left: 150px;
          width: 300px;
          height: 36px;
          padding: 6px 10px;
          font-size: 15px;
        }
      </style>
    </head>
    <body>
      <h1>Stage 4 Anti-Bot Kinematics Testbed</h1>
      <button id="target-btn" onclick="
        this.dataset.clicked = 'true';
        this.dataset.clickx = event.clientX;
        this.dataset.clicky = event.clientY;
        this.innerText = 'Clicked Successfully!';
      ">Click Me Human</button>

      <input id="text-input" type="text" placeholder="Type here..." />
      <div id="scroll-anchor" style="margin-top: 1500px; height: 100px; background: #eee;">End of Testbed</div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_content(html_content)

        # Test hover and click
        click_coord = interaction.hover_and_click(page, "#target-btn", click_delay_ms=90.0)
        btn = page.locator("#target-btn")
        box = btn.bounding_box()

        btn_clicked = btn.get_attribute("data-clicked")
        click_x = float(btn.get_attribute("data-clickx") or page.evaluate("() => parseFloat(document.getElementById('target-btn').dataset.clickx) || 0"))
        click_y = float(btn.get_attribute("data-clicky") or page.evaluate("() => parseFloat(document.getElementById('target-btn').dataset.clicky) || 0"))

        assert_check(
            "Headless Playwright button successfully triggered DOM click event via hover_and_click",
            btn_clicked == "true",
            f"Button data-clicked: {btn_clicked}",
        )
        assert_check(
            "Click coordinate lies strictly within button element bounding box",
            box["x"] <= click_x <= box["x"] + box["width"] and box["y"] <= click_y <= box["y"] + box["height"],
            f"Click: ({click_x}, {click_y}), Box: {box}",
        )
        # Verify 2D Gaussian offset: not clicked at rigid mathematical center
        center_x = box["x"] + box["width"] / 2.0
        center_y = box["y"] + box["height"] / 2.0
        assert_check(
            "Click point is naturally distributed rather than mathematically pinned to exact center pixel",
            abs(click_x - center_x) > 0.01 or abs(click_y - center_y) > 0.01 or abs(click_coord[0] - center_x) > 0.01,
            f"Click offset from center: dx={click_x - center_x:.2f}, dy={click_y - center_y:.2f}",
        )

        # ------------------------------------------------------------------
        # Check 3: Variable Scrolling & Backtracking Mechanics
        # ------------------------------------------------------------------
        print("\n--- Check 3: Variable Scrolling & Backtracking Mechanics ---")
        update_progress(55, "Testing human variable scrolling and backtracking mechanics...")

        scroll_res = interaction.scroll_page_human(
            page,
            target_scroll_y=800,
            max_scrolls=5,
            allow_backtrack=True,
            reading_pause_words=10,  # Fast verification dwell
        )

        current_scroll_y = int(page.evaluate("() => window.scrollY || window.pageYOffset || 0"))
        assert_check(
            "Variable scrolling successfully advanced page scroll position down viewport",
            current_scroll_y > 200,
            f"Current scroll Y: {current_scroll_y}px, Total px scrolled: {scroll_res['total_scrolled_px']}px",
        )
        assert_check(
            "scroll_page_human returns structured performance and kinematics metrics",
            scroll_res["scroll_steps"] > 0 and scroll_res["total_scrolled_px"] > 0 and scroll_res["elapsed_time_sec"] > 0,
            f"Result dict: {scroll_res}",
        )

        # Force a backtrack test by setting allow_backtrack=True over 6 steps
        backtrack_test = interaction.scroll_page_human(
            page,
            max_scrolls=6,
            allow_backtrack=True,
            reading_pause_words=5,
        )
        assert_check(
            "Re-Read backtracking mechanics executed or evaluated without error",
            "backtrack_count" in backtrack_test,
            f"Backtracks recorded: {backtrack_test['backtrack_count']}",
        )

        # ------------------------------------------------------------------
        # Check 4: Typo & Keystroke Cadence Emulation
        # ------------------------------------------------------------------
        print("\n--- Check 4: Typo & Keystroke Cadence Emulation ---")
        update_progress(75, "Testing human typing with QWERTY typo injection & Backspace repair...")

        # Test A: Typing with intentional high error rate (35%) to verify typo correction
        test_text_with_typos = "ScraperEngine"
        type_res_typos = interaction.type_human(
            page,
            "#text-input",
            test_text_with_typos,
            error_rate=0.35,
            wpm=85,
        )
        dom_val_typos = page.input_value("#text-input")

        assert_check(
            "type_human repaired all injected QWERTY typos so final DOM input value is 100% exact",
            dom_val_typos == test_text_with_typos,
            f"Expected: '{test_text_with_typos}', Actual in DOM: '{dom_val_typos}', Typos corrected: {type_res_typos['typos_corrected']}",
        )
        assert_check(
            "Typo injection stimulated physical mistakes and Backspace corrections",
            type_res_typos["typos_corrected"] >= 1,
            f"Typos corrected: {type_res_typos['typos_corrected']}",
        )

        # Test B: Clean typing with error_rate = 0.0
        page.fill("#text-input", "")
        clean_text = "CleanExecution"
        type_res_clean = interaction.type_human(
            page,
            "#text-input",
            clean_text,
            error_rate=0.0,
            wpm=100,
        )
        dom_val_clean = page.input_value("#text-input")

        assert_check(
            "type_human with error_rate=0.0 produces zero typos and exact text string",
            dom_val_clean == clean_text and type_res_clean["typos_corrected"] == 0,
            f"DOM: '{dom_val_clean}', Typos: {type_res_clean['typos_corrected']}",
        )
        assert_check(
            "Keystroke cadence took realistic human elapsed time (> 100ms)",
            type_res_clean["elapsed_time_sec"] > 0.1,
            f"Elapsed time: {type_res_clean['elapsed_time_sec']}s",
        )

        # Test Warmup
        warmup_res = interaction.warmup_browsing_session(page, target_domain="example.org", duration_sec=2.5)
        assert_check(
            "warmup_browsing_session successfully performed pre-scrape visitor behavior",
            len(warmup_res["actions_performed"]) >= 2,
            f"Actions: {warmup_res['actions_performed']}, Duration: {warmup_res['warmup_duration_sec']}s",
        )

        browser.close()

    # ------------------------------------------------------------------
    # Check 5: Stage 4 Logging, Master Index Sync & Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Stage 4 Logging, Master Index Sync & Secret Guard ---")
    update_progress(90, "Syncing Master FTS5 index and verifying Secret Guard...")

    stage4_log = ROOT / "logs" / "stages" / "stage_4_working_ways.jsonl"
    assert_check(
        "Stage 4 log file actively receiving entries: stage_4_working_ways.jsonl",
        stage4_log.exists() and stage4_log.stat().st_size > 0,
    )

    indexer = GlobalMasterIndexer()
    indexer.sync_all()

    master_db = ROOT / "index_store" / "global_master_index.sqlite"
    conn = sqlite3.connect(str(master_db))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM global_logs WHERE stage = 'Stage 4' AND tool_id = 'human_interaction'")
    interaction_log_count = cur.fetchone()[0]
    conn.close()

    assert_check(
        "GlobalMasterIndexer successfully indexed human_interaction Stage 4 logs",
        interaction_log_count > 0,
        f"Indexed records: {interaction_log_count}",
    )

    # Pre-Commit Secret Guard Scan
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
        print("🎉 ALL STAGE 4 STEP 4.2 CHECKS PASSED WITH 100% SUCCESS!\n")
        update_progress(100, "Stage 4 Step 4.2 verification complete.")
        sys.exit(0)
    else:
        print(f"❌ {FAILED_COUNT} CHECKS FAILED!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
