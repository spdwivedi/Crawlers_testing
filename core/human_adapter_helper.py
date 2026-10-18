"""
core/human_adapter_helper.py
============================
Shared Human Mode Helper — Stage 4 / Step 4.3 (Working Way 1).

Provides clean, standardized lifecycle hooks for all 20 tool adapters:
- Pre-request delay injection (apply_pre_request_delay)
- Reading dwell pauses (apply_reading_delay)
- Stream chunk pacing (apply_chunk_pacing)
- Full browser physical navigation and interaction flows (execute_browser_human_flow, async_execute_browser_human_flow)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from core.human_interaction import HumanInteractionEngine
from core.human_timing import HumanTimingEngine, TimingProfile
from core.logger_engine import LogEngine


class HumanAdapterHelper:
    """
    Standardized adapter hook for human timing, pacing, and browser kinematics.
    """

    def __init__(
        self,
        timing_engine: HumanTimingEngine | None = None,
        interaction_engine: HumanInteractionEngine | None = None,
    ) -> None:
        self.timing = timing_engine or HumanTimingEngine()
        self.interaction = interaction_engine or HumanInteractionEngine(timing_engine=self.timing)

    # -------------------------------------------------------------------------
    # 1. Core Lifecycle Hooks
    # -------------------------------------------------------------------------

    @classmethod
    def apply_pre_request_delay(
        cls,
        profile: str | TimingProfile = "BALANCED_HUMAN",
        action_type: str = "navigate",
        logger: LogEngine | None = None,
        target_delay: float | None = None,
        timing_profile: str | TimingProfile | None = None,
    ) -> float:
        """
        Calculates and executes authentic pre-request latency pause.
        Logs the pause event if a logger is provided.
        """
        chosen_profile = timing_profile or profile
        engine = HumanTimingEngine()
        elapsed = engine.sleep(profile=chosen_profile, action_type=action_type, target_delay=target_delay)
        if logger:
            logger.info(
                f"[HUMAN-MODE] Pre-request pause executed: {elapsed:.3f}s (Profile: {chosen_profile}, Action: {action_type})",
                extra={"human_delay_sec": round(elapsed, 4), "timing_profile": str(chosen_profile)},
            )
        return elapsed

    @classmethod
    def apply_reading_delay(
        cls,
        word_count: int = 100,
        reading_wpm: int = 220,
        logger: LogEngine | None = None,
        max_pause_sec: float | None = None,
        timing_profile: str | TimingProfile | None = None,
        profile: str | TimingProfile | None = None,
    ) -> float:
        """
        Calculates realistic human reading dwell times based on content length.
        """
        chosen_profile = timing_profile or profile
        engine = HumanTimingEngine()
        pause = engine.reading_pause(word_count=word_count, reading_wpm=reading_wpm)
        if chosen_profile and str(chosen_profile).upper() in ("FAST_AUTOMATED", "TIMINGPROFILE.FAST_AUTOMATED"):
            pause = min(pause, 0.05)
        if max_pause_sec is not None:
            pause = min(pause, max_pause_sec)
        t0 = time.perf_counter()
        time.sleep(pause)
        elapsed = time.perf_counter() - t0
        if logger:
            logger.info(
                f"[HUMAN-MODE] Reading dwell pause: {elapsed:.3f}s ({word_count} words @ {reading_wpm} WPM)",
                extra={"reading_pause_sec": round(elapsed, 4), "word_count": word_count},
            )
        return elapsed

    @classmethod
    def apply_chunk_pacing(
        cls,
        chunk_duration_sec: float = 3.0,
        playback_rate: float = 1.0,
        logger: LogEngine | None = None,
        playback_ratio: float | None = None,
    ) -> float:
        """
        Applies inter-chunk download stream pacing for media extraction.
        """
        rate = playback_ratio if playback_ratio is not None else playback_rate
        engine = HumanTimingEngine()
        delay = engine.chunk_download_pacing(chunk_duration_sec=chunk_duration_sec, playback_rate=rate)
        t0 = time.perf_counter()
        time.sleep(delay)
        elapsed = time.perf_counter() - t0
        if logger:
            logger.info(
                f"[HUMAN-MODE] Stream chunk pacing delay: {elapsed:.3f}s (chunk duration: {chunk_duration_sec}s)",
                extra={"chunk_pacing_sec": round(elapsed, 4)},
            )
        return elapsed


    # -------------------------------------------------------------------------
    # 2. Browser Human Pacing Hooks (Synchronous & Asynchronous)
    # -------------------------------------------------------------------------

    @classmethod
    def execute_browser_human_flow(
        cls,
        page: Any,
        target_url: str,
        do_warmup: bool = False,
        do_scroll: bool = True,
        max_scrolls: int = 3,
        allow_backtrack: bool = True,
        logger: LogEngine | None = None,
    ) -> dict[str, Any]:
        """
        Executes complete physical human browsing sequence on a synchronous Playwright page:
        warmup feed exploration, variable scrolling, and reading dwell pauses.
        """
        t0 = time.perf_counter()
        interaction = HumanInteractionEngine()
        metrics: dict[str, Any] = {
            "human_mode_active": True,
            "target_url": target_url,
            "warmup_executed": False,
            "scroll_executed": False,
        }

        if do_warmup:
            if logger:
                logger.info("[HUMAN-MODE] Executing pre-scrape browsing session warmup...")
            warmup_res = interaction.warmup_browsing_session(page, target_domain=target_url, duration_sec=4.0)
            metrics["warmup_executed"] = True
            metrics["warmup_metrics"] = warmup_res

        # Check if navigation is needed
        try:
            cur_url = page.url
            if not cur_url or cur_url == "about:blank":
                if logger:
                    logger.info(f"[HUMAN-MODE] Navigating to {target_url}...")
                page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass

        if do_scroll:
            if logger:
                logger.info("[HUMAN-MODE] Executing variable human scrolling with backtracking...")
            scroll_res = interaction.scroll_page_human(
                page,
                max_scrolls=max_scrolls,
                allow_backtrack=allow_backtrack,
                reading_pause_words=20,
            )
            metrics["scroll_executed"] = True
            metrics["scroll_metrics"] = scroll_res

        elapsed = time.perf_counter() - t0
        metrics["elapsed_time_sec"] = round(elapsed, 4)
        if logger:
            logger.info(f"[HUMAN-MODE] Browser human interaction flow completed in {elapsed:.3f}s")
        return metrics

    @classmethod
    async def async_execute_browser_human_flow(
        cls,
        page: Any,
        target_url: str,
        do_warmup: bool = False,
        do_scroll: bool = True,
        max_scrolls: int = 3,
        allow_backtrack: bool = True,
        logger: LogEngine | None = None,
    ) -> dict[str, Any]:
        """
        Executes complete physical human browsing sequence on an asynchronous Playwright page:
        warmup feed exploration, variable scrolling, and reading dwell pauses.
        """
        t0 = time.perf_counter()
        interaction = HumanInteractionEngine()
        metrics: dict[str, Any] = {
            "human_mode_active": True,
            "target_url": target_url,
            "warmup_executed": False,
            "scroll_executed": False,
        }

        if do_warmup:
            if logger:
                logger.info("[HUMAN-MODE] Executing async pre-scrape browsing session warmup...")
            warmup_res = await interaction.async_warmup_browsing_session(page, target_domain=target_url, duration_sec=4.0)
            metrics["warmup_executed"] = True
            metrics["warmup_metrics"] = warmup_res

        # Check if navigation is needed
        try:
            cur_url = page.url
            if not cur_url or cur_url == "about:blank":
                if logger:
                    logger.info(f"[HUMAN-MODE] Navigating to {target_url}...")
                await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass

        if do_scroll:
            if logger:
                logger.info("[HUMAN-MODE] Executing async variable human scrolling with backtracking...")
            scroll_res = await interaction.async_scroll_page_human(
                page,
                max_scrolls=max_scrolls,
                allow_backtrack=allow_backtrack,
                reading_pause_words=20,
            )
            metrics["scroll_executed"] = True
            metrics["scroll_metrics"] = scroll_res

        elapsed = time.perf_counter() - t0
        metrics["elapsed_time_sec"] = round(elapsed, 4)
        if logger:
            logger.info(f"[HUMAN-MODE] Async browser human interaction flow completed in {elapsed:.3f}s")
        return metrics
