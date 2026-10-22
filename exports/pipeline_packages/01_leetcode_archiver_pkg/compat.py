"""
compat.py
=========
Standalone Compatibility Shim for Exported Scraper Package.
Eliminates all monorepo dependencies, allowing independent execution.
"""
import os
import sys
import time
import json
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

def create_action_run(tool_id: str, action_name: str, target_url: str = "") -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    h = hashlib.md5(f"{time.time()}_{random.random()}".encode()).hexdigest()[:8]
    run_id = f"run_{now.strftime('%H%M%S')}_{h}"
    run_dir = ROOT / "output" / action_name / date_str / run_id
    raw_dir = run_dir / "raw"
    cleaned_dir = run_dir / "cleaned"
    logs_dir = run_dir / "logs"
    log_file = logs_dir / "action_run.jsonl"
    manifest_path = run_dir / "run_manifest.json"

    raw_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file.touch(exist_ok=True)

    return {
        "run_id": run_id,
        "tool_id": tool_id,
        "action_name": action_name,
        "date": date_str,
        "target_url": target_url,
        "started_at": now.isoformat(),
        "run_dir": str(run_dir),
        "raw_dir": str(raw_dir),
        "cleaned_dir": str(cleaned_dir),
        "logs_dir": str(logs_dir),
        "log_file": str(log_file),
        "manifest_path": str(manifest_path),
    }

def complete_action_run(
    run_info: dict[str, Any],
    status: str = "completed",
    domain_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_dir = Path(run_info["run_dir"])
    manifest = {
        **run_info,
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "domain_metrics": domain_metrics or {},
    }
    manifest_file = run_dir / "run_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest

class LogEngine:
    def __init__(self, *args, **kwargs):
        pass
    def info(self, msg: str, *args, **kwargs):
        print(f"[INFO] {msg}")
    def warn(self, msg: str, *args, **kwargs):
        print(f"[WARN] {msg}")
    def error(self, msg: str, *args, **kwargs):
        print(f"[ERROR] {msg}")

def start_task(*args, **kwargs):
    pass

def update_progress(pct: int, subtask: str = "", *args, **kwargs):
    print(f"[PROGRESS {pct}%] {subtask}")

def complete_task(*args, **kwargs):
    pass

def fail_task(*args, **kwargs):
    pass

class HumanAdapterHelper:
    @staticmethod
    def apply_pre_action_delay(human_mode: bool, timing_profile: str, *args, **kwargs):
        if human_mode:
            time.sleep(random.uniform(0.1, 0.3))

    @staticmethod
    def apply_post_action_delay(human_mode: bool, timing_profile: str, *args, **kwargs):
        if human_mode:
            time.sleep(random.uniform(0.1, 0.3))
