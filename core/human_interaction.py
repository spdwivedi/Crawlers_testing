"""
core/human_interaction.py
=========================
Physical Browser Interaction Engine — Stage 4 / Step 4.2.

Implements human pointer physics and authentic browsing kinematics:
1. Bezier Trajectory Mathematics & Pointer Dynamics (Fitts' Law easing, 2D Gaussian clicks).
2. Human Variable Scrolling & Re-Read Backtracking (wheel event chunks, eye-scan dwell).
3. Keystroke Cadence with Typo/Backspace Simulation (QWERTY adjacent keys, cognitive pause).
4. Session Warmup & Natural Feed Browsing (pre-scrape cursor wandering and viewport dwell).
"""

from __future__ import annotations

import math
import random
import time
from typing import Any, Sequence

from core.human_timing import HumanTimingEngine, TimingProfile

# QWERTY adjacent key map for authentic physical typo simulation
QWERTY_ADJACENT_KEYS: dict[str, list[str]] = {
    "a": ["q", "w", "s", "z"],
    "b": ["v", "g", "h", "n"],
    "c": ["x", "d", "f", "v"],
    "d": ["s", "e", "r", "f", "c", "x"],
    "e": ["w", "s", "d", "r"],
    "f": ["d", "r", "t", "g", "v", "c"],
    "g": ["f", "t", "y", "h", "b", "v"],
    "h": ["g", "y", "u", "j", "n", "b"],
    "i": ["u", "j", "k", "o"],
    "j": ["h", "u", "i", "k", "m", "n"],
    "k": ["j", "i", "o", "l", "m"],
    "l": ["k", "o", "p"],
    "m": ["n", "j", "k"],
    "n": ["b", "h", "j", "m"],
    "o": ["i", "k", "l", "p"],
    "p": ["o", "l"],
    "q": ["w", "a", "s"],
    "r": ["e", "d", "f", "t"],
    "s": ["a", "w", "e", "d", "x", "z"],
    "t": ["r", "f", "g", "y"],
    "u": ["y", "h", "j", "i"],
    "v": ["c", "f", "g", "b"],
    "w": ["q", "a", "s", "e"],
    "x": ["z", "s", "d", "c"],
    "y": ["t", "g", "h", "u"],
    "z": ["a", "s", "x"],
}


class HumanInteractionEngine:
    """
    Physical interaction engine that simulates human kinematics on Playwright/browser pages.
    """

    def __init__(self, timing_engine: HumanTimingEngine | None = None) -> None:
        self.timing = timing_engine or HumanTimingEngine()
        self._mouse_pos: tuple[float, float] = (150.0, 150.0)

    # -------------------------------------------------------------------------
    # 1. Bezier Trajectory Mathematics & Pointer Dynamics
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_bezier_path(
        start: tuple[float, float],
        end: tuple[float, float],
        steps: int = 25,
        deviation: float = 1.0,
    ) -> list[tuple[float, float]]:
        """
        Generates a smooth cubic Bezier curve with Fitts' Law velocity easing,
        randomized perpendicular normal offsets, and biological micro-jitter.
        """
        x0, y0 = float(start[0]), float(start[1])
        x3, y3 = float(end[0]), float(end[1])
        dx = x3 - x0
        dy = y3 - y0
        dist = math.hypot(dx, dy)

        if dist < 1e-4 or steps <= 1:
            return [(x3, y3)] * max(1, steps)

        # Unit normal vector perpendicular to chord
        nx = -dy / dist
        ny = dx / dist

        # Randomize curvature direction (human arm arc preference)
        side = random.choice([-1.0, 1.0])

        # Control point 1 (early flight)
        u1 = random.uniform(0.20, 0.40)
        h1 = side * random.uniform(0.12, 0.35) * dist * deviation
        x1 = x0 + u1 * dx + h1 * nx
        y1 = y0 + u1 * dy + h1 * ny

        # Control point 2 (mid-to-late flight)
        u2 = random.uniform(0.60, 0.85)
        h2 = side * random.uniform(0.08, 0.28) * dist * deviation
        x2 = x0 + u2 * dx + h2 * nx
        y2 = y0 + u2 * dy + h2 * ny

        points: list[tuple[float, float]] = []
        for i in range(steps):
            # Normalization tau in [0, 1]
            tau = i / float(steps - 1)

            # S-curve velocity easing (smoothstep: slow start -> fast mid-flight -> gentle decel)
            t = tau * tau * (3.0 - 2.0 * tau)

            # Cubic Bezier evaluation
            one_minus_t = 1.0 - t
            bx = (
                (one_minus_t ** 3) * x0
                + 3.0 * (one_minus_t ** 2) * t * x1
                + 3.0 * one_minus_t * (t ** 2) * x2
                + (t ** 3) * x3
            )
            by = (
                (one_minus_t ** 3) * y0
                + 3.0 * (one_minus_t ** 2) * t * y1
                + 3.0 * one_minus_t * (t ** 2) * y2
                + (t ** 3) * y3
            )

            # Add biological micro-jitter to intermediate flight points (excluding exact start/end)
            if 0 < i < steps - 1:
                jx = random.gauss(0.0, 0.75)
                jy = random.gauss(0.0, 0.75)
                bx += jx
                by += jy

            points.append((round(bx, 2), round(by, 2)))

        return points

    def move_mouse_human(
        self,
        page: Any,
        target_x: float,
        target_y: float,
        steps: int = 30,
        deviation: float = 1.0,
    ) -> None:
        """
        Moves the mouse to (target_x, target_y) along an authentic Bezier trajectory
        with sub-millisecond Gaussian pacing.
        """
        start_x, start_y = self._mouse_pos
        path = self.generate_bezier_path(
            (start_x, start_y),
            (target_x, target_y),
            steps=steps,
            deviation=deviation,
        )

        for pt in path:
            page.mouse.move(pt[0], pt[1])
            step_delay = HumanTimingEngine.gaussian_delay(0.003, 0.001, 0.0005, 0.010)
            time.sleep(step_delay)

        self._mouse_pos = (float(target_x), float(target_y))

    def hover_and_click(
        self,
        page: Any,
        selector_or_locator: Any,
        click_delay_ms: float = 120.0,
        deviation: float = 1.0,
    ) -> tuple[float, float]:
        """
        Navigates mouse along Bezier curve to a 2D-Gaussian distributed coordinate
        strictly inside the element's bounding box, pauses, and clicks with realistic hold interval.
        Returns the chosen (target_x, target_y) coordinate.
        """
        # Resolve locator
        if isinstance(selector_or_locator, str):
            locator = page.locator(selector_or_locator)
        else:
            locator = selector_or_locator

        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass

        box = locator.bounding_box()
        if not box:
            raise ValueError(f"Target element has no bounding box or is not visible: {selector_or_locator}")

        # Compute randomized target coordinate strictly inside the box using 2D Gaussian
        cx = box["x"] + box["width"] / 2.0
        cy = box["y"] + box["height"] / 2.0
        sx = max(1.0, box["width"] * 0.15)
        sy = max(1.0, box["height"] * 0.15)

        tx = random.gauss(cx, sx)
        ty = random.gauss(cy, sy)

        # Clamp safely within element borders with a 3px padding
        pad_x = min(3.0, box["width"] * 0.1)
        pad_y = min(3.0, box["height"] * 0.1)
        tx = max(box["x"] + pad_x, min(box["x"] + box["width"] - pad_x, tx))
        ty = max(box["y"] + pad_y, min(box["y"] + box["height"] - pad_y, ty))

        # Move mouse to randomized coordinate
        self.move_mouse_human(page, tx, ty, deviation=deviation)

        # Pre-click cognitive pause
        pre_click_pause = HumanTimingEngine.log_normal_delay(0.12, 0.3, min_val=0.04, max_val=0.30)
        time.sleep(pre_click_pause)

        # Execute realistic mouse-down, hold, mouse-up
        page.mouse.down()
        hold_time = HumanTimingEngine.gaussian_delay(click_delay_ms / 1000.0, 0.02, 0.04, 0.25)
        time.sleep(hold_time)
        page.mouse.up()

        return (tx, ty)

    # -------------------------------------------------------------------------
    # 2. Human Variable Scrolling & Re-Read Backtracking
    # -------------------------------------------------------------------------

    def scroll_page_human(
        self,
        page: Any,
        target_scroll_y: int | None = None,
        max_scrolls: int = 8,
        allow_backtrack: bool = True,
        reading_pause_words: int = 80,
    ) -> dict[str, Any]:
        """
        Performs natural variable wheel scrolling with sub-step easing, reading pauses,
        and re-read backtracking navigation.
        """
        t0 = time.perf_counter()
        scroll_steps = 0
        backtrack_count = 0
        total_scrolled_px = 0

        # Read initial position
        try:
            current_y = int(page.evaluate("() => window.scrollY || window.pageYOffset || 0"))
        except Exception:
            current_y = 0

        for _ in range(max_scrolls):
            if target_scroll_y is not None and current_y >= target_scroll_y:
                break

            # Variable scroll chunk: 250px - 550px
            chunk_dy = random.randint(250, 550)
            if target_scroll_y is not None:
                remaining = target_scroll_y - current_y
                if remaining <= 0:
                    break
                chunk_dy = min(chunk_dy, max(50, remaining))

            # Break chunk into micro wheel events with easing
            sub_steps = random.randint(4, 7)
            for _ in range(sub_steps):
                sub_dy = chunk_dy / float(sub_steps)
                page.mouse.wheel(0, sub_dy)
                time.sleep(random.uniform(0.010, 0.030))

            scroll_steps += 1
            total_scrolled_px += chunk_dy
            current_y += chunk_dy

            # Eye-scan reading pause after scroll
            dwell = HumanTimingEngine.reading_pause(word_count=reading_pause_words, reading_wpm=220)
            # Bound pause to keep automation responsive
            time.sleep(min(1.2, dwell))

            # Re-Read Backtracking: 20% chance to scroll upward to re-inspect content
            if allow_backtrack and scroll_steps < max_scrolls and random.random() < 0.22:
                backtrack_dy = int(chunk_dy * random.uniform(0.15, 0.30))
                # Upward wheel events
                for _ in range(3):
                    page.mouse.wheel(0, -(backtrack_dy / 3.0))
                    time.sleep(random.uniform(0.010, 0.025))

                backtrack_count += 1
                current_y -= backtrack_dy
                # Brief review dwell
                time.sleep(random.uniform(0.15, 0.35))

            # Allow dynamic content or infinite scroll to update DOM
            try:
                page.evaluate("() => document.body.scrollHeight")
            except Exception:
                pass

        elapsed = time.perf_counter() - t0
        return {
            "scroll_steps": scroll_steps,
            "backtrack_count": backtrack_count,
            "total_scrolled_px": total_scrolled_px,
            "elapsed_time_sec": round(elapsed, 4),
        }

    # -------------------------------------------------------------------------
    # 3. Keystroke Cadence with Typo/Backspace Simulation
    # -------------------------------------------------------------------------

    def type_human(
        self,
        page: Any,
        selector_or_locator: Any,
        text: str,
        error_rate: float = 0.03,
        wpm: int = 65,
    ) -> dict[str, Any]:
        """
        Types text character-by-character into an input element with realistic human
        keystroke delays, cognitive pauses, and simulated QWERTY typos + Backspace corrections.
        """
        t0 = time.perf_counter()

        # Focus element
        if isinstance(selector_or_locator, str):
            locator = page.locator(selector_or_locator)
        else:
            locator = selector_or_locator

        try:
            self.hover_and_click(page, locator)
        except Exception:
            locator.click()

        chars_typed = 0
        typos_corrected = 0

        for char in text:
            # Check for simulated physical typo
            if error_rate > 0 and char.isalpha() and random.random() < error_rate:
                lower = char.lower()
                adj_keys = QWERTY_ADJACENT_KEYS.get(lower, [])
                if adj_keys:
                    mistake = random.choice(adj_keys)
                    if char.isupper():
                        mistake = mistake.upper()

                    # 1. Type incorrect character
                    page.keyboard.type(mistake)
                    # 2. Cognitive realization hesitation (120ms - 350ms)
                    time.sleep(random.uniform(0.120, 0.350))
                    # 3. Press Backspace to correct
                    page.keyboard.press("Backspace")
                    time.sleep(random.uniform(0.040, 0.120))
                    typos_corrected += 1

            # Type intended character
            page.keyboard.type(char)
            chars_typed += 1

            # Inter-keystroke cadence delay
            delay = HumanTimingEngine.keystroke_delay(wpm_target=wpm)
            time.sleep(delay)

        elapsed = time.perf_counter() - t0
        return {
            "chars_typed": chars_typed,
            "typos_corrected": typos_corrected,
            "elapsed_time_sec": round(elapsed, 4),
        }

    # -------------------------------------------------------------------------
    # 4. Session Warmup & Natural Feed Browsing
    # -------------------------------------------------------------------------

    def warmup_browsing_session(
        self,
        page: Any,
        target_domain: str,
        duration_sec: float = 6.0,
    ) -> dict[str, Any]:
        """
        Simulates authentic pre-scrape visitor behavior:
        viewports scrolling, gentle cursor wander across cards/links, and dwell pauses.
        """
        t0 = time.perf_counter()
        actions_performed: list[str] = []

        # 1. Initial feed scroll
        scroll_res = self.scroll_page_human(
            page,
            max_scrolls=2,
            allow_backtrack=False,
            reading_pause_words=10,
        )
        actions_performed.append(f"scrolled_{scroll_res['scroll_steps']}_viewports")

        # 2. Cursor wander & hover over visible links
        try:
            links = page.locator("a, button, [role='button'], img").all()
            hover_count = 0
            for el in links[:4]:
                if time.perf_counter() - t0 >= duration_sec - 1.0:
                    break
                box = el.bounding_box()
                if box and box["width"] > 15 and box["height"] > 15:
                    target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
                    target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
                    self.move_mouse_human(page, target_x, target_y, steps=20)
                    time.sleep(random.uniform(0.15, 0.40))
                    hover_count += 1
            if hover_count > 0:
                actions_performed.append(f"hovered_{hover_count}_interactive_elements")
            else:
                # Random mouse wander in viewport
                self.move_mouse_human(page, random.uniform(150, 500), random.uniform(150, 400), steps=20)
                actions_performed.append("wandered_cursor_in_viewport")
        except Exception:
            actions_performed.append("wandered_cursor_fallback")

        # 3. Pre-navigation dwell pause
        rem = duration_sec - (time.perf_counter() - t0)
        if rem > 0:
            time.sleep(min(rem, 1.2))
            actions_performed.append("pre_extraction_dwell_pause")

        elapsed = time.perf_counter() - t0
        return {
            "warmup_duration_sec": round(elapsed, 4),
            "actions_performed": actions_performed,
            "target_domain": target_domain,
        }
