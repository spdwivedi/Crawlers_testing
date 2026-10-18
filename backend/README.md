# Backend Control Plane API & WebSocket Server (`backend/`)

The `backend/` directory hosts the FastAPI server providing REST endpoints, WebSocket telemetry feeds, and asynchronous task workers for the Antigravity Control Center.

---

## 🚀 Server Architecture

- **Engine:** FastAPI (Uvicorn ASGI runner on `127.0.0.1:8000`).
- **Telemetry Streaming:** `/ws/telemetry` broadcasts `logs/global/live_state.json` updates and `psutil` worker CPU/RAM consumption at 1 Hz.
- **Log Streaming:** `/ws/logs` tails `logs/global/*.jsonl` in real time using the OS-native kernel file notifications (`watchdog`).
- **Safe Threadpool Decoupling:** Long-running scraping tasks, video demuxing, and synchronous Playwright session recordings are delegated to worker threads via `asyncio.to_thread(...)`, preventing event-loop blocking.

---

## 📡 REST API Endpoint Catalog

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/state` | Returns active `live_state.json` telemetry, progress, and active workers |
| `GET` | `/api/tools` | Returns manifest of all 20 crawling engines and supported actions |
| `GET` | `/api/git-log` | Returns recent Git commits with stage/step tags and milestone flags |
| `GET` | `/api/data-tree` | Returns hierarchical directory tree of Bronze and Silver artifacts |
| `POST` | `/api/run-tool/{tool_id}` | Launches scraping execution with optional auth account routing |
| `GET` | `/api/tool-indexes` | Queries isolated tool SQLite databases (`index_store/tool_indexes/`) |
| `GET` | `/api/search` | Executes Okapi BM25 ranked full-text queries over `global_master_index.sqlite` |
| `GET` | `/api/vault/diagnostics` | Returns credential pool health metrics, quotas, and public non-sensitive stats |
| `GET` | `/api/vault/accounts` | Returns masked account inventory (zero plaintext passwords or raw cookies) |
| `POST` | `/api/vault/accounts` | Ingests or updates an encrypted account profile |
| `POST` | `/api/vault/bulk-import` | High-speed batch credential ingestion (Netscape, CSV, JSONL) |
| `POST` | `/api/vault/accounts/{id}/totp` | Generates live 6-digit 2FA TOTP code with time-remaining countdown |
| `POST` | `/api/vault/accounts/{id}/outcome`| Reports execution outcome to adjust health scores and cooldown quarantine |
| `POST` | `/api/vault/record-session` | Programmatic/interactive browser session recording into the encrypted vault |
| `POST` | `/api/vault/test-injection` | Tests 20-tool auth routing and verifies ephemeral cookie shredding |

---

## 🛠️ Launch Commands

```powershell
# Standard Execution
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Development Mode with Selective Reload (Prevents reload loops)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

For complete API documentation, refer to [docs/03_folder_and_file_reference/02_core_and_api_file_reference.md](../docs/03_folder_and_file_reference/02_core_and_api_file_reference.md).
