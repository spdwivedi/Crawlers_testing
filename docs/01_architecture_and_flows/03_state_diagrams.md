# Formal State Machine Reference: Telemetry, Accounts, Runs & Index Synchronization
**Project:** `Crawlers_testing` | **Status:** Formal State Machine Specification | **Stage:** Stage 3 Active

---

## 1. State Machine Theoretical Model

In distributed crawling and automated security systems, race conditions and inconsistent states lead to account bans, corrupted datasets, and ghost processes. `Crawlers_testing` implements a deterministic Finite State Machine (FSM) model across its four primary operational vectors:

$$M = (S, \Sigma, \delta, s_0, F)$$

Where:
- $S$ is the set of valid states.
- $\Sigma$ is the alphabet of trigger events (HTTP responses, CLI tracker calls, cron ticks).
- $\delta: S \times \Sigma \rightarrow S$ is the state transition function governed by explicit guard predicates.
- $s_0 \in S$ is the initial state.
- $F \subseteq S$ is the set of terminal (accepting) states.

---

## 2. Global Telemetry & HUD Task State Machine (`live_state.json`)

The Global Telemetry state machine governs the live execution status recorded in `logs/global/live_state.json` and mirrored in the real-time HUD on frontend Tab 1.

### 2.1 State Transition Table

```
+========================================================================================================================+
| CURRENT STATE       | EVENT / TRIGGER              | GUARD CONDITION              | ACTION                | NEXT STATE  |
+---------------------+------------------------------+------------------------------+-----------------------+-------------+
| IDLE                | cli_tracker.py start         | CLI arguments validated      | Write live_state.json | INITIALIZING|
| INITIALIZING        | Worker process spawned       | PID registered with psutil   | Start elapsed timer   | RUNNING     |
| RUNNING             | cli_tracker.py update        | 0 <= progress < 100          | Update progress %     | RUNNING     |
| RUNNING             | Tool scraper sub-step done   | Subtask string provided      | Append recent_events  | RUNNING     |
| RUNNING             | Unhandled Exception / crash  | Exception caught or SIGINT   | Record fail reason    | FAILED      |
| RUNNING             | cli_tracker.py complete      | Subtasks complete            | progress = 100%       | COMPLETING  |
| COMPLETING          | Flush logs & close sockets   | Filesystem sync complete     | is_running = false    | COMPLETED   |
| COMPLETED           | Next task start              | Previous task was completed  | Reset timers & arrays | INITIALIZING|
| FAILED              | Next task start              | User acknowledgment / retry  | Clean error flags     | INITIALIZING|
+========================================================================================================================+
```

### 2.2 Telemetry State Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> IDLE : System Boot

    IDLE --> INITIALIZING : cli_tracker.py start<br/>[stage, step, tool, action]
    
    state INITIALIZING {
        [*] --> Spawn_Worker
        Spawn_Worker --> Register_PID : psutil scans active PIDs
        Register_PID --> Init_Timers : started_at_epoch set
    }

    INITIALIZING --> RUNNING_SUBTASK : is_running = true

    state RUNNING_SUBTASK {
        [*] --> Executing_Step
        Executing_Step --> Updating_Progress : cli_tracker.py update<br/>[progress: 0% -> 99%]
        Updating_Progress --> Executing_Step : Heartbeat tick (1 Hz)
    }

    RUNNING_SUBTASK --> COMPLETING : cli_tracker.py complete<br/>[all subtasks pass]
    RUNNING_SUBTASK --> FAILED : cli_tracker.py fail<br/>[error / timeout / exception]

    state COMPLETING {
        [*] --> Set_Progress_100
        Set_Progress_100 --> Flush_4Tier_Logs
        Flush_4Tier_Logs --> Clear_IsRunning : is_running = false
    }

    COMPLETING --> COMPLETED : State serialized to disk
    COMPLETED --> INITIALIZING : New task initiated
    FAILED --> INITIALIZING : Retry / Remediation task initiated
```

---

## 3. Credential Vault Account Lifecycle & Quarantine State Machine

The account lifecycle state machine manages credential health, authentication states, rate-limit cooldowns, and anti-bot quarantine in `vault_store/credentials_vault.sqlite`.

### 3.1 State Transition Table

```
+=============================================================================================================================+
| CURRENT STATE       | EVENT / TRIGGER              | GUARD CONDITION              | ACTION                     | NEXT STATE  |
+---------------------+------------------------------+------------------------------+----------------------------+-------------+
| PROVISIONED         | Initial Import (Netscape/CSV)| Credentials encrypted        | Calculate initial health   | ACTIVE_READY|
| ACTIVE_READY        | Lease Requested              | Status == 'active' & Not Exh | Increment lease count      | LEASED      |
| LEASED              | Scrape Success Reported      | HTTP 200 & parsed cleanly    | Increment success counter  | ACTIVE_READY|
| LEASED              | Daily Quota Exceeded         | requests_today >= max_daily  | Set exhausted flag         | QUOTA_EXH   |
| LEASED              | HTTP 429 / Rate Limit        | Status code == 429           | cooldown_until = time()+sec| COOLDOWN    |
| LEASED              | Checkpoint / Captcha Trigger | Captcha or 2FA challenge     | Notify operator / Tab 5 UI | CHECKPOINT  |
| LEASED              | HTTP 401 / 403 Session Death | Invalidated auth cookie      | Mark requires session rec  | EXPIRED     |
| LEASED              | Hard Ban / Profile Deleted   | Account suspension message   | Revoke credentials permanently| BANNED  |
| COOLDOWN            | release_expired_cooldowns()  | time.time() > cooldown_until | status = 'active', timer=0 | ACTIVE_READY|
| QUOTA_EXH           | Midnight UTC Chron Reset     | UTC Day Rollover             | requests_today = 0         | ACTIVE_READY|
| CHECKPOINT          | Operator Solves Captcha      | TOTP or manual login passes  | New cookies re-encrypted   | ACTIVE_READY|
| EXPIRED             | Browser Session Recorder Run | Fresh login cookies stored   | Re-verify target access    | ACTIVE_READY|
+=============================================================================================================================+
```

### 3.2 Account Lifecycle State Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> PROVISIONED : Bulk Import / Add Account API
    PROVISIONED --> ACTIVE_READY : AES-256-GCM Encrypted & Validated

    ACTIVE_READY --> LEASED_IN_USE : AccountRouter.acquire_account()<br/>[Target matched, lowest usage]
    
    LEASED_IN_USE --> ACTIVE_READY : Outcome = 'success'<br/>[Health score preserved]
    
    LEASED_IN_USE --> QUOTA_EXHAUSTED : requests_today >= max_daily<br/>[Daily limit reached]
    QUOTA_EXHAUSTED --> ACTIVE_READY : UTC Midnight Cron Reset<br/>[requests_today = 0]

    LEASED_IN_USE --> COOLDOWN_QUARANTINE : Outcome = 'rate_limited'<br/>[HTTP 429 / soft challenge]
    COOLDOWN_QUARANTINE --> ACTIVE_READY : release_expired_cooldowns()<br/>[time.time() >= cooldown_until]

    LEASED_IN_USE --> CHECKPOINT_REQUIRED : Outcome = 'checkpoint'<br/>[2FA / SMS / Email Prompt]
    CHECKPOINT_REQUIRED --> ACTIVE_READY : TOTP Solved / Session Refreshed

    LEASED_IN_USE --> SESSION_EXPIRED : Outcome = 'expired'<br/>[HTTP 401 / Invalidated cookie]
    SESSION_EXPIRED --> ACTIVE_READY : Record Browser Session Re-auth

    LEASED_IN_USE --> DISABLED_BANNED : Outcome = 'banned'<br/>[Permanent Account Termination]
    DISABLED_BANNED --> [*] : Quarantined Permanently
```

---

## 4. Action Run & Data Lifecycle State Machine (`run_manifest.json`)

The Data Lifecycle state machine enforces the bronze-to-silver data pipeline in accordance with Governance Rule 3.

### 4.1 State Transition Table

```
+=============================================================================================================================+
| CURRENT STATE       | EVENT / TRIGGER              | GUARD CONDITION              | ACTION                     | NEXT STATE  |
+---------------------+------------------------------+------------------------------+----------------------------+-------------+
| UNALLOCATED         | create_action_run()          | Valid tool_id & action_name  | Create directory tree      | ALLOCATED   |
| ALLOCATED           | Network request initiated    | Socket open                  | Stream network payload     | RAW_INGEST  |
| RAW_INGEST          | Raw payload saved to raw/    | Bytes written & flush        | Compute raw SHA-256        | CLEANING    |
| CLEANING            | Normalizer / Parser finished | Structured JSON/CSV ready    | Write cleaned/ & Silver SHA| FINALIZING  |
| FINALIZING          | complete_action_run()        | Manifest schema satisfied    | Write run_manifest.json    | MANIFEST_OK |
| MANIFEST_OK         | Auto-Index Hook Triggered    | BaseToolIndexer available    | Insert into <tool>.sqlite  | TOOL_INDEXED|
| TOOL_INDEXED        | Global Master Hook Triggered | GlobalMasterIndexer running  | Insert into FTS5 tables    | FTS5_SYNCED |
| FTS5_SYNCED         | git_manager commit()         | Zero-Secret pre-commit pass  | Record Git commit in log   | COMMITTED   |
+=============================================================================================================================+
```

### 4.2 Run Lifecycle State Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> UNALLOCATED : Scraper Execution Request

    UNALLOCATED --> DIRECTORY_ALLOCATED : create_action_run()<br/>[Creates data/<tool>/<action>/<date>/run_<id>/]

    state DIRECTORY_ALLOCATED {
        [*] --> Init_Dirs
        Init_Dirs --> Create_Raw_Dir
        Create_Raw_Dir --> Create_Cleaned_Dir
        Create_Cleaned_Dir --> Create_Logs_Dir
    }

    DIRECTORY_ALLOCATED --> RAW_INGESTION : Scraper pipes network stream
    RAW_INGESTION --> CLEANING_NORMALIZATION : Raw files written to disk (Bronze)<br/>[Calculates SHA-256 checksums]
    
    CLEANING_NORMALIZATION --> MANIFEST_FINALIZED : Parsers write structured data (Silver)<br/>[Writes run_manifest.json]

    MANIFEST_FINALIZED --> TOOL_INDEXED : Auto-Index Hook<br/>[Inserts into tool_indexes/<tool_id>.sqlite]

    TOOL_INDEXED --> GLOBAL_FTS5_SYNCED : Master Indexer Hook<br/>[Federates into global_master_index.sqlite FTS5]

    GLOBAL_FTS5_SYNCED --> GIT_COMMITTED : git_manager.commit('[RUN-LOG]')<br/>[Pre-commit secret scan verified]
    
    GIT_COMMITTED --> [*] : Immutable Production Run Artifact
```

---

## 5. 20-Pipeline Index Synchronization State Machine

The Index Synchronization state machine governs how independent per-tool indexes are synchronized with the federated Global Master Search Index.

### 5.1 State Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> UNINDEXED : New Run Directory Created

    UNINDEXED --> PER_TOOL_INDEXING : Run Completes<br/>[complete_action_run() Hook]

    state PER_TOOL_INDEXING {
        [*] --> Read_Manifest
        Read_Manifest --> Extract_Domain_Metrics : Tool specific parser
        Extract_Domain_Metrics --> SQLite_Upsert : Write <tool_id>.sqlite
        SQLite_Upsert --> JSON_Mirror_Write : Write <tool_id>_index.json
    }

    PER_TOOL_INDEXING --> ISOLATED_READY : Tool Index Verified

    ISOLATED_READY --> FEDERATING_TO_GLOBAL : GlobalMasterIndexer.sync_all()<br/>or per-run hook

    state FEDERATING_TO_GLOBAL {
        [*] --> Read_Tool_Runs
        Read_Tool_Runs --> Upsert_Master_Runs : Deduplicate on run_id
        Upsert_Master_Runs --> Populate_FTS_Artifacts : Tokenize file names & snippets
        Populate_FTS_Artifacts --> Populate_FTS_Logs : Tokenize 4-tier log messages
    }

    FEDERATING_TO_GLOBAL --> SYNCED : FTS5 Indexes Fully Up to Date

    SYNCED --> OUT_OF_SYNC_REBUILDING : Disk Rebuild Triggered<br/>(POST /api/index/rebuild)
    OUT_OF_SYNC_REBUILDING --> PER_TOOL_INDEXING : Re-scan filesystem directories
```
