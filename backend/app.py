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
    if state.get("started_at_epoch"):
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
            if state.get("started_at_epoch"):
                state["elapsed_seconds"] = round(
                    time.time() - state["started_at_epoch"], 1
                )
            # Lightweight worker refresh every 5th tick
            if int(time.time()) % 5 == 0:
                state["worker_processes"] = refresh_workers()
                write_state(state)

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
    if _WATCHDOG_OK:
        handler = _LogHandler(log_broadcast_queue, loop)
        observer = Observer()
        observer.schedule(handler, str(ROOT / "logs"), recursive=True)
        observer.schedule(handler, str(ROOT / "data"), recursive=True)
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
