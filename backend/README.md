# Backend Control Plane API & WebSocket Server (`backend/`)

The `backend/` directory hosts the FastAPI server providing REST endpoints, WebSocket telemetry feeds, and asynchronous task workers for the Antigravity Control Center.

---

## 🚀 Server Architecture

- **Engine:** FastAPI (Uvicorn ASGI runner on `127.0.0.1:8000`).
- **Telemetry Streaming:** `/ws/telemetry` broadcasts `logs/global/live_state.json` updates and `psutil` worker CPU/RAM consumption at 1 Hz.
- **Log Streaming:** `/ws/logs` tails `logs/global/*.jsonl` in real time using the OS-native kernel file notifications (`watchdog`).
- **Safe Threadpool Decoupling:** Long-running scraping tasks, video demuxing, and synchronous Playwright session recordings are delegated to worker threads via `asyncio.to_thread(...)`, preventing event-loop blocking.

---

## 📡 REST API Endpoint Catalog (24+ Endpoints)

### 1. Core & Telemetry Endpoints
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/` | Serves the single-page Control Center dashboard (`frontend/index.html`) |
| `GET` | `/api/state` | Returns active `live_state.json` telemetry, progress, and active workers |
| `GET` | `/api/tools` | Returns manifest of all 20 crawling engines and supported actions |
| `GET` | `/api/git-log` | Returns recent Git commits with stage/step tags and milestone flags |
| `GET` | `/api/data-tree` | Returns hierarchical directory tree of Bronze and Silver artifacts |
| `GET` | `/api/run-manifest` | Retrieves a specific run manifest by path |
| `POST` | `/api/demo-run` | Launches a 10-second demo telemetry simulation |

### 2. Tool Execution & Search Federation
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/run-tool/{tool_id}` | Launches scraping execution with optional auth account routing |
| `GET` | `/api/tool-indexes` | Queries isolated tool SQLite databases (`index_store/tool_indexes/`) |
| `GET` | `/api/tool-indexes/{tool_id}` | Retrieves detailed runs and domain metrics for a specific engine |
| `GET` | `/api/search` | Executes Okapi BM25 ranked full-text queries over `global_master_index.sqlite` |

### 3. Encrypted Credential Vault & Auth Router
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/vault/diagnostics` | Returns credential pool health metrics, quotas, and public non-sensitive stats |
| `GET` | `/api/vault/accounts` | Returns masked account inventory (zero plaintext passwords or raw cookies) |
| `POST` | `/api/vault/accounts` | Ingests or updates an encrypted account profile |
| `POST` | `/api/vault/bulk-import` | High-speed batch credential ingestion (Netscape, CSV, JSONL) |
| `POST` | `/api/vault/accounts/{id}/totp` | Generates live 6-digit 2FA TOTP code with time-remaining countdown |
| `POST` | `/api/vault/accounts/{id}/outcome`| Reports execution outcome to adjust health scores and cooldown quarantine |
| `POST` | `/api/vault/record-session` | Programmatic/interactive browser session recording into the encrypted vault |
| `POST` | `/api/vault/test-injection` | Tests 20-tool auth routing and verifies ephemeral cookie shredding |

### 4. Working Ways (Safe Arena & Precision Task Router)
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/arena/run` | Launches head-to-head multi-tool tournament with staggered concurrency |
| `GET` | `/api/arena/reports` | Lists historical Safe Arena tournament evaluation reports |
| `GET` | `/api/arena/reports/{report_id}` | Retrieves full JSON & Markdown tournament report |
| `POST` | `/api/router/run` | Executes automated task plan with primary tool, fallbacks & enrichment handoffs |
| `GET` | `/api/router/plans` | Retrieves recommended routing templates for common scraping targets |
| `POST` | `/api/human/preview-delays` | Computes statistical neuromotor delay vectors for human simulation |

### 5. Production Task Pipelines
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/pipelines/leetcode/run` | Launches LeetCode Catalog, Specs & Starter Codes archiver |
| `POST` | `/api/pipelines/social/run` | Launches authenticated Reel downloader & Whisper speech transcriber |
| `POST` | `/api/pipelines/forensics/run` | Launches SingleFile offline snapshot & network wire origin forensics |
| `POST` | `/api/pipelines/multimodal/run` | Launches Multimodal Auto-Resolver (DOM text vs OCR vs Table vs PDF) |
| `GET` | `/api/pipelines/runs` | Returns catalog of executed production pipeline runs across all stages |
| `GET` | `/api/pipelines/stream/{pipeline_id}/{run_id}/{tier}/{filename}` | Securely streams pipeline raw and cleaned artifacts with MIME headers |

### 6. Master Benchmarks, Chaos Resilience & Project Exporter
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/benchmarks/overview` | Aggregated benchmark metrics (total runs, winner tool, fastest engine) |
| `GET` | `/api/benchmarks/reports` | Lists historical 20-tool benchmark battery reports |
| `GET` | `/api/benchmarks/reports/{report_id}` | Retrieves complete benchmark performance matrix (JSON & Markdown) |
| `POST` | `/api/benchmarks/run` | Executes multi-tool benchmark battery in background thread with HUD tracking |
| `GET` | `/api/resilience/overview` | Aggregated resilience metrics (resilience index, evaluations count) |
| `GET` | `/api/resilience/reports` | Lists historical chaos stress test reports |
| `GET` | `/api/resilience/reports/{report_id}` | Retrieves detailed chaos drill evaluation report |
| `POST` | `/api/resilience/run` | Dispatches chaos scenario (HTTP 429, DOM mutation, socket fault, schema fuzz) |
| `GET` | `/api/exports/list` | Returns catalog of standalone tools, data bundles, and pipeline packages |
| `POST` | `/api/exports/tool` | Packages scraper into zero-monorepo dependency runnable package |
| `POST` | `/api/exports/bundle` | Bundles Silver-tier data lake deliverables into signed ZIP archive |
| `POST` | `/api/exports/pipeline` | Creates containerized pipeline microservice with Dockerfile |
| `GET` | `/api/exports/download/{category}/{filename}` | Securely streams export archives with strict directory traversal guard |

---

## 🛠️ Launch Commands

```powershell
# Standard Execution
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Development Mode with Selective Reload (Prevents reload loops)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

For complete API documentation, refer to [docs/03_folder_and_file_reference/02_core_and_api_file_reference.md](../docs/03_folder_and_file_reference/02_core_and_api_file_reference.md).
