"""
core/state_tracker.py
=====================
Live State Telemetry manager — Rule 1.

Manages logs/global/live_state.json which the frontend polls/streams via
WebSocket for the always-on HUD bar.

live_state.json schema:
{
  "is_running": bool,
  "current_stage": str,
  "current_step": str,
  "active_tool_id": str,
  "active_action": str,
  "current_subtask": str,
  "started_at_epoch": float | null,
  "elapsed_seconds": float,
  "progress_percent": int (0-100),
  "recent_events": [ ...last 10 events ],
  "worker_processes": [ ...psutil scan results ]
}
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "logs" / "global" / "live_state.json"

_INITIAL_STATE: dict[str, Any] = {
    "is_running": False,
    "current_stage": "",
    "current_step": "",
    "active_tool_id": "",
    "active_action": "",
    "current_subtask": "",
    "started_at_epoch": None,
    "elapsed_seconds": 0.0,
    "progress_percent": 0,
    "recent_events": [],
    "worker_processes": [],
}


def _ensure_state_file() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text(
            json.dumps(_INITIAL_STATE, indent=2), encoding="utf-8"
        )


def read_state() -> dict[str, Any]:
    _ensure_state_file()
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_INITIAL_STATE)


def write_state(state: dict[str, Any]) -> None:
    _ensure_state_file()
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def start_task(
    stage: str,
    step: str,
    tool_id: str = "",
    action: str = "",
    subtask: str = "",
) -> None:
    """Mark a new task as running. Resets timer and progress."""
    state = read_state()
    now = time.time()
    state.update(
        {
            "is_running": True,
            "current_stage": stage,
            "current_step": step,
            "active_tool_id": tool_id,
            "active_action": action,
            "current_subtask": subtask,
            "started_at_epoch": now,
            "elapsed_seconds": 0.0,
            "progress_percent": 0,
        }
    )
    _push_event(state, f"STARTED: {stage} / {step} — {subtask}")
    write_state(state)


def update_progress(
    progress_percent: int,
    subtask: str = "",
    tool_id: str | None = None,
    action: str | None = None,
) -> None:
    """Update progress percentage and optional subtask/tool context."""
    state = read_state()
    if state.get("started_at_epoch"):
        state["elapsed_seconds"] = round(
            time.time() - state["started_at_epoch"], 1
        )
    state["progress_percent"] = min(max(int(progress_percent), 0), 100)
    if subtask:
        state["current_subtask"] = subtask
    if tool_id is not None:
        state["active_tool_id"] = tool_id
    if action is not None:
        state["active_action"] = action
    if subtask:
        _push_event(state, f"PROGRESS {progress_percent}%: {subtask}")
    write_state(state)


def complete_task(message: str = "Task completed.") -> None:
    """Mark the current task as complete."""
    state = read_state()
    if state.get("started_at_epoch"):
        state["elapsed_seconds"] = round(
            time.time() - state["started_at_epoch"], 1
        )
    state["is_running"] = False
    state["progress_percent"] = 100
    _push_event(state, f"COMPLETED: {message}")
    write_state(state)


def fail_task(reason: str = "Task failed.") -> None:
    """Mark the current task as failed."""
    state = read_state()
    if state.get("started_at_epoch"):
        state["elapsed_seconds"] = round(
            time.time() - state["started_at_epoch"], 1
        )
    state["is_running"] = False
    _push_event(state, f"FAILED: {reason}")
    write_state(state)


def refresh_workers() -> list[dict]:
    """
    Scan for active Python/tool worker processes running inside the
    project root. Returns list of {pid, name, cmdline, cpu_pct, ram_mb, runtime_s}.
    Requires psutil.
    """
    if not _PSUTIL_OK:
        return []

    root_str = str(ROOT).lower()
    workers = []
    for proc in psutil.process_iter(
        ["pid", "name", "cmdline", "cpu_percent", "memory_info", "create_time"]
    ):
        try:
            info = proc.info
            cmdline = " ".join(info.get("cmdline") or []).lower()
            if root_str not in cmdline:
                continue
            ram_mb = round(
                (info.get("memory_info") or type("", (), {"rss": 0})()).rss / 1_048_576, 1
            )
            runtime_s = round(time.time() - (info.get("create_time") or time.time()), 1)
            workers.append(
                {
                    "pid": info["pid"],
                    "name": info.get("name", ""),
                    "cmdline": (info.get("cmdline") or [])[:6],
                    "cpu_pct": info.get("cpu_percent", 0.0),
                    "ram_mb": ram_mb,
                    "runtime_s": runtime_s,
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    state = read_state()
    state["worker_processes"] = workers
    if state.get("started_at_epoch"):
        state["elapsed_seconds"] = round(
            time.time() - state["started_at_epoch"], 1
        )
    write_state(state)
    return workers


def _push_event(state: dict, message: str) -> None:
    """Append to recent_events list capped at 10."""
    events: list = state.setdefault("recent_events", [])
    events.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
        }
    )
    state["recent_events"] = events[-10:]
