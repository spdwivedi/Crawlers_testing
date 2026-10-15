"""
core/logger_engine.py
=====================
Simultaneous 4-Tier Structured Logger — Rule 2.

Writes JSONL events to ALL four log tiers simultaneously:
  Tier 1: data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl
  Tier 2: tools/<tool_id>/logs/tool_ops.jsonl
  Tier 3: logs/stages/stage_<N>_<name>.jsonl
  Tier 4: logs/global/antigravity_prompt_log.jsonl + .md

JSONL record schema:
  {
    "timestamp": "ISO8601",
    "level": "INFO|WARN|ERROR|DEBUG",
    "stage": str,
    "step": str,
    "tool_id": str,
    "action_name": str,
    "run_id": str,
    "message": str,
    "elapsed_ms": int,
    "progress_pct": int
  }
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_LOG_DIR = ROOT / "logs" / "global"
STAGES_LOG_DIR = ROOT / "logs" / "stages"

Level = Literal["DEBUG", "INFO", "WARN", "ERROR"]


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, record: dict) -> None:
    _ensure_dir(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _append_md_table_row(path: Path, record: dict) -> None:
    """Append a markdown table row to the global .md log."""
    _ensure_dir(path)
    ts = record.get("timestamp", "")[:19].replace("T", " ")
    level = record.get("level", "INFO")
    stage = record.get("stage", "")
    tool = record.get("tool_id", "")
    action = record.get("action_name", "")
    msg = record.get("message", "")
    pct = record.get("progress_pct", 0)

    # Write header if file is new/empty
    if not path.exists() or path.stat().st_size == 0:
        path.write_text(
            "# Antigravity Prompt Execution Log\n\n"
            "| Timestamp (UTC) | Level | Stage | Tool | Action | Progress | Message |\n"
            "|-----------------|-------|-------|------|--------|----------|---------|\n",
            encoding="utf-8",
        )

    with path.open("a", encoding="utf-8") as f:
        f.write(f"| {ts} | {level} | {stage} | {tool} | {action} | {pct}% | {msg} |\n")


class LogRecord:
    """Build a structured log record."""

    def __init__(
        self,
        level: Level,
        message: str,
        stage: str = "",
        step: str = "",
        tool_id: str = "",
        action_name: str = "",
        run_id: str = "",
        elapsed_ms: int = 0,
        progress_pct: int = 0,
        extra: dict | None = None,
    ) -> None:
        self.data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "stage": stage,
            "step": step,
            "tool_id": tool_id,
            "action_name": action_name,
            "run_id": run_id,
            "message": message,
            "elapsed_ms": elapsed_ms,
            "progress_pct": progress_pct,
        }
        if extra:
            self.data.update(extra)


class LogEngine:
    """
    Full 4-tier logger. One instance per action run.

    Usage:
        engine = LogEngine(
            tool_id="01_curl_cffi",
            action_name="scrape_for_leetcode",
            run_id="run_143012_ab12cd34",
            run_log_path=Path("data/.../logs/action_run.jsonl"),
            stage="Stage 1",
            step="Step 1.0",
        )
        engine.info("Parsing HTML", progress_pct=50)
    """

    def __init__(
        self,
        tool_id: str,
        action_name: str = "",
        run_id: str = "",
        run_log_path: Path | None = None,
        stage: str = "",
        step: str = "",
        stage_log_name: str = "stage_1_scaffolding",
    ) -> None:
        self.tool_id = tool_id
        self.action_name = action_name
        self.run_id = run_id
        self.stage = stage
        self.step = step
        self._start = time.monotonic()

        # Tier paths
        self._action_log: Path | None = run_log_path
        self._tool_log = (ROOT / "tools" / tool_id / "logs" / "tool_ops.jsonl") if tool_id else None
        self._stage_log = STAGES_LOG_DIR / f"{stage_log_name}.jsonl"
        self._global_jsonl = GLOBAL_LOG_DIR / "antigravity_prompt_log.jsonl"
        self._global_md = GLOBAL_LOG_DIR / "antigravity_prompt_log.md"

    def _elapsed_ms(self) -> int:
        return int((time.monotonic() - self._start) * 1000)

    def _write(self, level: Level, message: str, progress_pct: int = 0, extra: dict | None = None) -> None:
        rec = LogRecord(
            level=level,
            message=message,
            stage=self.stage,
            step=self.step,
            tool_id=self.tool_id,
            action_name=self.action_name,
            run_id=self.run_id,
            elapsed_ms=self._elapsed_ms(),
            progress_pct=progress_pct,
            extra=extra,
        )

        # Tier 1 — Action run log
        if self._action_log:
            _append_jsonl(self._action_log, rec.data)

        # Tier 2 — Tool ops log
        if self.tool_id and self._tool_log:
            _append_jsonl(self._tool_log, rec.data)

        # Tier 3 — Stage log
        _append_jsonl(self._stage_log, rec.data)

        # Tier 4 — Global logs
        _append_jsonl(self._global_jsonl, rec.data)
        _append_md_table_row(self._global_md, rec.data)

    def debug(self, message: str, progress_pct: int = 0, **extra) -> None:
        self._write("DEBUG", message, progress_pct, extra or None)

    def info(self, message: str, progress_pct: int = 0, **extra) -> None:
        self._write("INFO", message, progress_pct, extra or None)

    def warn(self, message: str, progress_pct: int = 0, **extra) -> None:
        self._write("WARN", message, progress_pct, extra or None)

    def error(self, message: str, progress_pct: int = 0, **extra) -> None:
        self._write("ERROR", message, progress_pct, extra or None)


class ToolLogger:
    """
    Simplified logger for use inside adapter stubs (no action run log).
    Writes to tool_ops.jsonl, stage log, and global logs.
    """

    def __init__(self, tool_id: str, stage: str = "", step: str = "") -> None:
        self._engine = LogEngine(
            tool_id=tool_id,
            stage=stage,
            step=step,
            run_log_path=None,
        )

    def info(self, message: str, **kwargs) -> None:
        extra = {k: v for k, v in kwargs.items() if k != "progress_pct"}
        self._engine.info(message, kwargs.get("progress_pct", 0), **extra)

    def warn(self, message: str, **kwargs) -> None:
        self._engine.warn(message, kwargs.get("progress_pct", 0))

    def error(self, message: str, **kwargs) -> None:
        self._engine.error(message, kwargs.get("progress_pct", 0))


def log_global(
    message: str,
    level: Level = "INFO",
    stage: str = "",
    step: str = "",
    tool_id: str = "",
    action_name: str = "",
    run_id: str = "",
    progress_pct: int = 0,
    stage_log_name: str = "stage_1_scaffolding",
) -> None:
    """
    Standalone function for quick global logging (no full engine instance needed).
    Used by git_manager.py and verify scripts.
    """
    engine = LogEngine(
        tool_id=tool_id,
        action_name=action_name,
        run_id=run_id,
        stage=stage,
        step=step,
        stage_log_name=stage_log_name,
    )
    engine._write(level, message, progress_pct)
