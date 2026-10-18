"""
backend/app.py
==============
FastAPI Real-Time Telemetry Backend
Serves the Control Center dashboard on http://127.0.0.1:8000

Endpoints:
  GET  /                     → Serves frontend/index.html
  GET  /api/state            → Current live_state.json snapshot
  GET  /api/tools            → tools/registry.json
  GET  /api/git-log          → Last 20 git commits
  GET  /api/data-tree        → data/ directory tree for the explorer
  GET  /api/run-manifest     → Specific run manifest
  POST /api/demo-run         → Trigger a demo telemetry simulation
  WS   /ws/telemetry         → Push live_state.json every 1 second
  WS   /ws/logs              → Stream JSONL log lines via watchdog
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.state_tracker import (
    complete_task,
    fail_task,
    read_state,
    refresh_workers,
    start_task,
    update_progress,
    write_state,
)
from core.folder_manager import create_action_run, complete_action_run
from core.git_manager import get_log, get_latest_hash

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    _WATCHDOG_OK = True
except ImportError:
    _WATCHDOG_OK = False

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Crawlers_testing Control Center",
    description="Real-Time Telemetry & Tool Management Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
TOOLS_DIR = ROOT / "tools"

# Mount static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ─── WebSocket Connection Managers ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict | str):
        msg = data if isinstance(data, str) else json.dumps(data, default=str)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


telemetry_mgr = ConnectionManager()
log_mgr = ConnectionManager()
log_broadcast_queue: asyncio.Queue = asyncio.Queue()

# ─── HTTP Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    html_path = FRONTEND_DIR / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return HTMLResponse("<h1>Control Center frontend not found.</h1>", status_code=404)


@app.get("/api/state")
async def get_state():
    state = read_state()
    if state.get("is_running") and state.get("started_at_epoch"):
        state["elapsed_seconds"] = round(
            time.time() - state["started_at_epoch"], 1
        )
    return JSONResponse(state)


@app.get("/api/tools")
async def get_tools():
    registry_path = TOOLS_DIR / "registry.json"
    if registry_path.exists():
        return JSONResponse(json.loads(registry_path.read_text(encoding="utf-8")))
    return JSONResponse({"error": "registry.json not found"}, status_code=404)


@app.get("/api/git-log")
async def get_git_log():
    try:
        log = get_log(n=20)
        return JSONResponse({"commits": log})
    except Exception as e:
        return JSONResponse({"commits": [], "error": str(e)})


@app.get("/api/data-tree")
async def get_data_tree():
    """Return hierarchical data directory tree for the run explorer."""
    tree = {}
    if not DATA_DIR.exists():
        return JSONResponse({"tree": tree})

    for tool_dir in sorted(DATA_DIR.iterdir()):
        if not tool_dir.is_dir() or tool_dir.name.startswith("."):
            continue
        tool_id = tool_dir.name
        tree[tool_id] = {}
        for action_dir in sorted(tool_dir.iterdir()):
            if not action_dir.is_dir():
                continue
            action = action_dir.name
            tree[tool_id][action] = {}
            for date_dir in sorted(action_dir.iterdir(), reverse=True):
                if not date_dir.is_dir():
                    continue
                date = date_dir.name
                tree[tool_id][action][date] = []
                for run_dir in sorted(date_dir.iterdir(), reverse=True):
                    if not run_dir.is_dir():
                        continue
                    manifest_path = run_dir / "run_manifest.json"
                    manifest = {}
                    if manifest_path.exists():
                        try:
                            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                    raw_files = [f.name for f in (run_dir / "raw").iterdir()] if (run_dir / "raw").exists() else []
                    cleaned_files = [f.name for f in (run_dir / "cleaned").iterdir()] if (run_dir / "cleaned").exists() else []
                    tree[tool_id][action][date].append(
                        {
                            "run_id": run_dir.name,
                            "manifest": manifest,
                            "raw_files": raw_files,
                            "cleaned_files": cleaned_files,
                        }
                    )
    return JSONResponse({"tree": tree})


@app.get("/api/run-manifest")
async def get_run_manifest(tool_id: str, action: str, date: str, run_id: str):
    manifest_path = DATA_DIR / tool_id / action / date / run_id / "run_manifest.json"
    if manifest_path.exists():
        return JSONResponse(json.loads(manifest_path.read_text(encoding="utf-8")))
    return JSONResponse({"error": "Manifest not found"}, status_code=404)


@app.get("/api/run-log")
async def get_run_log(tool_id: str, action: str, date: str, run_id: str):
    log_path = DATA_DIR / tool_id / action / date / run_id / "logs" / "action_run.jsonl"
    if log_path.exists():
        lines = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                lines.append(json.loads(line))
            except Exception:
                lines.append({"raw": line})
        return JSONResponse({"lines": lines})
    return JSONResponse({"lines": [], "error": "Log not found"})


@app.get("/api/recent-logs")
async def get_recent_logs(limit: int = 100):
    """Return historical log entries on dashboard load."""
    records = []
    log_files = [
        ROOT / "logs" / "global" / "antigravity_prompt_log.jsonl",
    ]
    stages_dir = ROOT / "logs" / "stages"
    if stages_dir.exists():
        log_files.extend(sorted(stages_dir.glob("*.jsonl")))

    tools_dir = ROOT / "tools"
    if tools_dir.exists():
        log_files.extend(sorted(tools_dir.glob("*/logs/tool_ops.jsonl")))

    for lf in log_files:
        if lf.exists():
            try:
                rel = str(lf.relative_to(ROOT))
                for line in lf.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        r = {"raw": line}
                    r["_source_file"] = rel
                    records.append(r)
            except Exception:
                pass

    records.sort(key=lambda r: r.get("timestamp") or "")
    return JSONResponse({"logs": records[-limit:]})


@app.get("/api/file-preview")
async def get_file_preview(tool_id: str, action: str, date: str, run_id: str, folder: str, filename: str):
    """Return preview of raw or cleaned file content (up to 10 KB)."""
    if folder not in ("raw", "cleaned"):
        return JSONResponse({"error": "Invalid folder (must be raw or cleaned)"}, status_code=400)
    safe_filename = Path(filename).name
    file_path = DATA_DIR / tool_id / action / date / run_id / folder / safe_filename
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")[:10240]
        return JSONResponse({
            "filename": safe_filename,
            "folder": folder,
            "size": file_path.stat().st_size,
            "content": content,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tool-indexes")
async def get_tool_indexes():
    """Return catalog of all 20 tool index summaries."""
    index_dir = ROOT / "index_store" / "tool_indexes"
    summaries = []
    if index_dir.exists():
        for jf in sorted(index_dir.glob("*_index.json")):
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                summaries.append({
                    "tool_id": data.get("tool_id"),
                    "metadata": data.get("metadata", {}),
                    "total_runs": data.get("total_runs", 0),
                    "total_files": data.get("total_files", 0),
                    "indexed_at": data.get("indexed_at"),
                })
            except Exception:
                pass
    return JSONResponse({"tool_indexes": summaries, "count": len(summaries)})


@app.get("/api/tool-indexes/{tool_id}")
async def get_single_tool_index(tool_id: str):
    """Return full index details (runs, domain metrics, files, recent logs) for a tool."""
    json_path = ROOT / "index_store" / "tool_indexes" / f"{tool_id}_index.json"
    if json_path.exists():
        try:
            return JSONResponse(json.loads(json_path.read_text(encoding="utf-8")))
        except Exception as e:
            return JSONResponse({"error": f"Failed to parse index json: {e}"}, status_code=500)

    try:
        import importlib
        from core.base_indexer import BaseToolIndexer
        indexer_cls = BaseToolIndexer
        try:
            mod = importlib.import_module(f"tools.{tool_id}.indexer")
            indexer_cls = getattr(mod, "ToolIndexer", BaseToolIndexer)
        except Exception:
            pass
        indexer = indexer_cls(tool_id)
        summary = indexer.get_summary()
        return JSONResponse(summary)
    except Exception as e:
        return JSONResponse({"error": f"Tool index not found: {e}"}, status_code=404)


@app.post("/api/tool-indexes/{tool_id}/rebuild")
async def rebuild_tool_index(tool_id: str):
    """Rebuild SQLite index and JSON snapshot for a tool by scanning data/."""
    try:
        import importlib
        from core.base_indexer import BaseToolIndexer
        indexer_cls = BaseToolIndexer
        try:
            mod = importlib.import_module(f"tools.{tool_id}.indexer")
            indexer_cls = getattr(mod, "ToolIndexer", BaseToolIndexer)
        except Exception:
            pass
        indexer = indexer_cls(tool_id)
        res = indexer.index_all_runs()
        return JSONResponse({
            "status": "rebuilt",
            "tool_id": tool_id,
            "runs_indexed": res.get("runs_indexed", 0),
            "summary": res.get("summary", {}),
        })
    except Exception as e:
        return JSONResponse({"error": f"Failed to rebuild index: {e}"}, status_code=500)


# ─── Global & Isolated Index Query Endpoints (Stage 2 Step 2.2) ───────────────

from core.global_indexer import GlobalMasterIndexer

@app.get("/api/index/overview")
async def get_index_overview():
    """Return global master index overview and all tool index rollups."""
    try:
        indexer = GlobalMasterIndexer()
        overview = indexer.get_overview()
        
        # Load all 20 individual tool index summaries as well
        tool_indexes_dir = ROOT / "index_store" / "tool_indexes"
        tools_summaries = []
        if tool_indexes_dir.exists():
            for jf in sorted(tool_indexes_dir.glob("*_index.json")):
                try:
                    data = json.loads(jf.read_text(encoding="utf-8"))
                    tools_summaries.append({
                        "tool_id": data.get("tool_id"),
                        "metadata": data.get("metadata", {}),
                        "total_runs": data.get("total_runs", 0),
                        "total_files": data.get("total_files", 0),
                        "indexed_at": data.get("indexed_at"),
                    })
                except Exception:
                    pass
        
        overview["individual_tool_indexes"] = tools_summaries
        return JSONResponse(overview)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/runs")
async def get_index_runs(
    scope: str = "global",
    tool_id: str | None = None,
    batch: int | None = None,
    action_name: str | None = None,
    run_date: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 100,
):
    """
    Query indexed runs from either:
      - scope='global' -> index_store/global_master_index.sqlite (global_runs)
      - scope='<tool_id>' -> index_store/tool_indexes/<tool_id>.sqlite (indexed_runs) directly
    """
    try:
        if scope and scope != "global":
            tool_db = ROOT / "index_store" / "tool_indexes" / f"{scope}.sqlite"
            if not tool_db.exists():
                return JSONResponse({"error": f"Tool index not found: {scope}"}, status_code=404)
            
            conn = sqlite3.connect(str(tool_db))
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM indexed_runs WHERE 1=1"
            params = []
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
                lq = f"%{q}%"
                params.extend([lq, lq, lq, lq])
            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            conn.close()
            
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
            return JSONResponse({"scope": scope, "runs": res, "count": len(res)})
        else:
            indexer = GlobalMasterIndexer()
            runs = indexer.query_runs(
                tool_id=tool_id,
                batch=batch,
                action_name=action_name,
                run_date=run_date,
                status=status,
                q=q,
                limit=limit,
            )
            return JSONResponse({"scope": "global", "runs": runs, "count": len(runs)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/files")
async def get_index_files(
    scope: str = "global",
    tool_id: str | None = None,
    action_name: str | None = None,
    run_date: str | None = None,
    tier: str | None = None,
    extension: str | None = None,
    q: str | None = None,
    limit: int = 100,
):
    """
    Query indexed files from either:
      - scope='global' -> index_store/global_master_index.sqlite (FTS5 fts_artifacts & global_files)
      - scope='<tool_id>' -> index_store/tool_indexes/<tool_id>.sqlite (indexed_files) directly
    """
    try:
        if scope and scope != "global":
            tool_db = ROOT / "index_store" / "tool_indexes" / f"{scope}.sqlite"
            if not tool_db.exists():
                return JSONResponse({"error": f"Tool index not found: {scope}"}, status_code=404)
            
            conn = sqlite3.connect(str(tool_db))
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM indexed_files WHERE 1=1"
            params = []
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
                lq = f"%{q}%"
                params.extend([lq, lq])
            query += " ORDER BY run_date DESC, filename ASC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            conn.close()
            return JSONResponse({"scope": scope, "files": [dict(r) for r in rows], "count": len(rows)})
        else:
            indexer = GlobalMasterIndexer()
            files = indexer.query_files(
                tool_id=tool_id,
                action_name=action_name,
                run_date=run_date,
                tier=tier,
                extension=extension,
                q=q,
                limit=limit,
            )
            return JSONResponse({"scope": "global", "files": files, "count": len(files)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/logs")
async def get_index_logs(
    scope: str = "global",
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
):
    """
    Query multi-tier indexed logs with FTS5 keyword search.
      - scope='global' -> queries global_logs / fts_logs across all 4 tiers
      - scope='<tool_id>' -> queries index_store/tool_indexes/<tool_id>.sqlite (indexed_logs)
    """
    try:
        if scope and scope != "global":
            tool_db = ROOT / "index_store" / "tool_indexes" / f"{scope}.sqlite"
            if not tool_db.exists():
                return JSONResponse({"error": f"Tool index not found: {scope}"}, status_code=404)
            
            conn = sqlite3.connect(str(tool_db))
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM indexed_logs WHERE 1=1"
            params = []
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
            conn.close()
            return JSONResponse({"scope": scope, "logs": [dict(r) for r in rows], "count": len(rows)})
        else:
            indexer = GlobalMasterIndexer()
            logs = indexer.query_logs(
                tool_id=tool_id,
                log_tier=log_tier,
                stage=stage,
                step=step,
                action_name=action_name,
                run_date=run_date,
                run_id=run_id,
                level=level,
                q=q,
                limit=limit,
            )
            return JSONResponse({"scope": "global", "logs": logs, "count": len(logs)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/index/rebuild")
async def rebuild_index(payload: dict | None = None):
    """
    Trigger live background re-indexing with animated telemetry updates on HUD.
    Accepts: {"scope": "global" | "<tool_id>"}
    """
    scope = (payload or {}).get("scope", "global")

    def _worker():
        try:
            start_task(
                stage="Stage 2",
                step="Step 2.2",
                tool_id="global_indexer" if scope == "global" else scope,
                action="rebuild_index",
                subtask=f"Rebuilding index for scope: {scope}...",
            )
            update_progress(progress_percent=20, subtask=f"Re-indexing pipeline active ({scope})...")
            
            if scope == "global":
                indexer = GlobalMasterIndexer()
                update_progress(progress_percent=50, subtask="Federating 20 tool databases into master index...")
                indexer.sync_all(rebuild_tools_first=True)
            else:
                import importlib
                from core.base_indexer import BaseToolIndexer
                indexer_cls = BaseToolIndexer
                try:
                    mod = importlib.import_module(f"tools.{scope}.indexer")
                    indexer_cls = getattr(mod, "ToolIndexer", BaseToolIndexer)
                except Exception:
                    pass
                update_progress(progress_percent=50, subtask=f"Re-indexing {scope}...")
                indexer_cls(scope).index_all_runs()
                GlobalMasterIndexer().sync_single_tool(scope)

            update_progress(progress_percent=100, subtask=f"Rebuild completed for {scope}!")
            complete_task(message=f"Index rebuild finished successfully for {scope}")
        except Exception as e:
            fail_task(reason=f"Index rebuild failed: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return JSONResponse({
        "status": "started",
        "scope": scope,
        "message": f"Index rebuild started for {scope}. Telemetry HUD updating.",
    })


@app.get("/api/index/pipelines-status")
async def get_pipelines_status():
    """
    Compares each of the 20 isolated SQLite databases (index_store/tool_indexes/<tool_id>.sqlite)
    against index_store/global_master_index.sqlite.
    Returns: tool_id, name, batch, mechanism_type, sqlite_path, db_size_kb,
             isolated_runs_count, global_runs_count, isolated_files_count, global_files_count,
             isolated_logs_count, sync_status ("SYNCED" | "OUT_OF_SYNC"), last_indexed_at, supported_actions.
    """
    try:
        registry_path = ROOT / "tools" / "registry.json"
        tools_list = []
        if registry_path.exists():
            with open(registry_path, "r", encoding="utf-8") as f:
                tools_list = json.load(f).get("tools", [])

        master_db = ROOT / "index_store" / "global_master_index.sqlite"
        master_conn = None
        global_tools_map = {}
        if master_db.exists():
            master_conn = sqlite3.connect(str(master_db))
            master_conn.row_factory = sqlite3.Row
            for row in master_conn.execute("SELECT * FROM global_tools").fetchall():
                global_tools_map[row["tool_id"]] = dict(row)

        pipelines = []
        synced_count = 0
        total_isolated_size_kb = 0.0

        for t in tools_list:
            tid = t["tool_id"]
            tool_db = ROOT / "index_store" / "tool_indexes" / f"{tid}.sqlite"
            db_size_kb = round(tool_db.stat().st_size / 1024, 2) if tool_db.exists() else 0.0
            total_isolated_size_kb += db_size_kb

            isolated_runs = 0
            isolated_files = 0
            isolated_logs = 0
            last_indexed = None

            if tool_db.exists():
                try:
                    conn = sqlite3.connect(str(tool_db))
                    conn.row_factory = sqlite3.Row
                    meta = conn.execute("SELECT * FROM tool_metadata WHERE tool_id = ?", (tid,)).fetchone()
                    if meta:
                        last_indexed = meta["last_indexed_at"]
                    isolated_runs = conn.execute("SELECT COUNT(*) FROM indexed_runs WHERE tool_id = ?", (tid,)).fetchone()[0]
                    isolated_files = conn.execute("SELECT COUNT(*) FROM indexed_files WHERE tool_id = ?", (tid,)).fetchone()[0]
                    isolated_logs = conn.execute("SELECT COUNT(*) FROM indexed_logs WHERE tool_id = ?", (tid,)).fetchone()[0]
                    conn.close()
                except Exception:
                    pass

            g_info = global_tools_map.get(tid, {})
            global_runs = g_info.get("total_runs", 0)
            global_files = (g_info.get("total_raw_files", 0) + g_info.get("total_cleaned_files", 0))

            is_synced = (isolated_runs == global_runs and isolated_files == global_files)
            sync_status = "SYNCED" if is_synced else "OUT_OF_SYNC"
            if is_synced:
                synced_count += 1

            pipelines.append({
                "tool_id": tid,
                "name": t.get("name", tid),
                "batch": t.get("batch", 1),
                "mechanism_type": t.get("mechanism_type", "HTTP"),
                "sqlite_path": f"index_store/tool_indexes/{tid}.sqlite",
                "db_size_kb": db_size_kb,
                "isolated_runs_count": isolated_runs,
                "global_runs_count": global_runs,
                "isolated_files_count": isolated_files,
                "global_files_count": global_files,
                "isolated_logs_count": isolated_logs,
                "sync_status": sync_status,
                "last_indexed_at": last_indexed or g_info.get("last_indexed_at"),
                "supported_actions": t.get("supported_actions", []),
                "installed": t.get("installed", True),
            })

        master_size_kb = round(master_db.stat().st_size / 1024, 2) if master_db.exists() else 0.0
        if master_conn:
            master_conn.close()

        return JSONResponse({
            "pipelines": pipelines,
            "total_tools": len(pipelines),
            "synced_count": synced_count,
            "master_db_size_kb": master_size_kb,
            "total_isolated_size_kb": round(total_isolated_size_kb, 2),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/cascading-facets")
async def get_cascading_facets(
    scope: str = "global",
    tool_id: str | None = None,
    action_name: str | None = None,
    run_date: str | None = None,
):
    """
    Returns available hierarchy of values for cascading dropdowns:
    tools, actions, dates, runs, stages, steps.
    Queries either global_master_index.sqlite (when scope=global)
    or index_store/tool_indexes/<scope>.sqlite (when scope=<tool_id>).
    """
    try:
        active_tool = scope if scope != "global" else tool_id

        if scope and scope != "global":
            db_path = ROOT / "index_store" / "tool_indexes" / f"{scope}.sqlite"
            if not db_path.exists():
                return JSONResponse({"error": f"Tool index not found: {scope}"}, status_code=404)
            runs_tbl = "indexed_runs"
            logs_tbl = "indexed_logs"
            tools_tbl = "tool_metadata"
        else:
            db_path = ROOT / "index_store" / "global_master_index.sqlite"
            if not db_path.exists():
                return JSONResponse({"error": "Global master index not found"}, status_code=404)
            runs_tbl = "global_runs"
            logs_tbl = "global_logs"
            tools_tbl = "global_tools"

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # 1. Tools list
        tools_res = []
        if scope == "global":
            t_rows = conn.execute(f"SELECT tool_id, name, total_runs FROM {tools_tbl} ORDER BY tool_id ASC").fetchall()
            for r in t_rows:
                tools_res.append({"tool_id": r["tool_id"], "name": r["name"], "runs_count": r["total_runs"]})
        else:
            t_rows = conn.execute(f"SELECT tool_id, name, total_runs FROM {tools_tbl}").fetchall()
            for r in t_rows:
                tools_res.append({"tool_id": r["tool_id"], "name": r["name"], "runs_count": r["total_runs"]})

        # 2. Actions list (filtered by active_tool if given)
        action_query = f"SELECT action_name, COUNT(*) as runs_count FROM {runs_tbl} WHERE 1=1"
        a_params = []
        if active_tool:
            action_query += " AND tool_id = ?"
            a_params.append(active_tool)
        action_query += " GROUP BY action_name ORDER BY runs_count DESC, action_name ASC"
        actions_res = [{"action_name": r["action_name"], "runs_count": r["runs_count"]} for r in conn.execute(action_query, a_params).fetchall()]

        # 3. Dates list (filtered by active_tool and action_name if given)
        date_query = f"SELECT run_date, COUNT(*) as runs_count FROM {runs_tbl} WHERE 1=1"
        d_params = []
        if active_tool:
            date_query += " AND tool_id = ?"
            d_params.append(active_tool)
        if action_name:
            date_query += " AND action_name = ?"
            d_params.append(action_name)
        date_query += " GROUP BY run_date ORDER BY run_date DESC"
        dates_res = [{"run_date": r["run_date"], "runs_count": r["runs_count"]} for r in conn.execute(date_query, d_params).fetchall()]

        # 4. Runs list (filtered by active_tool, action_name, run_date if given)
        runs_query = f"SELECT run_id, tool_id, action_name, run_date, status, elapsed_sec, target_url, raw_file_count, cleaned_file_count FROM {runs_tbl} WHERE 1=1"
        r_params = []
        if active_tool:
            runs_query += " AND tool_id = ?"
            r_params.append(active_tool)
        if action_name:
            runs_query += " AND action_name = ?"
            r_params.append(action_name)
        if run_date:
            runs_query += " AND run_date = ?"
            r_params.append(run_date)
        runs_query += " ORDER BY started_at DESC LIMIT 100"
        runs_res = [dict(r) for r in conn.execute(runs_query, r_params).fetchall()]

        # 5. Stages and Steps in logs
        stages_res = [r[0] for r in conn.execute(f"SELECT DISTINCT stage FROM {logs_tbl} WHERE stage IS NOT NULL AND stage != '' ORDER BY stage ASC").fetchall()]
        steps_res = [r[0] for r in conn.execute(f"SELECT DISTINCT step FROM {logs_tbl} WHERE step IS NOT NULL AND step != '' ORDER BY step ASC").fetchall()]

        conn.close()

        return JSONResponse({
            "scope": scope,
            "active_tool_id": active_tool,
            "tools": tools_res,
            "actions": actions_res,
            "dates": dates_res,
            "runs": runs_res,
            "stages": stages_res,
            "steps": steps_res,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/folder-bundle")
async def get_folder_bundle(
    run_id: str,
    scope: str = "global",
):
    """
    Returns a unified single-call bundle for a specific run_id:
    run_metadata (with parsed domain_metrics), raw_files, cleaned_files, action_logs, tool_ops_logs.
    """
    try:
        if scope and scope != "global":
            db_path = ROOT / "index_store" / "tool_indexes" / f"{scope}.sqlite"
            runs_tbl = "indexed_runs"
            files_tbl = "indexed_files"
            logs_tbl = "indexed_logs"
        else:
            db_path = ROOT / "index_store" / "global_master_index.sqlite"
            runs_tbl = "global_runs"
            files_tbl = "global_files"
            logs_tbl = "global_logs"

        if not db_path.exists():
            return JSONResponse({"error": f"Database not found: {db_path.name}"}, status_code=404)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        run_row = conn.execute(f"SELECT * FROM {runs_tbl} WHERE run_id = ?", (run_id,)).fetchone()

        # If not found in isolated DB, try falling back to global master
        if not run_row and scope != "global":
            master_path = ROOT / "index_store" / "global_master_index.sqlite"
            if master_path.exists():
                mconn = sqlite3.connect(str(master_path))
                mconn.row_factory = sqlite3.Row
                run_row = mconn.execute("SELECT * FROM global_runs WHERE run_id = ?", (run_id,)).fetchone()
                if run_row:
                    runs_tbl = "global_runs"
                    files_tbl = "global_files"
                    logs_tbl = "global_logs"
                    conn.close()
                    conn = mconn

        if not run_row:
            conn.close()
            return JSONResponse({"error": f"Run not found: {run_id}"}, status_code=404)

        run_dict = dict(run_row)
        if run_dict.get("domain_metrics_json"):
            try:
                run_dict["domain_metrics"] = json.loads(run_dict["domain_metrics_json"])
            except Exception:
                run_dict["domain_metrics"] = {}
        else:
            run_dict["domain_metrics"] = {}

        tool_id = run_dict.get("tool_id")

        # Files
        raw_rows = conn.execute(
            f"SELECT * FROM {files_tbl} WHERE run_id = ? AND tier = 'raw' ORDER BY filename ASC",
            (run_id,)
        ).fetchall()
        cleaned_rows = conn.execute(
            f"SELECT * FROM {files_tbl} WHERE run_id = ? AND tier = 'cleaned' ORDER BY filename ASC",
            (run_id,)
        ).fetchall()

        # Action logs for this run
        action_log_rows = conn.execute(
            f"SELECT * FROM {logs_tbl} WHERE run_id = ? ORDER BY timestamp ASC",
            (run_id,)
        ).fetchall()

        # Tool ops logs for this tool
        tool_ops_rows = []
        if tool_id:
            tool_ops_rows = conn.execute(
                f"SELECT * FROM {logs_tbl} WHERE tool_id = ? AND log_tier = 'tool_ops' ORDER BY timestamp DESC LIMIT 40",
                (tool_id,)
            ).fetchall()

        conn.close()

        return JSONResponse({
            "run_id": run_id,
            "tool_id": tool_id,
            "run_metadata": run_dict,
            "raw_files": [dict(r) for r in raw_rows],
            "cleaned_files": [dict(r) for r in cleaned_rows],
            "action_logs": [dict(r) for r in action_log_rows],
            "tool_ops_logs": [dict(r) for r in tool_ops_rows],
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/index/prompt-history")
async def get_prompt_history(limit: int = 100):
    """
    Reads logs/global/antigravity_prompt_log.jsonl and extracts prompt execution
    milestones alongside Git commit hashes, stages, steps, timestamps, and status.
    """
    try:
        log_file = ROOT / "logs" / "global" / "antigravity_prompt_log.jsonl"
        records = []
        milestones = []

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        records.append(rec)
                        msg = rec.get("message", "")
                        if any(p in msg for p in ["[SCAFFOLD]", "[TOOL-INSTALL]", "[UPDATE]", "[FIX]", "[RUN-LOG]"]) or "Git commit:" in msg or "Stage" in msg or "Step" in msg:
                            git_commit = ""
                            if "Git commit:" in msg:
                                parts = msg.split("Git commit:")
                                if len(parts) > 1:
                                    git_commit = parts[1].split()[0].strip()
                            milestones.append({
                                "timestamp": rec.get("timestamp"),
                                "stage": rec.get("stage"),
                                "step": rec.get("step"),
                                "level": rec.get("level", "INFO"),
                                "message": msg,
                                "git_commit": git_commit or rec.get("git_commit", ""),
                                "progress_pct": rec.get("progress_percent") or rec.get("progress_pct"),
                            })
                    except Exception:
                        pass

        milestones_sorted = list(reversed(milestones))[:limit]
        recent_records = list(reversed(records))[:limit]

        return JSONResponse({
            "count": len(records),
            "milestones_count": len(milestones),
            "milestones": milestones_sorted,
            "prompt_logs": recent_records,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)




@app.post("/api/run-tool/{tool_id}")
async def trigger_tool_run(tool_id: str):
    """Trigger smoke test run for a specific tool in background thread."""
    adapter_file = ROOT / "tools" / tool_id / "adapter.py"
    if not adapter_file.exists():
        # Fall back to adapter_stub.py if adapter.py does not exist yet
        adapter_file = ROOT / "tools" / tool_id / "adapter_stub.py"
    if not adapter_file.exists():
        return JSONResponse({"error": f"Adapter not found for {tool_id}"}, status_code=404)

    def _worker():
        import subprocess
        env = dict(os.environ)
        env["OPENBLAS_NUM_THREADS"] = "1"
        env["MKL_NUM_THREADS"] = "1"
        subprocess.run(
            [sys.executable, str(adapter_file)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
        )

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return JSONResponse({
        "status": "started",
        "tool_id": tool_id,
        "message": f"Smoke test launched for {tool_id}. Watch HUD and logs.",
    })


@app.post("/api/demo-run")
async def trigger_demo_run():
    """
    Trigger a 10-second demo simulation in background thread.
    Simulates: 01_curl_cffi / scrape_for_leetcode with live state updates.
    """
    thread = threading.Thread(target=_demo_simulation, daemon=True)
    thread.start()
    return JSONResponse({"status": "demo_started", "message": "Demo simulation launched. Watch the HUD."})


# ─── Demo Simulation ──────────────────────────────────────────────────────────

def _demo_simulation():
    """Simulates a 5-step tool run over ~12 seconds with live state updates."""
    steps = [
        (10, "Initializing curl_cffi session"),
        (25, "Resolving DNS & TLS handshake"),
        (45, "Fetching LeetCode problem page"),
        (70, "Parsing HTML with selectolax"),
        (90, "Saving raw output to disk"),
        (100, "Cleaning & structuring data"),
    ]

    start_task(
        stage="Stage 1",
        step="Step 1.0 Demo",
        tool_id="01_curl_cffi",
        action="scrape_for_leetcode",
        subtask="Initializing demo simulation...",
    )

    run_info = create_action_run(
        tool_id="01_curl_cffi",
        action_name="scrape_for_leetcode",
        target_url="https://leetcode.com/problems/two-sum/",
    )

    # Write a demo raw file
    raw_path = Path(run_info["raw_dir"]) / "demo_response.html"
    raw_path.write_text(
        "<html><body><h1>LeetCode Demo — Two Sum</h1></body></html>",
        encoding="utf-8",
    )

    for pct, subtask in steps:
        time.sleep(2)
        update_progress(progress_percent=pct, subtask=subtask)

    complete_action_run(run_info, status="completed")
    complete_task(message="Demo simulation complete! Check data/01_curl_cffi/scrape_for_leetcode/")


# ─── WebSocket: Telemetry (1s push) ──────────────────────────────────────────

@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await telemetry_mgr.connect(ws)
    try:
        while True:
            state = read_state()
            if state.get("is_running") and state.get("started_at_epoch"):
                state["elapsed_seconds"] = round(
                    time.time() - state["started_at_epoch"], 1
                )
            await ws.send_text(json.dumps(state, default=str))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        telemetry_mgr.disconnect(ws)
    except Exception:
        telemetry_mgr.disconnect(ws)


# ─── WebSocket: Log Stream (watchdog) ────────────────────────────────────────

if _WATCHDOG_OK:
    class _LogHandler(FileSystemEventHandler):
        def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
            self._queue = queue
            self._loop = loop
            self._tails: dict[str, int] = {}
            scan_dir = ROOT / "logs"
            if scan_dir.exists():
                for p in scan_dir.rglob("*.jsonl"):
                    try:
                        self._tails[str(p)] = p.stat().st_size
                    except OSError:
                        pass

        def on_modified(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix not in (".jsonl",):
                return
            try:
                size = path.stat().st_size
                prev = self._tails.get(str(path), 0)
                if size <= prev:
                    return
                with path.open("r", encoding="utf-8", errors="replace") as f:
                    f.seek(prev)
                    new_content = f.read()
                self._tails[str(path)] = size

                for line in new_content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        record = {"raw": line}
                    record["_source_file"] = str(path.relative_to(ROOT))
                    asyncio.run_coroutine_threadsafe(
                        self._queue.put(record), self._loop
                    )
            except Exception:
                pass


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket):
    await log_mgr.connect(ws)
    loop = asyncio.get_event_loop()

    observer = None
    if _WATCHDOG_OK and (ROOT / "logs").exists():
        handler = _LogHandler(log_broadcast_queue, loop)
        observer = Observer()
        observer.schedule(handler, str(ROOT / "logs"), recursive=True)
        observer.start()

    try:
        while True:
            try:
                record = await asyncio.wait_for(log_broadcast_queue.get(), timeout=2.0)
                await ws.send_text(json.dumps(record, default=str))
            except asyncio.TimeoutError:
                # Send a heartbeat ping to keep connection alive
                try:
                    await ws.send_text(json.dumps({"type": "heartbeat", "ts": time.time()}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        log_mgr.disconnect(ws)
        if observer:
            observer.stop()
            observer.join(timeout=1)


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    # Ensure log dirs exist
    for d in [ROOT / "logs" / "global", ROOT / "logs" / "stages"]:
        d.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  [*] Crawlers_testing Control Center")
    print("  [>] http://127.0.0.1:8000")
    print("  [W] WebSocket Telemetry: ws://127.0.0.1:8000/ws/telemetry")
    print("  [W] WebSocket Logs:      ws://127.0.0.1:8000/ws/logs")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
