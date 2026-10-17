"""
core/git_manager.py
===================
Atomic Git commit helper & Pre-Commit Secret Guard — Rule 4 & Rule 6.

Provides helpers to:
  - Stage files (git add)
  - Pre-commit secret scanning (scan_staged_for_secrets) to block credentials,
    .env, vault databases, and plaintext master keys from entering Git history.
  - Create standardized commits with required prefixes
  - Return the latest commit hash
  - Log the commit into the Global Prompt Log (Tier 4) & Stage Log (Tier 3)

Commit prefix convention:
  [SCAFFOLD]     — New structure, init, or directory creation
  [TOOL-INSTALL] — Installing or verifying a tool
  [UPDATE]       — Modifying existing code/config
  [FIX]          — Bug fix or error correction
  [RUN-LOG]      — After a tool run completes
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

VALID_PREFIXES = {"[SCAFFOLD]", "[TOOL-INSTALL]", "[UPDATE]", "[FIX]", "[RUN-LOG]"}

FORBIDDEN_FILE_PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"(^|/)vault_store/.*\.sqlite.*$", re.IGNORECASE),
    re.compile(r"(^|/)vault_store/.*\.db.*$", re.IGNORECASE),
    re.compile(r"(^|/)vault_store/temp_cookies/.*$", re.IGNORECASE),
    re.compile(r"(^|/)auth_profiles/.*(?<!README_AUTH\.md)$", re.IGNORECASE),
    re.compile(r".*\.(pem|key)$", re.IGNORECASE),
    re.compile(r"(^|/)(secrets|credentials)\.json$", re.IGNORECASE),
]

SAFE_EXCEPTIONS = [
    "vault_store/.gitkeep",
    "vault_store/README_VAULT.md",
    "vault_store/vault_stats_public.json",
    "auth_profiles/README_AUTH.md",
    ".env.example",
]


def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the project root with UTF-8 encoding."""
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def scan_staged_for_secrets(stage: str = "Stage 3", step: str = "Step 3.1") -> dict[str, Any]:
    """
    Pre-commit secret guard: scans all staged files for forbidden paths
    and staged diffs for the live VAULT_MASTER_KEY.
    
    If violations are detected, automatically unstages the offending files
    (git reset HEAD <path>) and logs a [SECURITY-GUARD] warning.
    
    Returns:
        {
            "violations_found": bool,
            "unstaged_files": list[str],
            "blocked_secrets_count": int,
            "details": list[str]
        }
    """
    res = _run_git("diff", "--cached", "--name-only")
    staged_files = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]

    unstaged: list[str] = []
    details: list[str] = []

    # 1. Path-based pattern checking
    for path in staged_files:
        # Check safe exceptions first
        if any(path.endswith(exc) or path == exc for exc in SAFE_EXCEPTIONS):
            continue

        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.search(path):
                # Unstage this forbidden file immediately
                _run_git("reset", "HEAD", "--", path)
                unstaged.append(path)
                msg = f"Blocked forbidden sensitive file: {path} (matched pattern: {pattern.pattern})"
                details.append(msg)
                _log_security_guard(msg, stage=stage, step=step)
                break

    # 2. Content diff scanning for live master key leak
    master_key = os.getenv("VAULT_MASTER_KEY")
    if not master_key and (ROOT / ".env").exists():
        try:
            for env_line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
                if env_line.startswith("VAULT_MASTER_KEY="):
                    master_key = env_line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass

    if master_key and len(master_key) >= 16:
        # Check diff of remaining staged files
        diff_res = _run_git("diff", "--cached")
        diff_out = diff_res.stdout or ""
        if master_key in diff_out:
            # Locate which file leaks the master key
            for path in staged_files:
                if path in unstaged or path in SAFE_EXCEPTIONS:
                    continue
                file_diff = _run_git("diff", "--cached", "--", path)
                file_out = file_diff.stdout or ""
                if master_key in file_out:
                    _run_git("reset", "HEAD", "--", path)
                    unstaged.append(path)
                    msg = f"Blocked file leaking live VAULT_MASTER_KEY: {path}"
                    details.append(msg)
                    _log_security_guard(msg, stage=stage, step=step)

    return {
        "violations_found": len(unstaged) > 0,
        "unstaged_files": unstaged,
        "blocked_secrets_count": len(unstaged),
        "details": details,
    }


def _log_security_guard(detail: str, stage: str = "Stage 3", step: str = "Step 3.1") -> None:
    """Log a security guard intervention to Tier 3 and Tier 4."""
    try:
        from core.logger_engine import log_global

        log_global(
            message=f"[SECURITY-GUARD] {detail}",
            level="WARN",
            stage=stage,
            step=step,
            tool_id="crypto_engine",
            action_name="secret_guard_intercept",
            run_id="",
            progress_pct=0,
            stage_log_name="stage_3_credential_vault",
        )
    except Exception:
        pass


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
    Create an atomic Git commit with pre-commit secret scanning.

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

    # Pre-commit secret scanning guard (Rule 6)
    guard_result = scan_staged_for_secrets(stage=stage or "Stage 3", step=step or "Step 3.1")
    if guard_result["violations_found"]:
        # Offending files were automatically unstaged
        pass

    full_message = f"{prefix} {message}"
    result = _run_git("commit", "-m", full_message)

    commit_hash = get_latest_hash()

    # Tier 4 log — import here to avoid circular imports
    try:
        from core.logger_engine import log_global

        log_global(
            message=f"Git commit: {commit_hash} — {full_message}",
            level="INFO",
            stage=stage or "Stage 3",
            step=step or "Step 3.1",
            tool_id="",
            action_name="git_commit",
            run_id="",
            progress_pct=0,
            stage_log_name="stage_3_credential_vault",
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
