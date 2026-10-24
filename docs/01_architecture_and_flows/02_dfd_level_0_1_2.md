# Data Flow Diagrams (DFD) Specification: Level 0, Level 1 & Level 2
**Project:** `Crawlers_testing` | **Status:** Formal Data Flow Specification | **Stage:** Stage 3 Active

---

## 1. DFD Theoretical Framework & Data Dictionary

Data Flow Diagrams (DFDs) trace the algorithmic path that raw inputs, credentials, and telemetry travel through the `Crawlers_testing` system. Unlike physical network or process diagrams, DFDs formalize how data changes state, where data is buffered, and what transforms are applied at each boundary.

### 1.1 Data Dictionary Notation & Standards

The diagrams follow standard Gane-Sarson / Yourdon structured analysis notation:
- **External Entities (Square / Subgraph):** External human operators, AI agent runtimes, remote HTTP endpoints, or remote source control.
- **Processes (Circles / Rounded Rectangles $P_x$):** Discrete computational units transforming input data streams into output data streams.
- **Data Stores (Open Cylinders / Brackets $D_x$):** Persistent on-disk databases, state files, or memory buffers.
- **Data Flows (Directed Arrows):** Named, typed data payloads with defined access constraints.

```
+==================================================================================================+
|                                    MASTER DFD DATA DICTIONARY                                    |
+==================================================================================================+
| SYMBOL | NAME                         | TYPE / MEDIUM           | INTEGRITY & SECURITY POLICY    |
+--------+------------------------------+-------------------------+--------------------------------+
| E1     | Engineer / Operator          | Human Actor             | Browser UI Session (Tab 1–5)   |
| E2     | Antigravity AI Agent         | AI Developer Runtime    | CLI & JSON Governance Protocol |
| E3     | Target Web Servers / APIs    | Remote HTTP/HTTPS/WSS   | TLS/JA4 Impersonation / WAF    |
| E4     | Git Remote Repository        | Remote VCS              | Pre-Commit Secret Guard Scan   |
| D1     | live_state.json              | Memory-Mapped JSON      | Atomic Single-Writer Locks     |
| D2     | credentials_vault.sqlite     | SQLite (WAL Mode)       | AES-256-GCM Row Encryption     |
| D3     | Data Lake (Bronze/Silver)    | Hierarchical Filesystem | Run-UUID Atomic Isolation      |
| D4     | Per-Tool Indexes (*.sqlite)  | 20x SQLite Databases    | Dedicated Tool Schemas         |
| D5     | global_master_index.sqlite   | SQLite (FTS5 Enabled)   | Federated Token Search Engine  |
| D6     | 4-Tier Logs (JSONL/MD)       | Append-Only Text Files  | Multi-Tier Concurrent Flush    |
+==================================================================================================+
```

---

## 2. DFD Level 0 — Context Diagram

The Context Diagram defines the absolute system boundary of `Crawlers_testing`. It illustrates how the core platform mediates between human developers, the Antigravity AI pair programmer, remote web endpoints, and source control.

```mermaid
flowchart LR
    E1["External Entity: Engineer / User<br/>(Browser UI & CLI)"]
    E2["External Entity: Antigravity AI Agent<br/>(IDE / Pair Programmer)"]
    E3["External Entity: Target Web Servers & APIs<br/>(Target Platforms)"]
    E4["External Entity: Git Repository<br/>(origin/main)"]

    SYS(("Crawlers_testing<br/>Core System Platform"))

    E1 -->|"1. Web UI Actions & Tool Triggers<br/>2. Plaintext Credentials & Seeds<br/>3. Search Queries (FTS5 & Tools)"| SYS
    SYS -->|"1. Live Telemetry & 60 FPS HUD<br/>2. Masked Account Records & TOTP<br/>3. Cleaned Datasets & Logs"| E1

    E2 -->|"1. CLI Tracker Commands (start/complete)<br/>2. Governance Prompts & Refactors<br/>3. Verification Scripts"| SYS
    SYS -->|"1. live_state.json Telemetry<br/>2. Structured 4-Tier Logs<br/>3. Test Assertions & Status"| E2

    SYS -->|"1. Impersonated TLS Client Hello<br/>2. Authenticated Cookies & Nonces<br/>3. GraphQL & Scraping Requests"| E3
    E3 -->|"1. HTML / DOM / Streams / Binary Blobs<br/>2. HTTP Status & Rate-Limit Headers<br/>3. 2FA Checkpoint Challenges"| SYS

    SYS -->|"1. Clean Commits (Prefix-Tagged)<br/>2. Public Non-Sensitive Stats"| E4
    E4 -->|"1. Clean Branch & Upstream Code"| SYS
```

---

## 3. DFD Level 1 — Major System Subsystems

Level 1 decomposes the system into six core processes and six primary data stores.

```mermaid
flowchart TB
    E1["Engineer / UI"]
    E2["AI Agent / CLI"]
    E3["Target Servers"]
    E4["Git Remote"]

    P1["P1: Task & Telemetry Controller<br/>(core/state_tracker.py)"]
    P2["P2: Vault & Auth Router<br/>(core/account_router.py)"]
    P3["P3: 20-Tool Execution Engine<br/>(tools/01_... to 20_...)"]
    P4["P4: Data Isolation & Folder Factory<br/>(core/folder_manager.py)"]
    P5["P5: Dual-Tier Indexing & FTS5<br/>(core/global_indexer.py)"]
    P6["P6: 4-Tier Logging & Secret Guard<br/>(core/logger_engine.py & git_mgr)"]

    D1[("D1: live_state.json")]
    D2[("D2: credentials_vault.sqlite<br/>(AES-256-GCM)")]
    D3[("D3: Data Lake<br/>data/<tool>/<action>/...")]
    D4[("D4: Tool Indexes<br/>index_store/tool_indexes/")]
    D5[("D5: Global Master Index<br/>index_store/global_master_index")]
    D6[("D6: 4-Tier Logs<br/>logs/global/ & stages/")]

    %% P1 Flows
    E1 & E2 -->|"start / update / complete"| P1
    P1 <-->|"Read / Write State"| D1
    P1 -->|"Active Task Context"| P6

    %% P2 Flows
    E1 -->|"Add Account / Bulk Import"| P2
    P2 <-->|"AES Encrypted R/W"| D2
    P2 -->|"Leased Auth Context & Ephemeral Cookies"| P3
    P3 -->|"Report Outcome (cooldown/success)"| P2

    %% P3 Flows
    E1 -->|"Execute Tool Request"| P3
    P3 -->|"Impersonated Requests"| E3
    E3 -->|"Raw HTTP / DOM / Media"| P3
    P3 -->|"Raw Scraped Payloads"| P4

    %% P4 Flows
    P4 -->|"Allocate Run & Write raw/"| D3
    P4 -->|"Write Normalized cleaned/"| D3
    P4 -->|"Finalize run_manifest.json"| D3
    D3 -->|"Trigger Auto-Index Hook"| P5

    %% P5 Flows
    P5 <-->|"Extract Domain Metrics & Index"| D4
    P5 <-->|"Federate into FTS5 Virtual Tables"| D5
    E1 -->|"Search Query (Runs/Logs)"| P5
    P5 -->|"Paginated Search Results"| E1

    %% P6 Flows
    P1 & P2 & P3 & P4 & P5 -->|"Emit Structured Log Record"| P6
    P6 -->|"Append Sync"| D6
    D6 -->|"watchdog Log Stream"| E1
    P6 -->|"Pre-Commit Scan & Atomic Commit"| E4
```

---

## 4. DFD Level 2 — Granular Subsystem Decomposition

### 4.1 DFD Level 2.1 — Tool Scrape & Folder Creation Flow
This diagram details the atomic lifecycle of a scrape execution from URL ingestion to bronze/silver filesystem serialization.

```mermaid
flowchart TD
    InURL["Input: Target URL + Tool ID + Action Name + Payload"] --> P4_1["P4.1: Compute Run UUID & Timestamp<br/>(generate_run_id)"]
    P4_1 --> P4_2["P4.2: Allocate Directory Tree<br/>(data/<tool>/<action>/<date>/run_<id>/)"]
    
    P4_2 --> P4_3["P4.3: Create Subdirectories<br/>- raw/<br/>- cleaned/<br/>- logs/"]
    
    P4_3 --> P3_1["P3.1: Execute Tool Driver<br/>(CurlCffi, Playwright, Scrapy, etc.)"]
    
    P3_1 -->|"Raw Response Stream"| P4_4["P4.4: Write Bronze Layer<br/>(raw/response.html or raw/media.mp4)"]
    
    P4_4 --> P3_2["P3.2: Parser / Normalizer<br/>(Selectolax / Trafilatura / Cleaners)"]
    P3_2 -->|"Parsed Structured Objects"| P4_5["P4.5: Write Silver Layer<br/>(cleaned/data.json or cleaned/table.csv)"]
    
    P4_4 & P4_5 --> P4_6["P4.6: Calculate SHA-256 Hashes<br/>(File Integrity Checksums)"]
    P4_6 --> P4_7["P4.7: Assemble run_manifest.json<br/>- Tool ID, Action, Target URL<br/>- Timestamp & Duration<br/>- File Manifests with SHA-256<br/>- Git Commit Hash & Status"]
    
    P4_7 --> Done["On-Disk Isolated Run Directory Finalized"]
```

### 4.2 DFD Level 2.2 — Auto-Indexing & Master FTS5 Federation Flow
This diagram details how on-disk run artifacts are indexed into isolated per-tool SQLite databases and then federated into the global master FTS5 search index.

```mermaid
flowchart TD
    Trigger["Hook: complete_action_run()<br/>(Run Manifest Ready)"] --> P5_1["P5.1: Parse run_manifest.json<br/>(Metadata, file paths, SHA256)"]
    
    P5_1 --> P5_2["P5.2: Extract Domain Metrics<br/>(Custom parser for Tool ID)"]
    
    P5_2 -->|"Metrics Dict (status_code, latency, parsed_items)"| P5_3["P5.3: Update Tool SQLite<br/>(index_store/tool_indexes/<tool_id>.sqlite)"]
    P5_3 --> P5_4["P5.4: Refresh Tool JSON Mirror<br/>(index_store/tool_indexes/<tool_id>_index.json)"]
    
    P5_3 --> P5_5["P5.5: Global Master Index Hook<br/>(core/global_indexer.py)"]
    
    P5_5 --> P5_6["P5.6: Upsert Master Tables<br/>(runs, artifacts, tool_catalog)"]
    P5_5 --> P5_7["P5.7: Populate FTS5 Virtual Tables<br/>(fts_runs, fts_artifacts, fts_logs)"]
    
    P5_7 --> Ready["Searchable across GET /api/search<br/>Sub-millisecond BM25 Ranked Queries"]
```

### 4.3 DFD Level 2.3 — Credential Vault Encryption, Private-Target Routing & Auth Injection Flow
This diagram traces credentials from `.env` key derivation through AES-256-GCM encryption, private follower matching, ephemeral cookie deployment, and zero-fill shredding.

```mermaid
flowchart TD
    Env[".env: VAULT_MASTER_KEY + VAULT_KDF_SALT"] --> P2_1["P2.1: PBKDF2-HMAC-SHA256 Derivation<br/>(100,000 iterations -> 256-bit Key)"]
    
    RawCred["Raw Secret / Password / Cookie Jar / TOTP Seed"] --> P2_2["P2.2: AES-256-GCM Encryption<br/>- Generate 96-bit Random Nonce<br/>- Encrypt Plaintext -> Ciphertext<br/>- Compute 128-bit Authentication Tag"]
    P2_1 --> P2_2
    
    P2_2 -->|"Format: v1:aes256gcm:<nonce>:<tag>:<ciphertext>"| P2_3["P2.3: Store in credentials_vault.sqlite<br/>(WAL Mode + Foreign Key Constraints)"]
    
    Req["Request: Tool Needs Auth for Target @private_user"] --> P2_4["P2.4: AccountRouter Target Matcher<br/>SELECT * FROM vault_accounts a<br/>JOIN account_target_access t ON a.account_id = t.account_id<br/>WHERE t.target_handle = @private_user<br/>AND a.status = 'active' ORDER BY LRU"]
    
    P2_3 --> P2_4
    P2_4 --> P2_5["P2.5: Decrypt Auth Payload<br/>(Verify GCM Tag & Decrypt In-Memory)"]
    
    P2_5 --> P2_6["P2.6: RFC 6238 TOTP Engine<br/>(Generate Current 6-Digit 2FA Code)"]
    
    P2_5 --> P2_7["P2.7: Format Ephemeral Netscape Cookie File<br/>(vault_store/temp_cookies/ephemeral_*.cookies.txt)"]
    
    P2_7 --> P3["P3: Execute Tool with Ephemeral Cookie Path"]
    
    P3 -->|"Context Exit (finally:)"| P2_8["P2.8: Ephemeral Shredder<br/>1. Overwrite file with 0x00 bytes<br/>2. Flush OS disk cache<br/>3. Unlink file from filesystem"]
    
    P2_8 --> Zero["Zero Residual Plaintext on Storage"]
```

### 4.4 DFD Level 2.4 — 4-Tier Logging & Live Telemetry Streaming Flow
This diagram shows how execution diagnostics are written to four distinct log tiers and streamed to connected WebSockets in real time.

```mermaid
flowchart TD
    Event["Diagnostic Log Event<br/>(Level, Message, Stage, Step, Tool, RunID)"] --> P6_1["P6.1: LoggerEngine Dispatcher<br/>(core/logger_engine.py)"]
    
    P6_1 -->|"Format JSON Record"| P6_2["P6.2: Tier 1 - Global JSONL<br/>logs/global/antigravity_prompt_log.jsonl"]
    P6_1 -->|"Format Markdown Entry"| P6_3["P6.3: Tier 2 - Global Markdown<br/>logs/global/antigravity_prompt_log.md"]
    P6_1 -->|"Format Stage Record"| P6_4["P6.4: Tier 3 - Stage JSONL<br/>logs/stages/stage_<N>_<name>.jsonl"]
    P6_1 -->|"Format Action Record"| P6_5["P6.5: Tier 4 - Run JSONL<br/>data/<tool>/<action>/.../logs/action_run.jsonl"]
    
    P6_2 & P6_4 --> FileSys["Disk Storage Flush"]
    
    FileSys --> Watchdog["P6.6: File Watcher (watchdog)<br/>Tails active JSONL files asynchronously"]
    
    Watchdog --> WS_Hub["P6.7: FastAPI WebSocket Server<br/>(/ws/logs)"]
    
    WS_Hub --> UI_Tab4["Frontend: Tab 4 Log Explorer DOM<br/>(Real-Time Virtual Scrolling Grid)"]
```

### 4.5 DFD Level 2.5 — Safe Arena Multi-Crawler Execution with Anti-Ban Staggered Concurrency
This diagram traces how multiple candidate crawler tools are executed sequentially with statistical safety offsets on a single target URL to determine an objective winner.

```mermaid
flowchart TD
    Req["Request: Safe Arena Tournament<br/>(Target URL, Candidate Tools, Stagger Delay)"] --> P7_1["P7.1: Resolve Candidate Tools<br/>(tools/registry.json filtering)"]
    P7_1 --> P7_2["P7.2: Generate Report ID & Allocate Reports Dir<br/>(index_store/arena_reports/)"]
    
    P7_2 --> P7_3["P7.3: Concurrency Loop with Stagger Offset<br/>For each tool: compute human delay, pause, execute"]
    
    P7_3 -->|"Tool Iteration"| P7_4["P7.4: In-Process Execution with Telemetry<br/>Track: Latency ms, RSS RAM Delta MB, Peak CPU %"]
    P7_4 --> P7_5["P7.5: Data Extraction & Byte Sizing<br/>Raw Ingested Bytes vs. Cleaned Output Chars"]
    
    P7_5 --> P7_6["P7.6: Multi-Vector Scoring Engine<br/>Speed Score (35%) + Richness (30%) + Stealth (25%) + Memory (10%)"]
    
    P7_6 --> P7_7["P7.7: Rank Leaderboard & Assign Winner<br/>Compute winning rationale"]
    
    P7_7 --> P7_8["P7.8: Persist Arena Artifacts<br/>- index_store/arena_reports/*.json<br/>- index_store/arena_reports/*.md"]
    
    P7_8 --> ArenaDone["Tournament Completed<br/>Leaderboard Broadcast over /ws/telemetry"]
```

### 4.6 DFD Level 2.6 — Precision Task Router Predecessor-to-Successor Artifact Handoffs
This diagram traces how multi-stage pipelines pass intermediate artifacts dynamically from fetchers to content processors.

```mermaid
flowchart TD
    PlanReq["Task Router Plan: e.g. GraphQL -> Markdown Chunker"] --> P8_1["P8.1: Resolve Pipeline Stages<br/>Stage 1: 01_curl_cffi -> Stage 2: 16_crawl4ai"]
    
    P8_1 --> P8_2["P8.2: Execute Stage 1 (Fetcher)<br/>Fetch raw GraphQL payload with TLS JA4 impersonation"]
    
    P8_2 --> P8_3["P8.3: Write Stage 1 Artifacts<br/>data/.../run_stage1/raw/graphql_payload.json"]
    
    P8_3 --> P8_4["P8.4: Contextual Artifact Handoff Resolver<br/>Locate predecessor outputs matching input_artifact_keys"]
    
    P8_4 --> P8_5["P8.5: Ingest Artifacts into Stage 2 (Processor)<br/>Pass file paths to 16_crawl4ai / cleaning pipeline"]
    
    P8_5 --> P8_6["P8.6: Execute Semantic Chunking & CommonMark Normalization"]
    
    P8_6 --> P8_7["P8.7: Write Final Silver Artifacts<br/>data/.../run_stage2/cleaned/two_sum.md"]
    
    P8_7 --> P8_8["P8.8: Consolidate Pipeline Manifest<br/>index_store/pipeline_reports/*.json"]
```

### 4.7 DFD Level 2.7 — Pydantic Silver-Tier Normalization & SHA-256 Integrity Verification
This diagram details the Silver-Tier contract enforcement gateway validating transformed assets before filesystem persistence.

```mermaid
flowchart TD
    RawArtifact["Input: Raw Scraped Ingest / Parsed Intermediate Dictionary"] --> P9_1["P9.1: Match Target Silver Contract<br/>Markdown | CodeProblem | SocialMedia | Forensics | Multimodal"]
    
    P9_1 --> P9_2["P9.2: Normalization & Field Scrubbing<br/>Strip HTML tags, sanitize Unicode, compute word count & reading time"]
    
    P9_2 --> P9_3["P9.3: Pydantic Schema Validation Gate<br/>Contract.model_validate(payload)"]
    
    P9_3 -->|Validation Fails: ValidationError| P9_4["P9.4: Safe Fallback & Error Logger<br/>Log validation error to Tier 4; abort write to cleaned/"]
    
    P9_3 -->|Validation Passes| P9_5["P9.5: Serialize Dual Outputs<br/>1. JSON Export: model_dump_json(indent=2)<br/>2. CommonMark Export: YAML frontmatter + markdown body"]
    
    P9_5 --> P9_6["P9.6: Cryptographic Digest Calculation<br/>Compute SHA-256 hash of serialized files"]
    
    P9_6 --> P9_7["P9.7: Record Digest in run_manifest.json<br/>Update file catalog with sha256_short & byte count"]
    
    P9_7 --> SilverComplete["Silver Tier Certified Artifact Landed in cleaned/"]
```
