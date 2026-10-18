"""
core/human_timing.py
====================
Human Timing, Jitter & Pacing Engine — Stage 4 / Rule 7.

Provides statistical distributions (Gaussian, Log-Normal, Exponential Backoff Jitter),
contextual action calculators (keystrokes, reading pauses, video/audio stream chunk pacing,
and session burst delays), and pre-configured timing profiles (FAST_AUTOMATED, BALANCED_HUMAN,
STEALTH_PARANOID, STREAM_PACED).
"""

from __future__ import annotations

import math
import random
import time
from enum import Enum
from typing import Any, Union


class TimingProfile(str, Enum):
    """Canonical timing profiles for scraping operations."""
    FAST_AUTOMATED = "FAST_AUTOMATED"
    BALANCED_HUMAN = "BALANCED_HUMAN"
    STEALTH_PARANOID = "STEALTH_PARANOID"
    STREAM_PACED = "STREAM_PACED"


class HumanTimingEngine:
    """
    Simulates authentic human interaction latency, eye-tracking comprehension pauses,
    and adaptive rate-limiting evasion.
    """

    def __init__(self, default_profile: TimingProfile | str = TimingProfile.BALANCED_HUMAN) -> None:
        if isinstance(default_profile, str):
            default_profile = TimingProfile(default_profile.upper())
        self.default_profile = default_profile
        self.last_delay: float = 0.0

    # -------------------------------------------------------------------------
    # 1. Statistical Distribution Generators
    # -------------------------------------------------------------------------

    @staticmethod
    def gaussian_delay(
        mean: float,
        std_dev: float,
        min_val: float = 0.5,
        max_val: float = 15.0,
    ) -> float:
        """
        Generate a Gaussian (normal) delay clamped strictly between min_val and max_val.
        """
        val = random.gauss(mean, std_dev)
        return max(min_val, min(max_val, val))

    @staticmethod
    def log_normal_delay(
        median: float,
        sigma: float = 0.5,
        min_val: float = 0.2,
        max_val: float = 20.0,
    ) -> float:
        """
        Generate a log-normal delay with given median and shape parameter sigma.
        Clamped strictly between min_val and max_val.
        
        Log-normal distributions naturally model human response and dwell times,
        featuring a strong mode with a long right tail (rare long pauses).
        """
        mu = math.log(max(1e-6, median))
        val = random.lognormvariate(mu, sigma)
        return max(min_val, min(max_val, val))

    @staticmethod
    def exponential_backoff_jitter(
        base: float = 1.0,
        attempt: int = 1,
        max_delay: float = 60.0,
        jitter_ratio: float = 0.5,
    ) -> float:
        """
        Calculate exponential backoff delay with decorrelated / full jitter.
        
        temp = min(max_delay, base * (2 ** attempt))
        returns uniform sample from [temp * (1 - jitter_ratio), temp * (1 + jitter_ratio)].
        """
        temp = min(max_delay, base * (2 ** max(0, attempt)))
        low = max(0.01, temp * (1.0 - jitter_ratio))
        high = max(low + 0.01, temp * (1.0 + jitter_ratio))
        return random.uniform(low, high)

    # -------------------------------------------------------------------------
    # 2. Contextual Action Delay Calculators
    # -------------------------------------------------------------------------

    @staticmethod
    def keystroke_delay(wpm_target: int = 65) -> float:
        """
        Computes inter-keystroke intervals (typically 60ms–180ms) with occasional
        300ms–600ms word-boundary pauses.
        """
        # Standard assumption: 5 characters per word
        chars_per_min = max(10, wpm_target * 5)
        base_interval = 60.0 / chars_per_min  # e.g., 60 / 325 ~= 0.1846s

        # 18% chance of word boundary or cognitive pause
        if random.random() < 0.18:
            return random.uniform(0.300, 0.600)

        # Standard typing keystroke interval with Gaussian jitter (~25% variance)
        jittered = random.gauss(base_interval, base_interval * 0.25)
        return max(0.050, min(0.350, jittered))

    @staticmethod
    def reading_pause(word_count: int = 100, reading_wpm: int = 220) -> float:
        """
        Computes realistic human reading dwell times based on text length,
        adding 20% random Gaussian variance and eye-scan hesitation pauses.
        """
        safe_words = max(1, word_count)
        base_time = (safe_words / max(50, reading_wpm)) * 60.0
        dwell = random.gauss(base_time, base_time * 0.20)

        # Saccade / hesitation pauses for longer sections
        if safe_words > 40:
            dwell += random.uniform(0.5, 2.5)

        return max(0.5, dwell)

    @staticmethod
    def chunk_download_pacing(chunk_duration_sec: float = 3.0, playback_rate: float = 1.0) -> float:
        """
        Computes inter-chunk download delays for video/audio streams (yt-dlp / HLS .ts parts),
        simulating buffer filling without triggering CDN stream flooding blocks.
        """
        target_delay = chunk_duration_sec / max(0.1, playback_rate)
        # Players fetch chunks slightly faster than real-time playback to buffer safely
        pacing = random.uniform(target_delay * 0.40, target_delay * 0.90)
        return max(0.2, pacing)

    @staticmethod
    def session_burst_delay(action_count_in_burst: int = 3) -> float:
        """
        Simulates quick multi-click bursts (0.4s–1.2s between rapid actions)
        followed by longer comprehension pauses (4s–12s).
        """
        if action_count_in_burst < 3:
            # Rapid micro-burst actions (e.g. clicking form fields, tab switching)
            return random.uniform(0.40, 1.20)
        else:
            # End of burst: user reviews content before initiating next sequence
            return random.uniform(4.0, 12.0)

    # -------------------------------------------------------------------------
    # 3. Pre-Configured Timing Profiles & Execution
    # -------------------------------------------------------------------------

    def get_delay(
        self,
        profile: TimingProfile | str | None = None,
        action_type: str = "navigate",
        **kwargs: Any,
    ) -> float:
        """
        Calculate appropriate delay based on timing profile and action type.
        """
        p = profile or self.default_profile
        if isinstance(p, str):
            p = TimingProfile(p.upper())

        act = action_type.lower()

        # Context-specific action overrides
        if act in ("keystroke", "type", "typing"):
            wpm = kwargs.get("wpm_target", 65 if p != TimingProfile.FAST_AUTOMATED else 150)
            return self.keystroke_delay(wpm_target=wpm)

        if act in ("read", "reading", "dwell"):
            words = kwargs.get("word_count", 100)
            return self.reading_pause(word_count=words)

        if act in ("chunk", "stream", "media") or p == TimingProfile.STREAM_PACED:
            chunk_sec = kwargs.get("chunk_duration_sec", 3.0)
            rate = kwargs.get("playback_rate", 1.0)
            return self.chunk_download_pacing(chunk_duration_sec=chunk_sec, playback_rate=rate)

        if act in ("burst", "click_burst"):
            cnt = kwargs.get("action_count_in_burst", 1)
            return self.session_burst_delay(action_count_in_burst=cnt)

        # Profile-based general navigation and interaction delays
        if p == TimingProfile.FAST_AUTOMATED:
            return random.uniform(0.10, 0.50)

        elif p == TimingProfile.BALANCED_HUMAN:
            if act == "click":
                return self.gaussian_delay(mean=1.5, std_dev=0.4, min_val=0.8, max_val=3.0)
            elif act == "scroll":
                return self.gaussian_delay(mean=1.0, std_dev=0.3, min_val=0.4, max_val=2.2)
            else:  # navigate, paginate, default
                return self.log_normal_delay(median=2.2, sigma=0.45, min_val=1.2, max_val=4.5)

        elif p == TimingProfile.STEALTH_PARANOID:
            # 8% chance of deep cognitive pause (simulating user reading or tab switching)
            if random.random() < 0.08:
                return self.gaussian_delay(mean=18.0, std_dev=2.5, min_val=15.0, max_val=25.0)

            if act == "click":
                return self.gaussian_delay(mean=4.0, std_dev=1.0, min_val=2.5, max_val=8.0)
            elif act == "scroll":
                return self.gaussian_delay(mean=2.5, std_dev=0.7, min_val=1.5, max_val=5.0)
            else:  # navigate
                return self.log_normal_delay(median=6.0, sigma=0.5, min_val=3.5, max_val=12.0)

        # Fallback
        return self.log_normal_delay(median=2.0, sigma=0.4, min_val=1.0, max_val=4.0)

    def sleep(
        self,
        profile: TimingProfile | str | None = None,
        action_type: str = "navigate",
        target_delay: float | None = None,
        **kwargs: Any,
    ) -> float:
        """
        Calculate delay, execute time.sleep(), and return actual wall-clock elapsed time.
        Stores the chosen delay in self.last_delay.
        """
        if target_delay is not None:
            delay = target_delay
        else:
            delay = self.get_delay(profile=profile, action_type=action_type, **kwargs)
        self.last_delay = delay
        t0 = time.perf_counter()
        time.sleep(delay)
        return time.perf_counter() - t0
