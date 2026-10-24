# End-to-End Process & Sequence Flows: Execution, Sessions, Auth & Concurrency
**Project:** `Crawlers_testing` | **Status:** Formal Sequence Specification | **Stage:** Stage 3 Active

---

## 1. Sequence Flow Theoretical Foundations

Sequence diagrams model the chronological exchange of synchronous and asynchronous messages between system lifelines. In `Crawlers_testing`, strict sequence sequencing ensures:
1. **Deterministic Session Scoping:** Authentication cookies and memory-mapped credentials exist exclusively for the lifespan of a tool invocation.
2. **Asynchronous Non-Blocking Execution:** Long-running scraping tasks, video demuxing, and headless browser processes never block the primary event loop.
3. **Deadlock-Free Windows Concurrency:** Windows filesystem locks on SQLite `.db` files and ephemeral `.txt` cookies are avoided through write-ahead logging (WAL), ephemeral context managers, and thread-pool delegators.

---

## 2. Sequence 1 — Full Lifecycle of a Tool Execution Triggered from Frontend Tab 2

This sequence illustrates the end-to-end execution of a scraping request initiated from the Web UI through the authentication, execution, indexing, and live telemetry layers.

### 2.1 Sequence 1 Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / UI (Tab 2)
    participant API as FastAPI Backend (:8000)
    participant Auth as AuthInjector (core/auth_injector.py)
    participant Router as AccountRouter (core/account_router.py)
    participant Tool as Tool Adapter (tools/01_... to 20_...)
    participant Target as External Target Server / WAF
    participant Folder as FolderManager (core/folder_manager.py)
    participant Indexer as BaseToolIndexer & MasterIndexer
    participant WS as WebSocket Hub (/ws/telemetry & /ws/logs)

    User->>API: POST /api/run-tool/{tool_id} {url, action, auth_strategy, target_handle}
    activate API
    API->>Folder: create_action_run(tool_id, action_name, url)
    activate Folder
    Folder-->>API: run_info {run_id, run_dir, raw_dir, cleaned_dir}
    deactivate Folder

    API->>Auth: with authenticated_session(tool_id, target_handle, strategy)
    activate Auth
    Auth->>Router: acquire_account(platform, required_target, strategy)
    activate Router
    Router-->>Auth: account_bundle {account_id, cookies, tokens, totp_code}
    deactivate Router

    Auth->>Auth: Write ephemeral_*.cookies.txt (Netscape format)
    Auth-->>API: Active Context {cookie_file, headers, session_tokens}

    API->>Tool: execute(url, payload, auth_context)
    activate Tool
    Tool->>WS: Broadcast Log: "Connecting with impersonated TLS..."
    Tool->>Target: HTTP/2 GET with JA4 Impersonated Handshake & Cookies
    activate Target
    Target-->>Tool: 200 OK (HTML Payload / Media Stream)
    deactivate Target

    Tool->>Folder: Write raw/response.html
    Tool->>Tool: Parse DOM / Extract Elements
    Tool->>Folder: Write cleaned/data.json
    Tool-->>API: Scrape Complete {status: "success", items_extracted: 142}
    deactivate Tool

    API->>Router: report_account_outcome(account_id, "success")
    Auth->>Auth: Overwrite ephemeral_*.cookies.txt with 0x00 & unlink
    deactivate Auth

    API->>Folder: complete_action_run(run_id, status="success")
    activate Folder
    Folder->>Indexer: index_single_run(run_dir)
    activate Indexer
    Indexer->>Indexer: Extract domain metrics & update <tool_id>.sqlite
    Indexer->>Indexer: Federate into global_master_index.sqlite FTS5
    Indexer-->>Folder: Indexing Complete
    deactivate Indexer
    Folder-->>API: Manifest Finalized & Indexed
    deactivate Folder

    API-->>User: 200 OK {run_id, status: "success", metrics, artifacts}
    deactivate API
    API->>WS: Broadcast Telemetry Update (Progress = 100%, State = Completed)
```

---

## 3. Sequence 2 — Interactive & Programmatic Browser Session Recording

This sequence traces how an engineer captures a live authenticated session (e.g., solving an Instagram or LeetCode 2FA challenge) and encrypts it directly into the vault without exposing plaintext credentials.

### 3.1 Sequence 2 Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / UI (Tab 5)
    participant API as FastAPI Backend (/api/vault/record-session)
    participant Thread as AsyncIO Threadpool (asyncio.to_thread)
    participant Rec as BrowserSessionRecorder
    participant PW as Playwright / Patchright Engine
    participant Target as Platform Login Page (e.g., Instagram)
    participant Crypto as CryptoEngine (core/crypto_engine.py)
    participant Vault as CredentialVault (credentials_vault.sqlite)

    User->>API: POST /api/vault/record-session {platform, login_url, interactive: true, wait: 45}
    activate API
    API->>Thread: Delegate to worker thread to prevent event-loop block
    activate Thread
    Thread->>Rec: record_browser_session(...)
    activate Rec

    Rec->>PW: Launch Chromium (headless=False if interactive)
    activate PW
    PW->>Target: Navigate to login_url
    activate Target
    Target-->>PW: Render Login Page & 2FA Form
    deactivate Target

    User->>PW: Manually Enters Password & Solves 2FA in Browser Window
    PW->>PW: Wait for wait_seconds or navigation to home feed

    Rec->>PW: context.cookies() -> Extract raw cookie dicts
    Rec->>PW: page.evaluate() -> Extract window.localStorage & sessionStorage
    Rec->>PW: Close Browser Context & Process
    deactivate PW

    Rec->>Rec: Parse Netscape tokens (csrftoken, sessionid, ds_user_id)
    Rec->>Crypto: encrypt_dict(cookie_jar) & encrypt_dict(session_tokens)
    activate Crypto
    Crypto->>Crypto: Generate 96-bit random nonce
    Crypto->>Crypto: AES-256-GCM authenticated encryption
    Crypto-->>Rec: v1:aes256gcm:<nonce>:<tag>:<ciphertext>
    deactivate Crypto

    Rec->>Vault: insert_account(platform, encrypted_cookies, encrypted_tokens, targets)
    activate Vault
    Vault->>Vault: Write to credentials_vault.sqlite (WAL Mode)
    Vault-->>Rec: account_id = "acc_insta_179232_..."
    deactivate Vault

    Rec-->>Thread: Session Summary {account_id, cookies_captured: 12, tokens: ["sessionid"]}
    deactivate Rec
    Thread-->>API: Worker Result Ready
    deactivate Thread
    API-->>User: 200 OK (Masked Summary, Zero Plaintext Secrets Exposed)
    deactivate API
```

---

## 4. Sequence 3 — Private-Target Follower Matching & Ephemeral Cookie Shredding

This sequence demonstrates how `AccountRouter` guarantees that private targets (e.g., private Instagram profiles or restricted corporate groups) are only crawled by accounts confirmed to follow them, followed by zero-residue cookie shredding.

### 4.1 Sequence 3 Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Tool as Scraping Tool / Runner
    participant Auth as AuthInjector (core/auth_injector.py)
    participant Router as AccountRouter (core/account_router.py)
    participant Vault as CredentialVault
    participant TOTP as TOTPHelper (core/totp_helper.py)
    participant Disk as Temp Filesystem (vault_store/temp_cookies/)

    Tool->>Auth: authenticated_session(tool_id="12_instaloader", required_target="@private_celebrity")
    activate Auth

    Auth->>Router: acquire_account(platform="instagram", required_target="@private_celebrity")
    activate Router
    Router->>Router: release_expired_cooldowns() -> Check for recovered accounts
    
    Router->>Vault: Query accounts JOIN account_target_access<br/>WHERE target_handle = '@private_celebrity'<br/>AND status = 'active'<br/>ORDER BY last_used_epoch ASC
    activate Vault
    Vault-->>Router: Eligible Account Record (acc_insta_4820)
    deactivate Vault

    Router->>Vault: get_account_decrypted(account_id)
    activate Vault
    Vault-->>Router: Decrypted Secrets {cookies, session_tokens, totp_seed}
    deactivate Vault

    opt Account Has 2FA TOTP Seed
        Router->>TOTP: generate_totp_code(secret=totp_seed)
        activate TOTP
        TOTP-->>Router: {code: "582914", time_remaining: 24, valid: true}
        deactivate TOTP
    end

    Router-->>Auth: Account Bundle {account_id, cookies, totp_code}
    deactivate Router

    Auth->>Disk: Open ephemeral_12_instaloader_run8421.cookies.txt
    activate Disk
    Auth->>Disk: Format cookies in standard Netscape tab-delimited format
    Disk-->>Auth: File written to disk
    deactivate Disk

    Auth-->>Tool: yield AuthContext(cookie_path=".../ephemeral_*.cookies.txt", totp="582914")
    
    activate Tool
    Tool->>Tool: Execute Instaloader CLI with --cookie-file argument
    Tool-->>Auth: Execution Block Concluded (or exception raised)
    deactivate Tool

    Auth->>Auth: Enter finally: Block (Guaranteed Cleanup)
    activate Auth
    Auth->>Disk: Open file in 'wb' binary overwrite mode
    activate Disk
    Auth->>Disk: Write b'\x00' * file_size (Zero-Fill Byte Shredding)
    Auth->>Disk: flush() + os.fsync() (Commit overwrite to physical storage)
    Auth->>Disk: os.remove() (Unlink file from filesystem)
    Disk-->>Auth: File completely erased
    deactivate Disk
    deactivate Auth
```

---

## 5. Sequence 4 — Background Process Architecture & Safe Concurrency Model

Scraping workflows involve long-running subprocesses, live streaming files, and continuous database telemetry. On Windows, file locking semantics (`ERROR_SHARING_VIOLATION`) can easily deadlock processes if concurrency is not designed defensively.

### 5.1 Architecture Concurrency Safeguards

1. **FastAPI Event Loop Decoupling (`asyncio.to_thread`):**
   FastAPI operates on an asynchronous `uvloop` / `asyncio` event loop. Synchronous, blocking operations (such as `sync_playwright` or database transactions taking $>5\text{ms}$) are delegated to Python's default thread pool via `await asyncio.to_thread(...)`. This prevents Playwright's `Sync API inside asyncio loop` runtime crash and ensures the web server responds to HUD polls at 60 FPS.
2. **SQLite Write-Ahead Logging (WAL Mode):**
   All system databases (`credentials_vault.sqlite`, `<tool_id>.sqlite`, `global_master_index.sqlite`) enforce:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA busy_timeout = 5000;
   PRAGMA foreign_keys = ON;
   ```
   Under WAL mode, readers never block writers, and writers never block readers. Concurrent HTTP requests from multiple browser tabs can read telemetry and account inventories while scrapers write run logs.
3. **Asynchronous File Tailing with `watchdog`:**
   Instead of polling files with sleep loops, the FastAPI backend uses the OS-native `ReadDirectoryChangesW` Windows API via the `watchdog` library. It streams newly appended JSONL lines across the `/ws/logs` WebSocket with less than 2ms latency.

### 5.2 Concurrency Architecture Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant UI as Browser Tab 1 / Tab 4
    participant MainLoop as FastAPI Main Event Loop (asyncio)
    participant ThreadPool as Background Threadpool (ThreadPoolExecutor)
    participant Scraper as Crawler Subprocess (python / ffmpeg)
    participant DiskLog as logs/global/antigravity_prompt_log.jsonl
    participant Watcher as Watchdog FileSystemEventHandler
    participant DB as SQLite Databases (WAL Mode)

    UI->>MainLoop: WebSocket Connect /ws/logs & /ws/telemetry
    MainLoop-->>UI: WebSocket Connected (Keep-Alive Ping 1s)

    UI->>MainLoop: POST /api/run-tool/11_yt_dlp_ffmpeg
    MainLoop->>ThreadPool: asyncio.to_thread(_execute_long_crawl)
    MainLoop-->>UI: HTTP 202 Accepted {status: "launched"}

    ThreadPool->>Scraper: Spawn Subprocess (yt-dlp --newline ...)
    activate Scraper

    loop While Scraping
        Scraper->>DiskLog: Append JSONL log record (Rule 2)
        Watcher->>DiskLog: Detect on_modified() event via OS kernel
        Watcher->>MainLoop: asyncio.run_coroutine_threadsafe(queue.put(record))
        MainLoop->>UI: WebSocket Message: {stream: "logs", data: record}
    end

    Scraper-->>ThreadPool: Process Exit Code 0
    deactivate Scraper

    ThreadPool->>DB: with conn: INSERT into runs & fts_runs (WAL Mode)
    activate DB
    DB-->>ThreadPool: Commit OK (No reader contention)
    deactivate DB

    ThreadPool-->>MainLoop: Task Completed
    MainLoop->>UI: WebSocket Telemetry: {progress: 100%, is_running: false}

---

## 6. Sequence 5 — Safe Arena Staggered Multi-Tool Concurrency Flow

The Safe Arena executes head-to-head multi-tool tournaments without triggering network bandwidth saturation or IP-level rate limits. It introduces deterministic staggered concurrency offsets between competing scraper engines.

```mermaid
sequenceDiagram
    autonumber
    participant Arena as SafeArenaRunner (core/arena_runner.py)
    participant Timer as HumanTimingEngine (core/human_timing.py)
    participant T1 as Scraper Engine 1 (01_curl_cffi)
    participant T2 as Scraper Engine 2 (04_httpx_parsel)
    participant T3 as Scraper Engine 3 (06_playwright)
    participant Watchdog as Auto-Kill Watchdog Thread
    participant Rep as Arena Report (index_store/arena_reports/)

    Arena->>Arena: Initialize Arena Tournament (Target: URL, Tools: [T1, T2, T3])
    Arena->>Watchdog: Spawn Watchdog (Hard Timeout: 30s)

    Arena->>T1: Launch Tool 1 (Offset: 0.0s)
    activate T1
    Arena->>Timer: Compute Stagger Offset (Gaussian: 1.2s ± 0.3s)
    Timer-->>Arena: Stagger Delay 1.25s
    Arena->>Arena: time.sleep(1.25)

    Arena->>T2: Launch Tool 2 (Offset: +1.25s)
    activate T2
    Arena->>Timer: Compute Stagger Offset (Gaussian: 1.2s ± 0.3s)
    Timer-->>Arena: Stagger Delay 1.18s
    Arena->>Arena: time.sleep(1.18)

    Arena->>T3: Launch Tool 3 (Offset: +2.43s)
    activate T3

    par Concurrent Execution & Metric Capture
        T1->>Arena: Return Results (Latency: 0.82s, RAM: 18MB, Bytes: 45KB)
        deactivate T1
    and
        T2->>Arena: Return Results (Latency: 0.94s, RAM: 22MB, Bytes: 48KB)
        deactivate T2
    and
        T3->>Arena: Return Results (Latency: 3.20s, RAM: 142MB, Bytes: 92KB)
        deactivate T3
    end

    Arena->>Watchdog: Cancel Watchdog (All tools finished cleanly)
    Arena->>Arena: Rank Tools by Composite Score (Speed, Yield, RAM)
    Arena->>Rep: Persist arena_<id>.json & arena_<id>.md
    Arena-->>Arena: Declare Winner (01_curl_cffi)
```

---

## 7. Sequence 6 — Precision Task Router & Multi-Stage Artifact Handoff Flow

When executing complex tasks, the `PrecisionTaskRouter` coordinates a primary scraper, evaluates extraction yield, falls back dynamically upon detection, and routes raw artifacts to downstream enrichment engines (OCR, Whisper, or Markdownify).

```mermaid
sequenceDiagram
    autonumber
    participant Router as PrecisionTaskRouter (core/task_router.py)
    participant Primary as Primary Tool (01_curl_cffi)
    participant Fallback as Fallback Tool (07_patchright)
    participant Pipe as CleaningPipeline (core/cleaning_pipeline.py)
    participant Enrich as Enrichment Tool (20_faster_whisper)
    participant Lake as Data Lake (Silver Tier)

    Router->>Router: Load Routing Plan for Task (e.g. social_video_harvest)
    Router->>Primary: Execute Primary Scraper (High Speed HTTP/TLS)
    activate Primary

    alt Primary Encounters Cloudflare / 403 Forbidden
        Primary-->>Router: Error: Cloudflare Challenge Detected
        deactivate Primary
        Router->>Router: Engage Fallback Routing Branch
        Router->>Fallback: Execute Stealth Browser (Patchright Undetected)
        activate Fallback
        Fallback-->>Router: Extraction Succeeded (Raw HTML + Video URL)
        deactivate Fallback
    else Primary Succeeds
        Primary-->>Router: Extraction Succeeded (Raw HTML + Video URL)
    end

    Router->>Enrich: Handoff Raw Audio/Video Stream (11_yt_dlp_ffmpeg)
    activate Enrich
    Enrich->>Enrich: Transcribe Audio via Whisper INT8
    Enrich-->>Router: Transcribed Text & Segment Timestamps
    deactivate Enrich

    Router->>Pipe: Validate Against CleanedSocialMediaContract
    activate Pipe
    Pipe-->>Router: Pydantic Validation Passed (Silver Tier Approved)
    deactivate Pipe

    Router->>Lake: Write silver_artifact.json & provenance metadata
    Router-->>Router: Task Complete with 100% Quality Assurance
```

---

## 8. Sequence 7 — Chaos Fault-Injection & Anti-Bot Resilience Loop Flow

The `ResilienceTester` spins up an ephemeral in-memory HTTP fault-injection server (`ChaosFaultServer`) to simulate hostile upstream environments and prove automated defensive recovery mechanisms.

```mermaid
sequenceDiagram
    autonumber
    participant Tester as ResilienceTester (core/resilience_tester.py)
    participant Server as ChaosFaultServer (Ephemeral HTTP Port)
    participant Tool as Tool Adapter Under Test (01_curl_cffi)
    participant Router as AccountRouter (core/account_router.py)
    participant Pipe as CleaningPipeline (core/cleaning_pipeline.py)

    Tester->>Server: Start Chaos Server (/fault/rate-limit, /fault/mutated-dom)
    activate Server

    rect rgb(40, 20, 20)
        note right of Tester: Scenario 1: HTTP 429 Rate Limiting & Cooldown Quarantine
        Tester->>Tool: Request /fault/rate-limit
        activate Tool
        Tool->>Server: HTTP GET /fault/rate-limit
        Server-->>Tool: HTTP 429 Too Many Requests (Retry-After: 2)
        Tool->>Tool: Catch 429 & Apply Exponential Backoff Jitter
        Tool->>Router: Flag Account as Quarantined (Cooldown Timer Engaged)
        Tool-->>Tester: Resilience Verified: Backoff + Quarantine Triggered
        deactivate Tool
    end

    rect rgb(20, 30, 40)
        note right of Tester: Scenario 2: Scrambled DOM & Semantic Relocation
        Tester->>Tool: Request /fault/mutated-dom
        activate Tool
        Tool->>Server: HTTP GET /fault/mutated-dom
        Server-->>Tool: HTML with Fuzzed CSS Classes (`.mutated_xyz_9981`)
        Tool->>Tool: Primary Selector Missed -> Trigger Semantic Fallback
        Tool->>Tool: Extract via `data-semantic="title"` and Header Heuristics
        Tool-->>Tester: Resilience Verified: Content Extracted Without IndexError
        deactivate Tool
    end

    rect rgb(20, 40, 20)
        note right of Tester: Scenario 3: Corrupted Schema Contract Fuzzing
        Tester->>Pipe: Inject Corrupted Payloads (Missing Required Fields)
        activate Pipe
        Pipe->>Pipe: Pydantic ValidationError Caught Cleanly
        Pipe->>Pipe: Apply Fallback Normalized Defaults
        Pipe-->>Tester: Resilience Verified: Zero Crashes, Safe Error Diagnostics
        deactivate Pipe
    end

    Tester->>Server: Shutdown Ephemeral Chaos Server
    deactivate Server
    Tester->>Tester: Compute Composite Resilience Index (e.g. 100.0/100)
    Tester-->>Tester: Persist resilience_<id>.json and .md Reports
```
```
