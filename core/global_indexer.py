"""
core/global_indexer.py
======================
Global Master Indexing Engine for Crawlers_testing — Stage 2 Step 2.2.

Federates and unifies all 20 per-tool SQLite databases and all 4 log tiers into:
  1. index_store/global_master_index.sqlite (WAL mode + SQLite FTS5 Full-Text Search)
  2. index_store/global_master_index.json (Comprehensive Git-tracked summary snapshot)

Provides:
  - sync_all(rebuild_tools_first=False): Full federation of 20 tools + 4 log tiers
  - sync_single_tool(tool_id): Sub-100ms incremental sync for Rule 5 hook
  - FTS5 full-text search across all artifacts, files, and multi-tier logs
  - Multi-dimensional query helpers for REST API and Control Center frontend
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INDEX_STORE_DIR = ROOT / "index_store"
TOOL_INDEXES_DIR = INDEX_STORE_DIR / "tool_indexes"
GLOBAL_DB_PATH = INDEX_STORE_DIR / "global_master_index.sqlite"
GLOBAL_JSON_PATH = INDEX_STORE_DIR / "global_master_index.json"
REGISTRY_PATH = ROOT / "tools" / "registry.json"


def _make_log_id(log_tier: str, record: dict, source_file: str, idx: int) -> str:
    """Generate deterministic unique ID for a log line."""
    ts = record.get("timestamp", "")
    msg = record.get("message", "")
    raw = f"{log_tier}|{ts}|{msg}|{source_file}|{idx}"
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:24]


class GlobalMasterIndexer:
    """Global Master Indexer federating all 20 tools and all 4 log tiers with FTS5 search."""

    def __init__(self, db_path: Path = GLOBAL_DB_PATH, json_path: Path = GLOBAL_JSON_PATH):
        self.db_path = db_path
        self.json_path = json_path
        INDEX_STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Initialize global master schema and FTS5 virtual tables."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS global_tools (
                    tool_id TEXT PRIMARY KEY,
                    name TEXT,
                    batch INTEGER,
                    mechanism_type TEXT,
                    total_runs INTEGER DEFAULT 0,
                    total_actions INTEGER DEFAULT 0,
                    total_raw_files INTEGER DEFAULT 0,
                    total_cleaned_files INTEGER DEFAULT 0,
                    total_raw_bytes INTEGER DEFAULT 0,
                    total_cleaned_bytes INTEGER DEFAULT 0,
                    total_log_entries INTEGER DEFAULT 0,
                    latest_domain_metrics_json TEXT,
                    last_indexed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS global_runs (
                    run_id TEXT PRIMARY KEY,
                    tool_id TEXT,
                    batch INTEGER,
                    mechanism_type TEXT,
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

                CREATE TABLE IF NOT EXISTS global_files (
                    file_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    tool_id TEXT,
                    batch INTEGER,
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

                CREATE TABLE IF NOT EXISTS global_logs (
                    log_id TEXT PRIMARY KEY,
                    log_tier TEXT,
                    stage TEXT,
                    step TEXT,
                    tool_id TEXT,
                    action_name TEXT,
                    run_date TEXT,
                    run_id TEXT,
                    timestamp TEXT,
                    level TEXT,
                    progress_pct INTEGER,
                    elapsed_ms INTEGER,
                    message TEXT,
                    source_file TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_gruns_tool_action ON global_runs(tool_id, action_name);
                CREATE INDEX IF NOT EXISTS idx_gruns_date ON global_runs(run_date);
                CREATE INDEX IF NOT EXISTS idx_gfiles_run ON global_files(run_id);
                CREATE INDEX IF NOT EXISTS idx_gfiles_tool ON global_files(tool_id, tier);
                CREATE INDEX IF NOT EXISTS idx_glogs_tier ON global_logs(log_tier, stage);
                CREATE INDEX IF NOT EXISTS idx_glogs_tool ON global_logs(tool_id, action_name);

                CREATE VIRTUAL TABLE IF NOT EXISTS fts_artifacts USING fts5(
                    file_id UNINDEXED,
                    run_id,
                    tool_id,
                    action_name,
                    run_date,
                    tier,
                    filename,
                    content_preview,
                    domain_metrics_json,
                    tokenize='porter unicode61'
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS fts_logs USING fts5(
                    log_id UNINDEXED,
                    log_tier,
                    stage,
                    step,
                    tool_id,
                    action_name,
                    run_id,
                    level,
                    message,
                    tokenize='porter unicode61'
                );
            """)

    def _get_registry_map(self) -> dict[str, dict[str, Any]]:
        """Load tools/registry.json into tool_id -> dict map."""
        reg_map = {}
        if REGISTRY_PATH.exists():
            try:
                reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
                for t in reg.get("tools", []):
                    reg_map[t["tool_id"]] = t
            except Exception:
                pass
        return reg_map

    def sync_single_tool(self, tool_id: str) -> dict[str, Any]:
        """
        Incrementally synchronize one tool from its isolated SQLite database
        into global_master_index.sqlite in <100ms.
        """
        tool_db = TOOL_INDEXES_DIR / f"{tool_id}.sqlite"
        if not tool_db.exists():
            return {"status": "skipped", "message": f"Tool DB not found: {tool_db}"}

        reg_map = self._get_registry_map()
        tinfo = reg_map.get(tool_id, {})
        batch = tinfo.get("batch", 1)
        mech = tinfo.get("mechanism_type", "General")
        name = tinfo.get("name", tool_id)

        # Read records from tool SQLite
        tool_conn = sqlite3.connect(str(tool_db))
        tool_conn.row_factory = sqlite3.Row
        runs = tool_conn.execute("SELECT * FROM indexed_runs WHERE tool_id = ?", (tool_id,)).fetchall()
        files = tool_conn.execute("SELECT * FROM indexed_files WHERE tool_id = ?", (tool_id,)).fetchall()
        tool_conn.close()

        # Run directory domain metrics lookup for latest run
        latest_metrics_json = ""
        if runs:
            latest_metrics_json = runs[0]["domain_metrics_json"] or ""

        # Calculate bytes and counts
        total_runs = len(runs)
        total_actions = len(set(r["action_name"] for r in runs))
        raw_files = [f for f in files if f["tier"] == "raw"]
        clean_files = [f for f in files if f["tier"] == "cleaned"]
        total_raw_bytes = sum(f["size_bytes"] for f in raw_files)
        total_clean_bytes = sum(f["size_bytes"] for f in clean_files)

        with self._get_connection() as conn:
            # 1. Update global_tools
            conn.execute(
                """
                INSERT OR REPLACE INTO global_tools (
                    tool_id, name, batch, mechanism_type, total_runs, total_actions,
                    total_raw_files, total_cleaned_files, total_raw_bytes, total_cleaned_bytes,
                    total_log_entries, latest_domain_metrics_json, last_indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool_id, name, batch, mech, total_runs, total_actions,
                    len(raw_files), len(clean_files), total_raw_bytes, total_clean_bytes,
                    0, latest_metrics_json, datetime.now(timezone.utc).isoformat(),
                ),
            )

            # 2. Update global_runs
            conn.execute("DELETE FROM global_runs WHERE tool_id = ?", (tool_id,))
            for r in runs:
                conn.execute(
                    """
                    INSERT INTO global_runs (
                        run_id, tool_id, batch, mechanism_type, action_name, run_date, target_url,
                        started_at, ended_at, elapsed_sec, status, git_commit,
                        raw_file_count, cleaned_file_count, raw_total_bytes, cleaned_total_bytes,
                        domain_metrics_json, cleaned_text_preview, run_dir_relpath
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["run_id"], tool_id, batch, mech, r["action_name"], r["run_date"], r["target_url"],
                        r["started_at"], r["ended_at"], r["elapsed_sec"], r["status"], r["git_commit"],
                        r["raw_file_count"], r["cleaned_file_count"], r["raw_total_bytes"], r["cleaned_total_bytes"],
                        r["domain_metrics_json"], r["cleaned_text_preview"], r["run_dir_relpath"],
                    ),
                )

            # 3. Update global_files and fts_artifacts
            conn.execute("DELETE FROM global_files WHERE tool_id = ?", (tool_id,))
            conn.execute("DELETE FROM fts_artifacts WHERE tool_id = ?", (tool_id,))

            # Build map of run_id -> domain_metrics_json
            run_metrics_map = {r["run_id"]: r["domain_metrics_json"] for r in runs}

            for f in files:
                conn.execute(
                    """
                    INSERT INTO global_files (
                        file_id, run_id, tool_id, batch, action_name, run_date,
                        tier, filename, extension, size_bytes, sha256_short, relpath, content_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f["file_id"], f["run_id"], tool_id, batch, f["action_name"], f["run_date"],
                        f["tier"], f["filename"], f["extension"], f["size_bytes"],
                        f["sha256_short"], f["relpath"], f["content_preview"],
                    ),
                )

                # Index into FTS5
                conn.execute(
                    """
                    INSERT INTO fts_artifacts (
                        file_id, run_id, tool_id, action_name, run_date,
                        tier, filename, content_preview, domain_metrics_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f["file_id"], f["run_id"], tool_id, f["action_name"], f["run_date"],
                        f["tier"], f["filename"], f["content_preview"] or "",
                        run_metrics_map.get(f["run_id"], "") or "",
                    ),
                )

            # 4. Ingest tool_ops logs & action logs for this tool
            self._sync_logs_for_tool(conn, tool_id)

        # Update JSON snapshot
        self._export_json_summary()

        return {
            "status": "synchronized",
            "tool_id": tool_id,
            "runs": total_runs,
            "files": len(files),
        }

    def _sync_logs_for_tool(self, conn: sqlite3.Connection, tool_id: str) -> None:
        """Scan and insert logs specific to a tool into global_logs and fts_logs."""
        # A. Tool ops logs: tools/<tool_id>/logs/tool_ops.jsonl
        ops_path = ROOT / "tools" / tool_id / "logs" / "tool_ops.jsonl"
        if ops_path.exists():
            try:
                rel = str(ops_path.relative_to(ROOT))
                for idx, line in enumerate(ops_path.read_text(encoding="utf-8", errors="replace").splitlines()):
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    log_id = _make_log_id("tool_ops", r, rel, idx)
                    self._insert_log(conn, log_id, "tool_ops", r, rel)
            except Exception:
                pass

        # B. Action run logs: data/<tool_id>/*/*/*/logs/action_run.jsonl
        tool_data = ROOT / "data" / tool_id
        if tool_data.exists():
            for action_log in tool_data.glob("*/*/*/logs/action_run.jsonl"):
                try:
                    rel = str(action_log.relative_to(ROOT))
                    for idx, line in enumerate(action_log.read_text(encoding="utf-8", errors="replace").splitlines()):
                        line = line.strip()
                        if not line:
                            continue
                        r = json.loads(line)
                        log_id = _make_log_id("action_run", r, rel, idx)
                        self._insert_log(conn, log_id, "action_run", r, rel)
                except Exception:
                    pass

    def _insert_log(self, conn: sqlite3.Connection, log_id: str, log_tier: str, r: dict, source_file: str) -> None:
        """Insert a single log record into global_logs and fts_logs."""
        conn.execute(
            """
            INSERT OR IGNORE INTO global_logs (
                log_id, log_tier, stage, step, tool_id, action_name, run_date,
                run_id, timestamp, level, progress_pct, elapsed_ms, message, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id, log_tier, r.get("stage", ""), r.get("step", ""),
                r.get("tool_id", ""), r.get("action_name", ""),
                r.get("timestamp", "")[:10] if r.get("timestamp") else "",
                r.get("run_id", ""), r.get("timestamp", ""),
                r.get("level", "INFO"), int(r.get("progress_pct") or 0),
                int(r.get("elapsed_ms") or 0), r.get("message", ""), source_file,
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO fts_logs (
                log_id, log_tier, stage, step, tool_id, action_name,
                run_id, level, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id, log_tier, r.get("stage", ""), r.get("step", ""),
                r.get("tool_id", ""), r.get("action_name", ""),
                r.get("run_id", ""), r.get("level", "INFO"), r.get("message", ""),
            ),
        )

    def sync_all(self, rebuild_tools_first: bool = False) -> dict[str, Any]:
        """
        Federate all 20 per-tool indexes and all 4 log tiers into the global master index.
        """
        reg_map = self._get_registry_map()

        # Optional: trigger all 20 tool indexers first
        if rebuild_tools_first:
            for tool_id in reg_map.keys():
                try:
                    mod = importlib.import_module(f"tools.{tool_id}.indexer")
                    cls_ = getattr(mod, "ToolIndexer", None)
                    if cls_:
                        cls_(tool_id).index_all_runs()
                except Exception:
                    pass

        # Clear and rebuild global tables
        with self._get_connection() as conn:
            conn.execute("DELETE FROM global_tools;")
            conn.execute("DELETE FROM global_runs;")
            conn.execute("DELETE FROM global_files;")
            conn.execute("DELETE FROM global_logs;")
            conn.execute("DELETE FROM fts_artifacts;")
            conn.execute("DELETE FROM fts_logs;")

            # 1. Ingest all 20 tool databases
            for tool_id, tinfo in reg_map.items():
                tool_db = TOOL_INDEXES_DIR / f"{tool_id}.sqlite"
                if not tool_db.exists():
                    continue

                batch = tinfo.get("batch", 1)
                mech = tinfo.get("mechanism_type", "General")
                name = tinfo.get("name", tool_id)

                tool_conn = sqlite3.connect(str(tool_db))
                tool_conn.row_factory = sqlite3.Row
                runs = tool_conn.execute("SELECT * FROM indexed_runs WHERE tool_id = ?", (tool_id,)).fetchall()
                files = tool_conn.execute("SELECT * FROM indexed_files WHERE tool_id = ?", (tool_id,)).fetchall()
                tool_conn.close()

                latest_metrics_json = runs[0]["domain_metrics_json"] if runs else ""
                raw_files = [f for f in files if f["tier"] == "raw"]
                clean_files = [f for f in files if f["tier"] == "cleaned"]
                total_raw_bytes = sum(f["size_bytes"] for f in raw_files)
                total_clean_bytes = sum(f["size_bytes"] for f in clean_files)

                # Insert global_tools
                conn.execute(
                    """
                    INSERT INTO global_tools (
                        tool_id, name, batch, mechanism_type, total_runs, total_actions,
                        total_raw_files, total_cleaned_files, total_raw_bytes, total_cleaned_bytes,
                        total_log_entries, latest_domain_metrics_json, last_indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tool_id, name, batch, mech, len(runs), len(set(r["action_name"] for r in runs)),
                        len(raw_files), len(clean_files), total_raw_bytes, total_clean_bytes,
                        0, latest_metrics_json, datetime.now(timezone.utc).isoformat(),
                    ),
                )

                # Insert global_runs
                run_metrics_map = {}
                for r in runs:
                    run_metrics_map[r["run_id"]] = r["domain_metrics_json"]
                    conn.execute(
                        """
                        INSERT INTO global_runs (
                            run_id, tool_id, batch, mechanism_type, action_name, run_date, target_url,
                            started_at, ended_at, elapsed_sec, status, git_commit,
                            raw_file_count, cleaned_file_count, raw_total_bytes, cleaned_total_bytes,
                            domain_metrics_json, cleaned_text_preview, run_dir_relpath
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            r["run_id"], tool_id, batch, mech, r["action_name"], r["run_date"], r["target_url"],
                            r["started_at"], r["ended_at"], r["elapsed_sec"], r["status"], r["git_commit"],
                            r["raw_file_count"], r["cleaned_file_count"], r["raw_total_bytes"], r["cleaned_total_bytes"],
                            r["domain_metrics_json"], r["cleaned_text_preview"], r["run_dir_relpath"],
                        ),
                    )

                # Insert global_files and fts_artifacts
                for f in files:
                    conn.execute(
                        """
                        INSERT INTO global_files (
                            file_id, run_id, tool_id, batch, action_name, run_date,
                            tier, filename, extension, size_bytes, sha256_short, relpath, content_preview
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f["file_id"], f["run_id"], tool_id, batch, f["action_name"], f["run_date"],
                            f["tier"], f["filename"], f["extension"], f["size_bytes"],
                            f["sha256_short"], f["relpath"], f["content_preview"],
                        ),
                    )

                    conn.execute(
                        """
                        INSERT INTO fts_artifacts (
                            file_id, run_id, tool_id, action_name, run_date,
                            tier, filename, content_preview, domain_metrics_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f["file_id"], f["run_id"], tool_id, f["action_name"], f["run_date"],
                            f["tier"], f["filename"], f["content_preview"] or "",
                            run_metrics_map.get(f["run_id"], "") or "",
                        ),
                    )

            # 2. Ingest Tier 4: Global Prompt Logs
            prompt_log_file = ROOT / "logs" / "global" / "antigravity_prompt_log.jsonl"
            if prompt_log_file.exists():
                try:
                    rel = str(prompt_log_file.relative_to(ROOT))
                    for idx, line in enumerate(prompt_log_file.read_text(encoding="utf-8", errors="replace").splitlines()):
                        line = line.strip()
                        if not line:
                            continue
                        r = json.loads(line)
                        log_id = _make_log_id("global_prompt", r, rel, idx)
                        self._insert_log(conn, log_id, "global_prompt", r, rel)
                except Exception:
                    pass

            # 3. Ingest Tier 3: Stage Logs
            stages_dir = ROOT / "logs" / "stages"
            if stages_dir.exists():
                for stage_file in stages_dir.glob("*.jsonl"):
                    try:
                        rel = str(stage_file.relative_to(ROOT))
                        for idx, line in enumerate(stage_file.read_text(encoding="utf-8", errors="replace").splitlines()):
                            line = line.strip()
                            if not line:
                                continue
                            r = json.loads(line)
                            log_id = _make_log_id("stage_log", r, rel, idx)
                            self._insert_log(conn, log_id, "stage_log", r, rel)
                    except Exception:
                        pass

            # 4. Ingest Tier 2: Tool Ops Logs (all tools)
            tools_dir = ROOT / "tools"
            if tools_dir.exists():
                for ops_file in tools_dir.glob("*/logs/tool_ops.jsonl"):
                    try:
                        rel = str(ops_file.relative_to(ROOT))
                        for idx, line in enumerate(ops_file.read_text(encoding="utf-8", errors="replace").splitlines()):
                            line = line.strip()
                            if not line:
                                continue
                            r = json.loads(line)
                            log_id = _make_log_id("tool_ops", r, rel, idx)
                            self._insert_log(conn, log_id, "tool_ops", r, rel)
                    except Exception:
                        pass

            # 5. Ingest Tier 1: Action Run Logs
            data_dir = ROOT / "data"
            if data_dir.exists():
                for action_file in data_dir.glob("*/*/*/*/logs/action_run.jsonl"):
                    try:
                        rel = str(action_file.relative_to(ROOT))
                        for idx, line in enumerate(action_file.read_text(encoding="utf-8", errors="replace").splitlines()):
                            line = line.strip()
                            if not line:
                                continue
                            r = json.loads(line)
                            log_id = _make_log_id("action_run", r, rel, idx)
                            self._insert_log(conn, log_id, "action_run", r, rel)
                    except Exception:
                        pass

            # Update log counts in global_tools
            for tool_id in reg_map.keys():
                count = conn.execute("SELECT COUNT(*) FROM global_logs WHERE tool_id = ?", (tool_id,)).fetchone()[0]
                conn.execute("UPDATE global_tools SET total_log_entries = ? WHERE tool_id = ?", (count, tool_id))

        # Export full summary to JSON snapshot
        summary = self._export_json_summary()
        return summary

    def _export_json_summary(self) -> dict[str, Any]:
        """Generate and export comprehensive summary to global_master_index.json."""
        with self._get_connection() as conn:
            tools_rows = conn.execute("SELECT * FROM global_tools ORDER BY batch, tool_id").fetchall()
            runs_rows = conn.execute("SELECT * FROM global_runs ORDER BY started_at DESC").fetchall()
            files_rows = conn.execute("SELECT * FROM global_files").fetchall()
            logs_rows = conn.execute("SELECT * FROM global_logs").fetchall()

            # Breakdown metrics
            total_tools = len(tools_rows)
            total_runs = len(runs_rows)
            total_files = len(files_rows)
            total_logs = len(logs_rows)

            raw_files = [f for f in files_rows if f["tier"] == "raw"]
            clean_files = [f for f in files_rows if f["tier"] == "cleaned"]
            total_raw_bytes = sum(f["size_bytes"] for f in raw_files)
            total_clean_bytes = sum(f["size_bytes"] for f in clean_files)

            # Breakdown of logs by tier
            tier_counts = {}
            for l in logs_rows:
                tier = l["log_tier"]
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            # Breakdown of logs by stage
            stage_counts = {}
            for l in logs_rows:
                stg = l["stage"] or "Unassigned"
                stage_counts[stg] = stage_counts.get(stg, 0) + 1

            # Runs by tool, action, and date
            tool_run_counts = {}
            action_run_counts = {}
            date_run_counts = {}
            for r in runs_rows:
                tid = r["tool_id"]
                act = r["action_name"]
                dt = r["run_date"]
                tool_run_counts[tid] = tool_run_counts.get(tid, 0) + 1
                action_run_counts[act] = action_run_counts.get(act, 0) + 1
                if dt:
                    date_run_counts[dt] = date_run_counts.get(dt, 0) + 1

            # Distinct filters
            distinct_actions = sorted(list(set(r["action_name"] for r in runs_rows if r["action_name"])))
            distinct_dates = sorted(list(set(r["run_date"] for r in runs_rows if r["run_date"])), reverse=True)
            distinct_stages = sorted(list(set(l["stage"] for l in logs_rows if l["stage"])))
            distinct_steps = sorted(list(set(l["step"] for l in logs_rows if l["step"])))

            tools_list = []
            for t in tools_rows:
                td = dict(t)
                if td.get("latest_domain_metrics_json"):
                    try:
                        td["latest_domain_metrics"] = json.loads(td["latest_domain_metrics_json"])
                    except Exception:
                        td["latest_domain_metrics"] = {}
                else:
                    td["latest_domain_metrics"] = {}
                tools_list.append(td)

            summary = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "totals": {
                    "total_tools": total_tools,
                    "total_runs": total_runs,
                    "total_files": total_files,
                    "total_raw_files": len(raw_files),
                    "total_cleaned_files": len(clean_files),
                    "total_raw_bytes": total_raw_bytes,
                    "total_cleaned_bytes": total_clean_bytes,
                    "total_bytes": total_raw_bytes + total_clean_bytes,
                    "total_logs": total_logs,
                },
                "logs_breakdown": {
                    "by_tier": tier_counts,
                    "by_stage": stage_counts,
                },
                "filters": {
                    "actions": distinct_actions,
                    "dates": distinct_dates,
                    "stages": distinct_stages,
                    "steps": distinct_steps,
                },
                "distribution": {
                    "runs_by_tool": tool_run_counts,
                    "runs_by_action": action_run_counts,
                    "runs_by_date": date_run_counts,
                },
                "tools": tools_list,
            }

            self.json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
            return summary

    def get_overview(self) -> dict[str, Any]:
        """Return master overview JSON snapshot (from cache or live generation)."""
        if self.json_path.exists():
            try:
                return json.loads(self.json_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return self._export_json_summary()

    def query_runs(
        self,
        tool_id: str | None = None,
        batch: int | None = None,
        action_name: str | None = None,
        run_date: str | None = None,
        status: str | None = None,
        q: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query global runs with multi-filter and optional search."""
        query = "SELECT * FROM global_runs WHERE 1=1"
        params = []

        if tool_id and tool_id != "global":
            query += " AND tool_id = ?"
            params.append(tool_id)
        if batch is not None:
            query += " AND batch = ?"
            params.append(batch)
        if action_name:
            query += " AND action_name = ?"
            params.append(action_name)
        if run_date:
            query += " AND run_date = ?"
            params.append(run_date)
        if status:
            query += " AND status = ?"
            params.append(status)
        if q:
            query += " AND (run_id LIKE ? OR target_url LIKE ? OR domain_metrics_json LIKE ? OR cleaned_text_preview LIKE ?)"
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q, like_q])

        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            res = []
            for r in rows:
                rd = dict(r)
                if rd.get("domain_metrics_json"):
                    try:
                        rd["domain_metrics"] = json.loads(rd["domain_metrics_json"])
                    except Exception:
                        rd["domain_metrics"] = {}
                else:
                    rd["domain_metrics"] = {}
                res.append(rd)
            return res

    def query_files(
        self,
        tool_id: str | None = None,
        action_name: str | None = None,
        run_date: str | None = None,
        tier: str | None = None,
        extension: str | None = None,
        q: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query files with FTS5 or LIKE filtering."""
        with self._get_connection() as conn:
            if q and q.strip():
                # Use FTS5
                # Sanitize query for FTS5 (escape special chars)
                clean_q = "".join(c if c.isalnum() or c in (" ", "_", "-") else " " for c in q).strip()
                if clean_q:
                    fts_sql = "SELECT file_id FROM fts_artifacts WHERE fts_artifacts MATCH ? LIMIT ?"
                    try:
                        fts_ids = [row[0] for row in conn.execute(fts_sql, (f'"{clean_q}"*', limit * 2)).fetchall()]
                    except Exception:
                        fts_ids = []
                    
                    if fts_ids:
                        placeholders = ",".join("?" for _ in fts_ids)
                        sql = f"SELECT * FROM global_files WHERE file_id IN ({placeholders})"
                        params = list(fts_ids)
                        if tool_id and tool_id != "global":
                            sql += " AND tool_id = ?"
                            params.append(tool_id)
                        if tier:
                            sql += " AND tier = ?"
                            params.append(tier)
                        sql += f" LIMIT {limit}"
                        return [dict(r) for r in conn.execute(sql, params).fetchall()]

            # Fallback to standard SQL query
            query = "SELECT * FROM global_files WHERE 1=1"
            params = []
            if tool_id and tool_id != "global":
                query += " AND tool_id = ?"
                params.append(tool_id)
            if action_name:
                query += " AND action_name = ?"
                params.append(action_name)
            if run_date:
                query += " AND run_date = ?"
                params.append(run_date)
            if tier:
                query += " AND tier = ?"
                params.append(tier)
            if extension:
                query += " AND extension = ?"
                params.append(extension.lower())
            if q:
                query += " AND (filename LIKE ? OR content_preview LIKE ?)"
                like_q = f"%{q}%"
                params.extend([like_q, like_q])

            query += " ORDER BY run_date DESC, filename ASC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def query_logs(
        self,
        tool_id: str | None = None,
        log_tier: str | None = None,
        stage: str | None = None,
        step: str | None = None,
        action_name: str | None = None,
        run_date: str | None = None,
        run_id: str | None = None,
        level: str | None = None,
        q: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Query unified logs with FTS5 or multi-column filter."""
        with self._get_connection() as conn:
            if q and q.strip():
                clean_q = "".join(c if c.isalnum() or c in (" ", "_", "-") else " " for c in q).strip()
                if clean_q:
                    try:
                        fts_sql = "SELECT log_id FROM fts_logs WHERE fts_logs MATCH ? LIMIT ?"
                        fts_ids = [row[0] for row in conn.execute(fts_sql, (f'"{clean_q}"*', limit * 2)).fetchall()]
                        if fts_ids:
                            placeholders = ",".join("?" for _ in fts_ids)
                            sql = f"SELECT * FROM global_logs WHERE log_id IN ({placeholders})"
                            params = list(fts_ids)
                            if tool_id and tool_id != "global":
                                sql += " AND tool_id = ?"
                                params.append(tool_id)
                            if log_tier:
                                sql += " AND log_tier = ?"
                                params.append(log_tier)
                            if stage:
                                sql += " AND stage = ?"
                                params.append(stage)
                            sql += " ORDER BY timestamp DESC LIMIT ?"
                            params.append(limit)
                            return [dict(r) for r in conn.execute(sql, params).fetchall()]
                    except Exception:
                        pass

            query = "SELECT * FROM global_logs WHERE 1=1"
            params = []
            if tool_id and tool_id != "global":
                query += " AND tool_id = ?"
                params.append(tool_id)
            if log_tier:
                query += " AND log_tier = ?"
                params.append(log_tier)
            if stage:
                query += " AND stage = ?"
                params.append(stage)
            if step:
                query += " AND step = ?"
                params.append(step)
            if action_name:
                query += " AND action_name = ?"
                params.append(action_name)
            if run_date:
                query += " AND run_date = ?"
                params.append(run_date)
            if run_id:
                query += " AND run_id = ?"
                params.append(run_id)
            if level:
                query += " AND level = ?"
                params.append(level)
            if q:
                query += " AND message LIKE ?"
                params.append(f"%{q}%")

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]


if __name__ == "__main__":
    indexer = GlobalMasterIndexer()
    print("Executing full federation of 20 tools and 4 log tiers...")
    t0 = time.time()
    summary = indexer.sync_all(rebuild_tools_first=False)
    elapsed = time.time() - t0
    print(f"Master index synchronized in {elapsed:.2f}s!")
    print(f"Tools: {summary['totals']['total_tools']}, Runs: {summary['totals']['total_runs']}, Files: {summary['totals']['total_files']}, Logs: {summary['totals']['total_logs']}")
