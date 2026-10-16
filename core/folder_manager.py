"""
core/folder_manager.py
======================
Action/Date/Run folder factory.

Creates isolated output directories following Rule 3:
  data/<tool_id>/<action_name>/<YYYY-MM-DD>/run_<HHMMSS>_<short_uuid>/
    ├── raw/
    ├── cleaned/
    └── logs/
        └── action_run.jsonl

Also initializes run_manifest.json with full metadata.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Project Root ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _short_uuid(length: int = 8) -> str:
    return uuid.uuid4().hex[:length]


def create_action_run(
    tool_id: str,
    action_name: str,
    target_url: str = "",
) -> dict:
    """
    Create a complete isolated run directory for a tool action.

    Returns a dict with all run metadata (run_info), including the absolute
    path to the run root so callers can write their outputs.

    Directory structure created:
        data/<tool_id>/<action_name>/<YYYY-MM-DD>/run_<HHMMSS>_<uuid8>/
            raw/
            cleaned/
            logs/
                action_run.jsonl
            run_manifest.json
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    short_id = _short_uuid()
    run_id = f"run_{time_str}_{short_id}"

    run_dir = DATA_DIR / tool_id / action_name / date_str / run_id
    raw_dir = run_dir / "raw"
    cleaned_dir = run_dir / "cleaned"
    logs_dir = run_dir / "logs"

    # Create all directories
    for d in (raw_dir, cleaned_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Initialize action_run.jsonl
    log_file = logs_dir / "action_run.jsonl"
    _append_jsonl(
        log_file,
        {
            "event": "run_created",
            "run_id": run_id,
            "tool_id": tool_id,
            "action_name": action_name,
            "target_url": target_url,
            "timestamp": now.isoformat(),
        },
    )

    # Build run_manifest
    manifest = {
        "run_id": run_id,
        "tool_id": tool_id,
        "action_name": action_name,
        "date": date_str,
        "target_url": target_url,
        "started_at": now.isoformat(),
        "ended_at": None,
        "elapsed_sec": None,
        "status": "running",
        "raw_files": [],
        "cleaned_files": [],
        "git_commit": None,
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    run_info = {
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
    return run_info


def complete_action_run(
    run_info: dict | None = None,
    status: str = "completed",
    git_commit: str | None = None,
    records_extracted: int | None = None,
    quality_score: float | None = None,
    error_msg: str | None = None,
    **kwargs,
) -> dict:
    """
    Finalize a run: update run_manifest.json with end time, elapsed, file lists,
    and status. Call after the tool action finishes (success or failure).
    """
    manifest_path_val = None
    if isinstance(run_info, dict):
        manifest_path_val = run_info.get("manifest_path")
    elif "manifest_path" in kwargs:
        manifest_path_val = kwargs["manifest_path"]

    if not manifest_path_val:
        run_dir_val = run_info.get("run_dir") if isinstance(run_info, dict) else kwargs.get("run_dir")
        if run_dir_val:
            manifest_path_val = str(Path(run_dir_val) / "run_manifest.json")

    if not manifest_path_val:
        return {}

    manifest_path = Path(manifest_path_val)
    if not manifest_path.exists():
        return {}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    started = datetime.fromisoformat(manifest["started_at"])
    elapsed = round((now - started).total_seconds(), 3)

    run_dir = manifest_path.parent
    raw_files = [f.name for f in (run_dir / "raw").iterdir() if f.is_file()] if (run_dir / "raw").exists() else []
    cleaned_files = [f.name for f in (run_dir / "cleaned").iterdir() if f.is_file()] if (run_dir / "cleaned").exists() else []

    manifest.update(
        {
            "ended_at": now.isoformat(),
            "elapsed_sec": elapsed,
            "status": status,
            "raw_files": raw_files,
            "cleaned_files": cleaned_files,
            "git_commit": git_commit or manifest.get("git_commit"),
        }
    )
    if records_extracted is not None:
        manifest["records_extracted"] = records_extracted
    if quality_score is not None:
        manifest["quality_score"] = quality_score
    if error_msg is not None:
        manifest["error"] = error_msg

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Rule 5: Auto-Indexing into index_store/tool_indexes/<tool_id>.sqlite & <tool_id>_index.json
    try:
        tool_id = manifest.get("tool_id")
        if tool_id:
            import importlib
            from core.base_indexer import BaseToolIndexer
            indexer_cls = BaseToolIndexer
            try:
                mod = importlib.import_module(f"tools.{tool_id}.indexer")
                indexer_cls = getattr(mod, "ToolIndexer", BaseToolIndexer)
            except Exception:
                pass
            indexer = indexer_cls(tool_id)
            indexer.index_single_run(run_dir)
    except Exception:
        pass

    return manifest


def _append_jsonl(path: Path, record: dict) -> None:
    """Append a JSON record as a single line to a .jsonl file."""
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
