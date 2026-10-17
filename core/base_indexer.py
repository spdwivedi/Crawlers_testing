"""
core/base_indexer.py
====================
Base Tool Indexing Engine for Crawlers_testing — Rule 5.

Provides BaseToolIndexer, which indexes runs, artifacts, file manifests,
and 4-tier logs for a tool into:
  1. Dedicated SQLite DB: index_store/tool_indexes/<tool_id>.sqlite
  2. Companion JSON snapshot: index_store/tool_indexes/<tool_id>_index.json

Each of the 20 crawler/extractor tools subclasses BaseToolIndexer and overrides
extract_domain_metrics() to parse tool-specific KPIs and analytical metadata.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

INDEX_STORE_DIR = ROOT / "index_store"
TOOL_INDEXES_DIR = INDEX_STORE_DIR / "tool_indexes"
REGISTRY_PATH = ROOT / "tools" / "registry.json"


def _sha256_short(path: Path) -> str:
    """Return the first 16 characters of SHA-256 for a file."""
    if not path.is_file():
        return ""
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return ""


def _get_content_preview(path: Path, max_chars: int = 2000) -> str:
    """Return text preview for textual files or binary placeholder."""
    if not path.is_file():
        return ""
    suffix = path.suffix.lower()
    text_exts = {".json", ".jsonl", ".md", ".txt", ".csv", ".html", ".htm", ".xml", ".srt", ".py", ".yaml", ".yml"}
    if suffix in text_exts:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            clean = " ".join(content.split())
            return clean[:max_chars]
        except Exception:
            return ""
    size = path.stat().st_size if path.exists() else 0
    return f"<{suffix[1:].upper() if suffix else 'BINARY'} file, size: {size} bytes>"


class BaseToolIndexer:
    """Base class for per-tool SQLite and JSON indexing."""

    def __init__(self, tool_id: str):
        self.tool_id = tool_id
        self.db_path = TOOL_INDEXES_DIR / f"{tool_id}.sqlite"
        self.json_path = TOOL_INDEXES_DIR / f"{tool_id}_index.json"
        self.data_dir = ROOT / "data" / tool_id
        self.tool_dir = ROOT / "tools" / tool_id

        TOOL_INDEXES_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Create SQLite schema if not already initialized."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tool_metadata (
                    tool_id TEXT PRIMARY KEY,
                    name TEXT,
                    batch INTEGER,
                    mechanism_type TEXT,
                    total_runs INTEGER DEFAULT 0,
                    total_actions INTEGER DEFAULT 0,
                    total_raw_files INTEGER DEFAULT 0,
                    total_cleaned_files INTEGER DEFAULT 0,
                    total_log_entries INTEGER DEFAULT 0,
                    last_indexed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS indexed_runs (
                    run_id TEXT PRIMARY KEY,
                    tool_id TEXT,
                    action_name TEXT,
                    run_date TEXT,
                    target_url TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    elapsed_sec REAL,
                    status TEXT,
                    git_commit TEXT,
                    raw_file_count INTEGER,
                    cleaned_file_count INTEGER,
                    raw_total_bytes INTEGER,
                    cleaned_total_bytes INTEGER,
                    domain_metrics_json TEXT,
                    cleaned_text_preview TEXT,
                    run_dir_relpath TEXT
                );

                CREATE TABLE IF NOT EXISTS indexed_files (
                    file_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    tool_id TEXT,
                    action_name TEXT,
                    run_date TEXT,
                    tier TEXT,
                    filename TEXT,
                    extension TEXT,
                    size_bytes INTEGER,
                    sha256_short TEXT,
                    relpath TEXT,
                    content_preview TEXT
                );

                CREATE TABLE IF NOT EXISTS indexed_logs (
                    log_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    tool_id TEXT,
                    action_name TEXT,
                    run_date TEXT,
                    log_tier TEXT,
                    timestamp TEXT,
                    level TEXT,
                    stage TEXT,
                    step TEXT,
                    progress_pct INTEGER,
                    elapsed_ms INTEGER,
                    message TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_runs_tool_action ON indexed_runs(tool_id, action_name);
                CREATE INDEX IF NOT EXISTS idx_files_run_id ON indexed_files(run_id);
                CREATE INDEX IF NOT EXISTS idx_logs_run_id ON indexed_logs(run_id);
            """)

            # Populate initial tool metadata if missing
            row = conn.execute("SELECT tool_id FROM tool_metadata WHERE tool_id = ?", (self.tool_id,)).fetchone()
            if not row:
                name = self.tool_id
                batch = 1
                mech = "General"
                if REGISTRY_PATH.exists():
                    try:
                        reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
                        for t in reg.get("tools", []):
                            if t.get("tool_id") == self.tool_id:
                                name = t.get("name", self.tool_id)
                                batch = t.get("batch", 1)
                                mech = t.get("mechanism_type", "General")
                                break
                    except Exception:
                        pass

                conn.execute(
                    """
                    INSERT OR REPLACE INTO tool_metadata 
                    (tool_id, name, batch, mechanism_type, last_indexed_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.tool_id, name, batch, mech, datetime.now(timezone.utc).isoformat()),
                )

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        """
        Extract tool-specific domain metrics from raw and cleaned files.
        Subclasses should override this method!
        """
        metrics = {
            "default_metric": "ok",
            "raw_files": [f.name for f in raw_dir.iterdir() if f.is_file()] if raw_dir.exists() else [],
            "cleaned_files": [f.name for f in cleaned_dir.iterdir() if f.is_file()] if cleaned_dir.exists() else [],
        }
        return metrics

    def index_single_run(self, run_dir: Path) -> dict[str, Any]:
        """Index or re-index a single run directory into the tool SQLite DB and JSON snapshot."""
        if not run_dir.exists() or not run_dir.is_dir():
            return {"status": "error", "message": f"Run dir does not exist: {run_dir}"}

        parts = run_dir.parts
        # data/<tool_id>/<action>/<date>/<run_id>
        run_id = run_dir.name
        run_date = parts[-2] if len(parts) >= 2 else ""
        action_name = parts[-3] if len(parts) >= 3 else ""

        raw_dir = run_dir / "raw"
        cleaned_dir = run_dir / "cleaned"
        logs_dir = run_dir / "logs"
        manifest_file = run_dir / "run_manifest.json"

        manifest_data = {}
        if manifest_file.exists():
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            except Exception:
                manifest_data = {}

        target_url = manifest_data.get("target_url", "")
        started_at = manifest_data.get("started_at", "")
        ended_at = manifest_data.get("completed_at", manifest_data.get("ended_at", ""))
        elapsed_sec = float(manifest_data.get("elapsed_seconds", 0.0))
        status = manifest_data.get("status", "unknown")
        git_commit = manifest_data.get("git_commit", "")

        raw_files = [f for f in raw_dir.iterdir() if f.is_file()] if raw_dir.exists() else []
        cleaned_files = [f for f in cleaned_dir.iterdir() if f.is_file()] if cleaned_dir.exists() else []

        raw_file_count = len(raw_files)
        cleaned_file_count = len(cleaned_files)
        raw_total_bytes = sum(f.stat().st_size for f in raw_files)
        cleaned_total_bytes = sum(f.stat().st_size for f in cleaned_files)

        # Domain metrics
        domain_metrics = self.extract_domain_metrics(run_dir, raw_dir, cleaned_dir)
        domain_metrics_json = json.dumps(domain_metrics, default=str)

        # Cleaned text preview for quick search
        cleaned_preview_parts = []
        for cf in cleaned_files:
            if cf.suffix.lower() in [".md", ".json", ".csv", ".txt", ".srt"]:
                prev = _get_content_preview(cf, max_chars=400)
                if prev:
                    cleaned_preview_parts.append(f"[{cf.name}]: {prev}")
        cleaned_text_preview = " | ".join(cleaned_preview_parts)[:2000]

        rel_run_dir = run_dir.relative_to(ROOT).as_posix()

        with self._get_connection() as conn:
            # 1. Insert or update indexed_runs
            conn.execute(
                """
                INSERT OR REPLACE INTO indexed_runs (
                    run_id, tool_id, action_name, run_date, target_url,
                    started_at, ended_at, elapsed_sec, status, git_commit,
                    raw_file_count, cleaned_file_count, raw_total_bytes, cleaned_total_bytes,
                    domain_metrics_json, cleaned_text_preview, run_dir_relpath
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, self.tool_id, action_name, run_date, target_url,
                    started_at, ended_at, elapsed_sec, status, git_commit,
                    raw_file_count, cleaned_file_count, raw_total_bytes, cleaned_total_bytes,
                    domain_metrics_json, cleaned_text_preview, rel_run_dir,
                ),
            )

            # 2. Index raw files
            for rf in raw_files:
                file_id = f"{run_id}_raw_{rf.name}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO indexed_files (
                        file_id, run_id, tool_id, action_name, run_date, tier,
                        filename, extension, size_bytes, sha256_short, relpath, content_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_id, run_id, self.tool_id, action_name, run_date, "raw",
                        rf.name, rf.suffix.lower(), rf.stat().st_size,
                        _sha256_short(rf), rf.relative_to(ROOT).as_posix(),
                        _get_content_preview(rf, max_chars=1500),
                    ),
                )

            # 3. Index cleaned files
            for cf in cleaned_files:
                file_id = f"{run_id}_cleaned_{cf.name}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO indexed_files (
                        file_id, run_id, tool_id, action_name, run_date, tier,
                        filename, extension, size_bytes, sha256_short, relpath, content_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_id, run_id, self.tool_id, action_name, run_date, "cleaned",
                        cf.name, cf.suffix.lower(), cf.stat().st_size,
                        _sha256_short(cf), cf.relative_to(ROOT).as_posix(),
                        _get_content_preview(cf, max_chars=1500),
                    ),
                )

            # 4. Index run logs
            action_log_path = logs_dir / "action_run.jsonl"
            if action_log_path.exists():
                try:
                    for idx, line in enumerate(action_log_path.read_text(encoding="utf-8").splitlines()):
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        log_id = f"{run_id}_act_{idx}"
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO indexed_logs (
                                log_id, run_id, tool_id, action_name, run_date, log_tier,
                                timestamp, level, stage, step, progress_pct, elapsed_ms, message
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                log_id, run_id, self.tool_id, action_name, run_date, "action_run",
                                rec.get("timestamp", ""), rec.get("level", "INFO"),
                                rec.get("stage", ""), rec.get("step", ""),
                                rec.get("progress_pct", 0), rec.get("elapsed_ms", 0),
                                rec.get("message", ""),
                            ),
                        )
                except Exception:
                    pass

            # Update aggregated tool metadata
            self._update_tool_metadata(conn)

        # Export JSON snapshot
        self._export_json_summary()

        return {
            "status": "indexed",
            "run_id": run_id,
            "tool_id": self.tool_id,
            "raw_files": raw_file_count,
            "cleaned_files": cleaned_file_count,
            "domain_metrics": domain_metrics,
        }

    def _update_tool_metadata(self, conn: sqlite3.Connection) -> None:
        """Update aggregate counts in tool_metadata."""
        total_runs = conn.execute("SELECT COUNT(*) FROM indexed_runs WHERE tool_id = ?", (self.tool_id,)).fetchone()[0]
        total_actions = conn.execute("SELECT COUNT(DISTINCT action_name) FROM indexed_runs WHERE tool_id = ?", (self.tool_id,)).fetchone()[0]
        total_raw = conn.execute("SELECT COUNT(*) FROM indexed_files WHERE tool_id = ? AND tier = 'raw'", (self.tool_id,)).fetchone()[0]
        total_cleaned = conn.execute("SELECT COUNT(*) FROM indexed_files WHERE tool_id = ? AND tier = 'cleaned'", (self.tool_id,)).fetchone()[0]
        total_logs = conn.execute("SELECT COUNT(*) FROM indexed_logs WHERE tool_id = ?", (self.tool_id,)).fetchone()[0]

        conn.execute(
            """
            UPDATE tool_metadata SET
                total_runs = ?,
                total_actions = ?,
                total_raw_files = ?,
                total_cleaned_files = ?,
                total_log_entries = ?,
                last_indexed_at = ?
            WHERE tool_id = ?
            """,
            (
                total_runs, total_actions, total_raw, total_cleaned, total_logs,
                datetime.now(timezone.utc).isoformat(), self.tool_id,
            ),
        )

    def _index_tool_ops_logs(self, conn: sqlite3.Connection) -> None:
        """Index tools/<tool_id>/logs/tool_ops.jsonl into indexed_logs."""
        tool_ops_path = self.tool_dir / "logs" / "tool_ops.jsonl"
        if tool_ops_path.exists():
            try:
                for idx, line in enumerate(tool_ops_path.read_text(encoding="utf-8").splitlines()):
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    log_id = f"{self.tool_id}_ops_{idx}"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO indexed_logs (
                            log_id, run_id, tool_id, action_name, run_date, log_tier,
                            timestamp, level, stage, step, progress_pct, elapsed_ms, message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            log_id, rec.get("run_id", "tool_ops"), self.tool_id,
                            rec.get("action_name", ""), "", "tool_ops",
                            rec.get("timestamp", ""), rec.get("level", "INFO"),
                            rec.get("stage", ""), rec.get("step", ""),
                            rec.get("progress_pct", 0), rec.get("elapsed_ms", 0),
                            rec.get("message", ""),
                        ),
                    )
            except Exception:
                pass

    def index_all_runs(self) -> dict[str, Any]:
        """Scan data/<tool_id> and index all existing runs and tool_ops logs."""
        runs_found = []
        if self.data_dir.exists():
            for action_dir in self.data_dir.iterdir():
                if action_dir.is_dir():
                    for date_dir in action_dir.iterdir():
                        if date_dir.is_dir():
                            for run_dir in date_dir.iterdir():
                                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                                    runs_found.append(run_dir)

        runs_found.sort(key=lambda d: d.name)
        for r_dir in runs_found:
            self.index_single_run(r_dir)

        # Index tool_ops logs
        with self._get_connection() as conn:
            self._index_tool_ops_logs(conn)
            self._update_tool_metadata(conn)

        self._export_json_summary()

        summary = self.get_summary()
        return {
            "tool_id": self.tool_id,
            "runs_indexed": len(runs_found),
            "summary": summary,
        }

    def _export_json_summary(self) -> None:
        """Export companion JSON snapshot (<tool_id>_index.json)."""
        summary_data = self.get_summary()
        self.json_path.write_text(json.dumps(summary_data, indent=2, default=str), encoding="utf-8")

    def get_summary(self) -> dict[str, Any]:
        """Retrieve complete structured summary dictionary for this tool index."""
        with self._get_connection() as conn:
            meta_row = conn.execute("SELECT * FROM tool_metadata WHERE tool_id = ?", (self.tool_id,)).fetchone()
            meta = dict(meta_row) if meta_row else {}

            runs_rows = conn.execute("SELECT * FROM indexed_runs WHERE tool_id = ? ORDER BY started_at DESC", (self.tool_id,)).fetchall()
            runs = []
            for r in runs_rows:
                rd = dict(r)
                if rd.get("domain_metrics_json"):
                    try:
                        rd["domain_metrics"] = json.loads(rd["domain_metrics_json"])
                    except Exception:
                        rd["domain_metrics"] = {}
                else:
                    rd["domain_metrics"] = {}
                runs.append(rd)

            files_rows = conn.execute("SELECT * FROM indexed_files WHERE tool_id = ? ORDER BY tier, filename", (self.tool_id,)).fetchall()
            files = [dict(f) for f in files_rows]

            recent_logs_rows = conn.execute("SELECT * FROM indexed_logs WHERE tool_id = ? ORDER BY timestamp DESC LIMIT 50", (self.tool_id,)).fetchall()
            recent_logs = [dict(l) for l in recent_logs_rows]

            return {
                "tool_id": self.tool_id,
                "metadata": meta,
                "total_runs": len(runs),
                "runs": runs,
                "total_files": len(files),
                "files_summary": {
                    "raw": [f for f in files if f.get("tier") == "raw"],
                    "cleaned": [f for f in files if f.get("tier") == "cleaned"],
                },
                "recent_logs": recent_logs,
                "indexed_at": meta.get("last_indexed_at", datetime.now(timezone.utc).isoformat()),
            }


def get_tool_indexer(tool_id: str) -> BaseToolIndexer:
    """Factory function returning the dedicated ToolIndexer for a tool, or BaseToolIndexer fallback."""
    import importlib
    indexer_cls = BaseToolIndexer
    try:
        mod = importlib.import_module(f"tools.{tool_id}.indexer")
        indexer_cls = getattr(mod, "ToolIndexer", BaseToolIndexer)
    except Exception:
        pass
    return indexer_cls(tool_id)

