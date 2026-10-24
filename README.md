# 🕷️ Crawlers_testing: Enterprise Web Crawling, Anti-Bot Evasion & Multimodal Ingestion Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Stealth%20%26%20Patchright-45ba4b?logo=playwright&logoColor=white)](https://playwright.dev/)
[![SQLite FTS5](https://img.shields.io/badge/Search-SQLite%20FTS5%20(BM25)-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/fts5.html)
[![Cryptography](https://img.shields.io/badge/Security-AES--256--GCM%20%2B%20PBKDF2-red?logo=gnupg&logoColor=white)](https://cryptography.io/)
[![Zero Plaintext](https://img.shields.io/badge/Vault-Zero--Plaintext%20Enforced-brightgreen)](#-zero-plaintext-security--cryptographic-vault)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade, high-throughput web crawling, content harvesting, and multimodal extraction ecosystem engineered to defeat modern anti-bot protections (**Cloudflare Turnstile**, **Akamai Bot Manager**, **DataDome**, **PerimeterX**, and **AWS WAF**) while guaranteeing zero data loss, reproducible execution, and strict governance.

Unifies **20 specialized crawling engines** across **7 technical scraping paradigms**, orchestrated by a **FastAPI control plane**, real-time **4-tier telemetry**, dual-tier **SQLite FTS5 search indexing**, and an **AES-256-GCM encrypted credential vault** with RFC 6238 2FA TOTP generation and zero-fill cookie shredding.

---

## 🏛️ System Architecture

The platform operates across six strictly bounded horizontal tiers:

```mermaid
flowchart TB
    subgraph L1["Layer 1: Presentation & Telemetry HUD (8 Dashboard Tabs)"]
        UI_Tab1["Tab 1: Real-Time Stream & Live HUD"]
        UI_Tab2["Tab 2: Universal Tool Runner"]
        UI_Tab3["Tab 3: Data Lake Inspector"]
        UI_Tab4["Tab 4: Master FTS5 Search & Log Explorer"]
        UI_Tab5["Tab 5: 🔐 Encrypted Credential Vault & Auth Router"]
        UI_Tab6["Tab 6: ⚙ Working Ways & Safe Arena Studio"]
        UI_Tab7["Tab 7: 🧪 Real Task Pipelines & Cleaned Inspector"]
        UI_Tab8["Tab 8: 📊 Master Benchmarks, Chaos Lab & Exporter"]
        WS_Client["WebSocket Handlers (/ws/telemetry, /ws/logs)"]
    end

    subgraph L2["Layer 2: API & Control Plane (FastAPI :8000 / :8001)"]
        API_Router["FastAPI Application Router (24+ REST Endpoints)"]
        WS_Hub["Async WebSocket Hub & File Watcher (watchdog)"]
        Tool_Endpoints["POST /api/run-tool/{tool_id}"]
        Search_Endpoints["GET /api/search & GET /api/tool-indexes"]
        Vault_Endpoints["GET /api/vault/* & POST /api/vault/*"]
        Ways_Endpoints["POST /api/arena/run, /api/router/run, /api/human/*"]
        Pipe_Endpoints["POST /api/pipelines/*/run & GET /api/pipelines/stream/*"]
        Bench_Endpoints["GET & POST /api/benchmarks/*, /api/resilience/*, /api/exports/*"]
    end

    subgraph L3["Layer 3: Core Orchestration, Working Ways & Governance"]
        StateTracker["core/state_tracker.py & cli_tracker.py (Telemetry HUD)"]
        FolderManager["core/folder_manager.py (Strict Data Isolation)"]
        LoggerEngine["core/logger_engine.py (4-Tier Log Dispatcher)"]
        GitManager["core/git_manager.py (Pre-Commit Secret Guard)"]
        HumanTiming["core/human_timing.py & human_interaction.py (Kinematics)"]
        SafeArena["core/arena_runner.py (Staggered Concurrency)"]
        TaskRouter["core/task_router.py (Precision Chaining & Handoffs)"]
        CleanPipeline["core/cleaning_pipeline.py (Silver Tier Contract Engine)"]
        BenchEngine["core/benchmark_engine.py (Performance Matrix Engine)"]
        ChaosTester["core/resilience_tester.py (Chaos Fault Server)"]
        ProjExporter["core/project_exporter.py (Zero-Leak Standalone Packager)"]
    end

    subgraph L4["Layer 4: Security & Authentication Layer"]
        CryptoEngine["core/crypto_engine.py (AES-256-GCM + PBKDF2)"]
        CredVault["core/credential_vault.py (Encrypted SQLite WAL)"]
        AccountRouter["core/account_router.py (Target Match & Quotas)"]
        AuthInjector["core/auth_injector.py (Zero-Fill Ephemeral Shredder)"]
        TOTPHelper["core/totp_helper.py (RFC 6238 2FA Engine)"]
        SessionRecorder["core/browser_session_recorder.py (Playwright/Patchright)"]
    end

    subgraph L5["Layer 5: Extraction & Production Pipelines"]
        Tools20["20 Specialized Engines (P1: TLS/JA4 to P7: Multimodal AI)"]
        Pipe1["Pipeline 1: LeetCode Archiver (01_curl_cffi + Markdownify)"]
        Pipe2["Pipeline 2: Authenticated Reel & Whisper Transcription"]
        Pipe3["Pipeline 3: Secured Snapshot & Wire Forensics"]
        Pipe4["Pipeline 4: Multimodal Auto-Resolver (DOM vs OCR vs Table vs PDF)"]
    end

    subgraph L6["Layer 6: Storage, Search Federation & Exports"]
        DataLake["data/<tool_id>/<action>/<date>/<run_id>/ (raw/, cleaned/, manifest)"]
        ToolIndexes["index_store/tool_indexes/<tool_id>.sqlite & .json (20 Tools)"]
        MasterFTS5["index_store/global_master_index.sqlite (FTS5 Federated Search)"]
        ReportsDir["index_store/{arena,pipeline,benchmark,resilience}_reports/"]
        VaultDB["vault_store/credentials_vault.sqlite (AES Encrypted)"]
        ExportsDir["exports/{standalone_tools,data_bundles,pipeline_packages}/"]
        LogsTier["logs/global/ & logs/stages/ (4-Tier JSONL/MD)"]
    end

    L1 <-->|HTTP REST & WebSockets| L2
    L2 --> L3
    L2 --> L4
    L3 --> L5
    L4 -->|Injects Ephemeral Auth| L5
    L5 -->|Outputs Bronze/Silver Artifacts| DataLake
    DataLake -->|Triggers Auto-Indexing| ToolIndexes
    ToolIndexes -->|Federates Runs & Artifacts| MasterFTS5
    L3 -->|Generates Reports & Benchmarks| ReportsDir
    L3 -->|Produces Zero-Leak Standalone Packages| ExportsDir
    L3 -->|Emits Structured 4-Tier Logs| LogsTier
    LogsTier -->|watchdog stream| WS_Hub
    L4 <-->|Encrypted Read/Write| VaultDB
```

---

## 🛠️ Master 20-Tool Capabilities Matrix

The platform integrates 20 specialized tools organized across four batch cohorts:

| ID | Tool Name | Batch | Paradigm / Mechanism | Primary Dependency | Key Capabilities & Primary Use Case |
|:--:|:---|:---:|:---|:---|:---|
| **01** | `01_curl_cffi` | 1 | HTTP / TLS Impersonation | `curl_cffi` (BoringSSL) | Bypasses Cloudflare JA3/JA4 TLS fingerprinting & HTTP/2 frame ordering |
| **02** | `02_selectolax_lxml` | 1 | C-Engine DOM Slicers | `selectolax` (Modest C) | Ultra-fast HTML parsing (10k+ pages/sec) avoiding Python object allocations |
| **03** | `03_scrapy` | 1 | Industrial Framework | `scrapy` (Twisted) | Concurrent sitemap and catalog crawls with built-in item pipelines |
| **04** | `04_httpx_parsel` | 1 | Async HTTP/2 + Selectors | `httpx` + `parsel` | High-concurrency async API harvesting with Scrapy-grade CSS/XPath |
| **05** | `05_trafilatura` | 1 | Content & Boilerplate Slicer | `trafilatura` | Density-based editorial text extraction, stripping ads and cookie notices |
| **06** | `06_playwright` | 2 | Standard Browser Automation | `playwright` (Chromium) | Full JavaScript SPA rendering, synthetic user input, and HAR network traces |
| **07** | `07_patchright` | 2 | C++ Patched Stealth Browser | `patchright` | Unhooks `window.cdc_*` and CDP leaks at binary compilation level |
| **08** | `08_camoufox` | 2 | Firefox Anti-Detect Engine | `camoufox` | Randomizes canvas noise, WebGL renderers, and OS fonts per execution run |
| **09** | `09_nodriver` | 2 | Raw CDP WebSocket Engine | `nodriver` | Eliminates webdriver binaries; communicates via raw WebSocket frames |
| **10** | `10_scrapling` | 2 | Adaptive Heuristic Relocator | `scrapling` | Auto-heals broken selectors via semantic graph distance when CSS classes churn |
| **11** | `11_yt_dlp_ffmpeg` | 3 | Stream Demuxer & Transcoder | `yt-dlp` + `ffmpeg` | Demuxes HLS (`.m3u8`) and DASH (`.mpd`) video streams from 1,000+ sites |
| **12** | `12_instaloader` | 3 | Social Graph Archiver | `instaloader` | Interfaces with Instagram GraphQL endpoints to harvest posts, reels, and stories |
| **13** | `13_gallery_dl` | 3 | Multi-Platform Image Archiver | `gallery-dl` | Bulk media downloader for 200+ visual communities (Reddit, Pinterest, Twitter) |
| **14** | `14_singlefile_archive` | 3 | Offline Page Bundler | `single-file-cli` | Inlines all fonts, CSS, and images into Base64 for immutable legal/forensic HTML |
| **15** | `15_mitmproxy_interceptor`| 3 | Deep Wire TLS Interceptor | `mitmproxy` | In-memory TLS proxy intercepting hidden XHR/GraphQL streams before DOM rendering |
| **16** | `16_crawl4ai` | 4 | AI/LLM-Optimized Extractor | `crawl4ai` | Converts web pages into token-efficient, LLM-ready clean Markdown chunks |
| **17** | `17_surya_ocr` | 4 | Multilingual Document OCR | `surya-ocr` (PyTorch) | 90+ language OCR with reading-order detection and document layout analysis |
| **18** | `18_paddleocr_img2table` | 4 | Table Grid Extractor | `paddleocr` + `img2table` | Detects cell boundaries in raster images and converts balance sheets into CSV/Excel |
| **19** | `19_docling_pdf` | 4 | IBM Document Layout Parser | `docling` | Parses complex multi-column PDFs, footnotes, and formulas into structured JSON |
| **20** | `20_faster_whisper_scrapegraph` | 4 | Audio Transcription & Graph | `faster-whisper` + graph | 4x faster local Whisper speech-to-text + ScrapeGraph knowledge graph synthesis |

---

## 🖥️ Antigravity Control Center Dashboard

The platform includes a responsive, dark-mode single-page application hosted directly on `http://127.0.0.1:8000` (or `:8001` fallback):

```
+===================================================================================================================+
|  HUD BAR: [Stage: Master Verification]  [Step: Final Audit]  [Elapsed: 14.2s]  [Prog: 100%]  [Workers: 4]         |
|  Canvas CPU Monitor: [||||||||||  12%]      Canvas RAM Monitor: [||||||||||||||||  196 MB]                        |
+===================================================================================================================+
| [Tab 1: Telemetry] [Tab 2: Tools] [Tab 3: Explorer] [Tab 4: Search] [Tab 5: Vault]                              |
| [Tab 6: ⚙ Working Ways] [Tab 7: 🧪 Real Pipelines] [Tab 8: 📊 Benchmarks & Exporter]                            |
+===================================================================================================================+
```

- **Top Sticky HUD Bar:** Real-time 60 FPS Canvas displays showing active task, subtask, elapsed seconds, worker PIDs, and active CPU/RAM consumption.
- **Tab 1: Telemetry Dashboard & Worker Monitor:** Visual timeline of execution milestones, process tree inspection, and system health dials.
- **Tab 2: 20-Tool Universal Execution Hub:** Parameter configuration panels for all 20 engines with live JSON response inspectors.
- **Tab 3: Data Lake Inspector:** Hierarchical filesystem browser for inspecting Bronze (`raw/`), Silver (`cleaned/`), and provenance manifests (`run_manifest.json`).
- **Tab 4: Master FTS5 Search & Log Explorer:** Okapi BM25 ranked full-text queries over `global_master_index.sqlite` and virtual-scrolling live 4-tier log stream (`/ws/logs`).
- **Tab 5: 🔐 Encrypted Credential Vault & Auth Router:** Encrypted account inventory, 6-card KPI ribbon, private-target follower coverage matrix, on-demand RFC 6238 2FA TOTP generator, 50-account bulk seed importer, and 20-tool auth injection sandbox.
- **Tab 6: ⚙ Working Ways & Safe Arena Studio:**
  - *Human Simulation Studio:* Interactive neuromotor delays, Gaussian reaction times, and cubic Bezier mouse kinematics.
  - *Safe Arena Studio:* Head-to-head multi-tool benchmark arena with staggered start offsets, auto-kill timeouts, and resource monitoring.
  - *Precision Task Router Studio:* Automated routing matrix chaining primary, fallback, and enrichment tools into multi-stage pipelines.
- **Tab 7: 🧪 Real Task Pipelines & Cleaned Inspector:**
  - Dedicated control planes for the 4 Production Pipelines: **LeetCode Archiver**, **Social Media & Whisper**, **Secured Snapshot Forensics**, and **Multimodal Auto-Resolver**.
  - Silver-Tier Data Lake Inspector streaming raw/cleaned artifacts (HTML, Markdown, Audio, Code, Forensics JSON).
  - Pydantic schema validation contract compliance matrix.
- **Tab 8: 📊 Master Benchmarks, Chaos Lab & Standalone Exporter:**
  - *Master Benchmark Lab:* 20-tool tournament battery execution, radar multi-vector chart (Speed, Richness, Stealth, Memory, Reliability), and gold winner leaderboard.
  - *Chaos & Resilience Stress Lab:* Fault-injection testing against HTTP 429 rate limits, scrambled DOM mutations, socket resets, and contract fuzzing.
  - *Standalone Project Exporter:* Zero-monorepo dependency tool packaging, cryptographically signed Data Lake bundling (`.zip`), and containerized Dockerfile generation.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Version 3.11, 3.12, or 3.14.
- **Git:** Installed and on system PATH.

### 2. Clone & Environment Setup
```powershell
# Clone repository
git clone https://github.com/<your-username>/Crawlers_testing.git
cd Crawlers_testing

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate     # On Linux / macOS

# Install core dependencies
pip install -r requirements.txt

# Install browser automation binaries
playwright install chromium
patchright install chromium
```

### 3. Automatic Master Key Initialization
The cryptographic engine auto-initializes upon first execution:
- Generates a cryptographically secure 256-bit `VAULT_MASTER_KEY` and 128-bit `VAULT_KDF_SALT`.
- Persists secrets to `.env` (strictly ignored by Git).
- Creates a safe `.env.example` template with placeholder keys for team collaboration.

### 4. Launching the Control Center Dashboard
```powershell
# Launch FastAPI Control Plane & Telemetry Server (:8000 or :8001)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or `http://127.0.0.1:8001`).

### 5. Running Production Workloads from the CLI

#### A. Execute Safe Arena Multi-Tool Tournament
```powershell
.\.venv\Scripts\python.exe core/arena_runner.py --tools 01_curl_cffi,04_httpx_parsel,06_playwright --url "https://quotes.toscrape.com"
```

#### B. Execute Production Task Pipeline 1 (LeetCode Archiver)
```powershell
.\.venv\Scripts\python.exe pipelines/01_leetcode_archiver.py --slug "two-sum" --human-mode
```

#### C. Run Master 20-Tool Performance Benchmark Battery
```powershell
.\.venv\Scripts\python.exe core/benchmark_engine.py --tools 01_curl_cffi,04_httpx_parsel --iterations 3 --url "https://quotes.toscrape.com"
```

#### D. Run Chaos & Anti-Bot Fault-Injection Drills
```powershell
.\.venv\Scripts\python.exe core/resilience_tester.py --full-battery
```

#### E. Export Standalone Scraper Package or Data Lake Bundle
```powershell
# Package 01_curl_cffi into a zero-monorepo dependency standalone project
.\.venv\Scripts\python.exe -c "from core.project_exporter import get_project_exporter; get_project_exporter().export_standalone_tool('01_curl_cffi', output_format='both')"

# Bundle Silver-Tier Cleaned Data Lake into a signed ZIP
.\.venv\Scripts\python.exe -c "from core.project_exporter import get_project_exporter; get_project_exporter().bundle_data_lake(scope='cleaned')"
```

#### F. Run Master System Regression Verification Suite
```powershell
.\.venv\Scripts\python.exe core/verify_master_system.py
```

---

## 🔒 Zero-Plaintext Security & Cryptographic Vault

`Crawlers_testing` implements military-grade credential protection:

1. **AES-256-GCM + PBKDF2 (600,000 iterations):** All passwords, cookies, tokens, and 2FA seeds are encrypted with a 256-bit symmetric key derived via PBKDF2-HMAC-SHA256 (OWASP recommended baseline against GPU brute-force).
2. **Row-Binding Cryptographic Proof:** Every encryption call binds the ciphertext to its specific `account_id` via Associated Data (AD). If an attacker attempts to copy ciphertext between rows in the database, decryption immediately fails with `ValueError: GCM tag mismatch`, preventing row-swapping injection attacks.
3. **Blind Index Hashing:** Account deduplication is performed in $O(1)$ time via deterministic HMAC-SHA256 hashes ($\text{BlindHash} = \text{HMAC}(Key, \text{platform} \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{username})$) without storing plaintext usernames.
4. **Ephemeral Cookie Shredding:** Tools requiring physical Netscape `.cookies.txt` files receive dynamically generated temporary files. Upon context exit, `AuthInjector` overwrites the file bytes with `0x00`, flushes the disk cache via `os.fsync()`, and unlinks the file, leaving zero forensic trace on physical media.
5. **Git Pre-Commit Secret Guard:** Automated scanner in `core/git_manager.py` inspects staged files before every Git commit, intercepting `.env`, `*.sqlite`, raw cipher tokens (`v1:aes256gcm:`), and private keys.

---

## 📖 Documentation Ecosystem

Comprehensive, textbook-grade documentation is maintained in [`docs/`](docs/):

```
docs/
├── 01_architecture_and_flows/
│   ├── 01_system_architecture_overview.md   # 6-Layer Architecture & 7 Scraping Paradigms
│   ├── 02_dfd_level_0_1_2.md                # Context, Subsystem & Granular Level 2 DFDs
│   ├── 03_state_diagrams.md                 # Telemetry, Account Quarantine & Run FSMs
│   └── 04_process_and_sequence_flows.md     # Safe Arena, Pipeline Handoff & Chaos Sequences
├── 02_database_and_security/
│   ├── 01_database_schemas_and_er_diagrams.md# Two-Tier Topology, PRAGMAs & Report Repositories
│   ├── 02_fts5_search_and_indexing_specification.md # Inverted Index, Unicode61 & BM25 Math
│   └── 03_cryptography_and_zero_leak_security_spec.md # AES-GCM Row-Binding Proofs & TOTP
├── 03_folder_and_file_reference/
│   ├── 01_folder_structure_and_data_taxonomy.md # Bronze/Silver/Gold & Manifest Contracts
│   ├── 02_core_and_api_file_reference.md    # 21 Core Classes, 24+ REST APIs & WebSockets
│   └── 03_20_tools_adapter_catalog.md       # 20-Row Matrix & 20 Deep-Dive Profiles
└── 04_operations_and_guides/
    ├── 01_developer_operations_and_runbook.md # Safe Arena, Benchmarks, Chaos Drills & Ops
    ├── 02_troubleshooting_and_resilience_guide.md # Windows File Locks & Anti-Bot Recovery
    └── 03_documentation_master_index.md     # Cross-Referenced Knowledge Index & Graph
```

---

## 📜 Mandatory Antigravity Governance Protocol

Development in this repository is strictly regulated by the **9 Antigravity Governance Rules** specified in [`GEMINI.md`](GEMINI.md):
- **Rule 1 (Live State Telemetry):** Every task must register start/update/complete state in `logs/global/live_state.json` via `core/cli_tracker.py`.
- **Rule 2 (4-Tier Logging):** Every diagnostic event is appended to all four log tiers simultaneously via `core/logger_engine.py` (Global JSONL, Global MD, Stage Log, Action Run Log).
- **Rule 3 (Strict Data Isolation):** All scrape output is strictly isolated into `data/<tool>/<action>/<date>/run_<id>/` containing `raw/`, `cleaned/`, `logs/`, and `run_manifest.json`.
- **Rule 4 (Atomic Git Commits):** Every development action concludes with a categorized Git commit (`[SCAFFOLD]`, `[TOOL-INSTALL]`, `[UPDATE]`, `[FIX]`, `[RUN-LOG]`, `[DOCS]`).
- **Rule 5 (Auto-Indexing):** Completing an action run automatically updates `<tool_id>.sqlite` and federates records into `global_master_index.sqlite` (FTS5).
- **Rule 6 (Zero-Plaintext Security):** Plaintext credentials, `.env`, and `vault_store/*.sqlite*` must never be logged or committed to Git.
- **Rule 7 (Human Simulation & Timing Discipline):** Pacing delays follow `core/human_timing.py` statistical distributions (Gaussian, Log-Normal, Exponential Backoff Jitter).
- **Rule 8 (Data Lake Silver Tier Contract Enforcement):** All transformed files saved into `cleaned/` must strictly validate against Pydantic schema contracts in `core/cleaning_pipeline.py`.
- **Rule 9 (Benchmark Traceability & Non-Destructive Testing):** All benchmark and chaos runs must record reproducible telemetry (p50/p90/p99, RAM delta, CPU %, yield, stealth) into structured reports.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
