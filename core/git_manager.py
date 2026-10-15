"""
core/git_manager.py
===================
Atomic Git commit helper — Rule 4.

Provides helpers to:
  - Stage files (git add)
  - Create standardized commits with required prefixes
  - Return the latest commit hash
  - Log the commit into the Global Prompt Log (Tier 4)

Commit prefix convention:
  [SCAFFOLD]     — New structure, init, or directory creation
  [TOOL-INSTALL] — Installing or verifying a tool
  [UPDATE]       — Modifying existing code/config
  [FIX]          — Bug fix or error correction
  [RUN-LOG]      — After a tool run completes
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALID_PREFIXES = {"[SCAFFOLD]", "[TOOL-INSTALL]", "[UPDATE]", "[FIX]", "[RUN-LOG]"}


def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the project root."""
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def stage_all() -> None:
    """git add -A"""
    _run_git("add", "-A")


def stage_paths(*paths: str) -> None:
    """git add <paths>"""
    _run_git("add", *paths)


def get_latest_hash() -> str:
    """Return the latest short commit hash, or empty string if no commits."""
    result = _run_git("rev-parse", "--short", "HEAD")
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def commit(
    prefix: str,
    message: str,
    stage_all_files: bool = True,
    stage: str = "",
    step: str = "",
) -> str:
    """
    Create an atomic Git commit.

    Args:
        prefix:  Must be one of VALID_PREFIXES (e.g. "[SCAFFOLD]").
        message: Short commit message describing the change.
        stage_all_files: If True, runs git add -A before committing.
        stage: Current stage label (for log entry).
        step:  Current step label (for log entry).

    Returns:
        The resulting short commit hash.
    """
    if prefix not in VALID_PREFIXES:
        raise ValueError(
            f"Invalid prefix '{prefix}'. Must be one of: {sorted(VALID_PREFIXES)}"
        )

    if stage_all_files:
        stage_all()

    full_message = f"{prefix} {message}"
    result = _run_git("commit", "-m", full_message)

    commit_hash = get_latest_hash()

    # Tier 4 log — import here to avoid circular imports
    try:
        from core.logger_engine import log_global

        log_global(
            message=f"Git commit: {commit_hash} — {full_message}",
            level="INFO",
            stage=stage or "Stage 1",
            step=step or "Step 1.0",
            tool_id="",
            action_name="git_commit",
            run_id="",
            progress_pct=0,
        )
    except Exception:
        pass

    if result.returncode == 0:
        return commit_hash
    elif "nothing to commit" in result.stdout + result.stderr:
        return commit_hash
    else:
        raise RuntimeError(
            f"Git commit failed: {result.stderr.strip() or result.stdout.strip()}"
        )


def get_log(n: int = 10) -> list[dict]:
    """Return the last n git commits as list of dicts."""
    result = _run_git(
        "log", f"-{n}", "--pretty=format:%H|%h|%s|%ai|%an"
    )
    entries = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("|", 4)
        if len(parts) == 5:
            entries.append(
                {
                    "hash": parts[0],
                    "short_hash": parts[1],
                    "message": parts[2],
                    "date": parts[3],
                    "author": parts[4],
                }
            )
    return entries


def is_clean() -> bool:
    """Return True if the working tree has no uncommitted changes."""
    result = _run_git("status", "--porcelain")
    return result.stdout.strip() == ""
