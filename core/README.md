# Core Governance, Telemetry, Security & Execution Engine (`core/`)

The `core/` package forms the operational and algorithmic backbone of `Crawlers_testing`. It enforces the 9 mandatory governance rules, manages real-time telemetry, provisions isolated data lake run directories, executes simultaneous 4-tier structured logging, powers the zero-plaintext cryptographic vault, and orchestrates the 3 Working Ways, 4 Production Pipelines, Benchmarking, Chaos Stress Lab, and Standalone Project Exporter.

---

## 🏛️ Comprehensive 23-Module Core Architecture

The core framework is structured across 8 operational domains containing 23 specialized Python modules:

### 1. Governance, Telemetry & Process Lifecycle (Rule 1 & Rule 2)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`state_tracker.py`](file:///d:/Project_Files/Crawlers_testing/core/state_tracker.py) | `StateTracker`, `update_progress`, `get_live_state` | Thread-safe atomic read/write of `logs/global/live_state.json`. Monitors active worker PIDs, CPU %, and memory RSS footprint via `psutil`. (**Rule 1**) |
| [`cli_tracker.py`](file:///d:/Project_Files/Crawlers_testing/core/cli_tracker.py) | CLI wrapper (`start`, `update`, `complete`, `fail`) | Terminal-based state controller invoked before and after every automation task. (**Rule 1**) |
| [`logger_engine.py`](file:///d:/Project_Files/Crawlers_testing/core/logger_engine.py) | `LogEngine`, `log_global`, `log_stage` | Dispatches structured diagnostic events simultaneously across all 4 tiers: Global JSONL, Global Markdown, Stage Log, and Action Run Log. (**Rule 2**) |

### 2. Medallion Data Lake Isolation & Git Protection (Rule 3, Rule 4, Rule 6)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`folder_manager.py`](file:///d:/Project_Files/Crawlers_testing/core/folder_manager.py) | `create_action_run`, `complete_action_run` | Allocates isolated run directories (`raw/`, `cleaned/`, `logs/`, `run_manifest.json`) and triggers automatic indexing upon run completion. (**Rule 3 & Rule 5**) |
| [`git_manager.py`](file:///d:/Project_Files/Crawlers_testing/core/git_manager.py) | `commit_atomic`, `scan_staged_for_secrets` | Enforces categorized atomic Git commits (`[SCAFFOLD]`, `[TOOL-INSTALL]`, `[UPDATE]`, `[FIX]`, `[RUN-LOG]`, `[DOCS]`) and intercepts accidental staging of `.env`, `*.sqlite`, or tokens. (**Rule 4 & Rule 6**) |

### 3. Dual-Tier Search Indexing & Federation (Rule 5)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`base_indexer.py`](file:///d:/Project_Files/Crawlers_testing/core/base_indexer.py) | `BaseToolIndexer` | Abstract SQLite WAL indexer for the 20 tool engines. Captures SHA-256 manifests, text previews, and tool-specific KPIs into `<tool_id>.sqlite`. (**Rule 5**) |
| [`global_indexer.py`](file:///d:/Project_Files/Crawlers_testing/core/global_indexer.py) | `GlobalMasterIndexer`, `sync_all` | Federates records from all 20 tool SQLite databases and 4 log tiers into `global_master_index.sqlite` with SQLite FTS5 BM25 ranked full-text search. (**Rule 5**) |

### 4. Zero-Plaintext Cryptographic Vault & Authentication (Rule 6)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`crypto_engine.py`](file:///d:/Project_Files/Crawlers_testing/core/crypto_engine.py) | `CryptoEngine`, `encrypt_str`, `decrypt_str` | PBKDF2-HMAC-SHA256 (600,000 iterations) key derivation, AES-256-GCM authenticated encryption with row-binding Associated Data (AD), and blind indexing. (**Rule 6**) |
| [`credential_vault.py`](file:///d:/Project_Files/Crawlers_testing/core/credential_vault.py) | `CredentialVault`, `get_credential_vault` | Encrypted SQLite repository managing account profiles, credentials, cookies, and target junction relationships with high-concurrency WAL mode. (**Rule 6**) |
| [`totp_helper.py`](file:///d:/Project_Files/Crawlers_testing/core/totp_helper.py) | `TOTPHelper`, `generate_totp_code` | RFC 6238 2FA TOTP generator with Base32 secret normalization, clock-skew verification, and memory-only token extraction (never leaks raw seeds). (**Rule 6**) |
| [`vault_importer.py`](file:///d:/Project_Files/Crawlers_testing/core/vault_importer.py) | `VaultImporter`, `import_from_file` | High-throughput batch credential ingestor parsing Netscape `cookies.txt`, CSV, and JSONL formats in a single atomic transaction. (**Rule 6**) |
| [`account_router.py`](file:///d:/Project_Files/Crawlers_testing/core/account_router.py) | `AccountRouter`, `lease_account`, `report_outcome` | Intelligent account rotation with cooldown quarantine auto-release, hourly rate-limit quotas, and target-follower coverage matching. (**Rule 6**) |
| [`browser_session_recorder.py`](file:///d:/Project_Files/Crawlers_testing/core/browser_session_recorder.py) | `BrowserSessionRecorder` | Interactive and headless Playwright session capturer recording cookies, localStorage, and session state directly into the encrypted vault. (**Rule 6**) |
| [`auth_injector.py`](file:///d:/Project_Files/Crawlers_testing/core/auth_injector.py) | `AuthInjector`, `authenticated_session` | Universal authentication bundle context manager synthesizing headers, cookies, and ephemeral Netscape files with 0x00 byte shredding on exit. (**Rule 6**) |

### 5. Human Simulation, Biomechanics & Kinematics (Rule 7)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`human_timing.py`](file:///d:/Project_Files/Crawlers_testing/core/human_timing.py) | `HumanTimingEngine`, `TimingProfile` | Generates authentic statistical delay distributions (Gaussian, Log-Normal, Exponential Backoff Jitter) and contextual delays (keystrokes, dwell times). (**Rule 7**) |
| [`human_interaction.py`](file:///d:/Project_Files/Crawlers_testing/core/human_interaction.py) | `HumanInteractionEngine` | Evaluates cubic Bezier mouse curves with Fitts' Law velocity easing ($t \mapsto t^2(3 - 2t)$), micro-tremor jitter, QWERTY typing cadences, and typo simulations. (**Rule 7**) |
| [`human_adapter_helper.py`](file:///d:/Project_Files/Crawlers_testing/core/human_adapter_helper.py) | `HumanAdapterHelper` | Bridge orchestrating browser page warmups, natural human feed browsing, random viewport wandering, and reading dwell pauses. (**Rule 7**) |

### 6. The 3 Working Ways & Silver-Tier Contract Engine (Rule 3 & Rule 8)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`arena_runner.py`](file:///d:/Project_Files/Crawlers_testing/core/arena_runner.py) | `SafeArenaRunner`, `run_arena` | **Working Way 2:** Coordinates head-to-head multi-tool tournaments on a target URL with anti-ban staggered concurrency and comparative scoring. |
| [`task_router.py`](file:///d:/Project_Files/Crawlers_testing/core/task_router.py) | `PrecisionTaskRouter`, `PipelineStage` | **Working Way 3:** Multi-stage tool chaining engine with dynamic predecessor artifact resolution and canonical extraction recipes. |
| [`cleaning_pipeline.py`](file:///d:/Project_Files/Crawlers_testing/core/cleaning_pipeline.py) | `CleaningPipeline`, 5 Contract Models | **Rule 8:** Silver-Tier schema validator enforcing `CleanedMarkdownContract`, `CleanedCodeProblemContract`, `CleanedSocialMediaContract`, `CleanedForensicsContract`, and `CleanedMultimodalContract`. |

### 7. Benchmarking, Chaos Stress Lab & Standalone Exporter (Rule 9)
| Module | Primary Classes / Functions | Operational Role & Governance Mandate |
|:---|:---|:---|
| [`benchmark_engine.py`](file:///d:/Project_Files/Crawlers_testing/core/benchmark_engine.py) | `BenchmarkEngine`, `compute_percentiles` | Master 20-tool performance matrix engine computing statistical latency percentiles ($p50/p90/p99$), RAM deltas, data yield, and composite scores. (**Rule 9**) |
| [`resilience_tester.py`](file:///d:/Project_Files/Crawlers_testing/core/resilience_tester.py) | `ResilienceTester`, `ChaosFaultServer` | Ephemeral localhost chaos testbed injecting HTTP 429 rate limits, Cloudflare markers, scrambled DOM mutations, TCP resets, and contract fuzzing. (**Rule 9**) |
| [`project_exporter.py`](file:///d:/Project_Files/Crawlers_testing/core/project_exporter.py) | `ProjectExporter`, `export_standalone_tool` | Zero-leak packager generating standalone runnable scraper packages, cryptographically signed Data Lake ZIP bundles, and Dockerized pipeline packages. |

---

## 🛠️ CLI Operations & Verification

```powershell
# 1. Update live telemetry from CLI
python core/cli_tracker.py update --progress 50 --subtask "Parsing HTML with Modest C engine"

# 2. Derive on-demand 2FA TOTP code for account
python -c "from core.totp_helper import TOTPHelper; from core.credential_vault import get_credential_vault; print(TOTPHelper.get_totp_for_account(get_credential_vault(), 'acc_insta_...'))"

# 3. Synchronize all 20 tool databases into the master search index
python -c "from core.global_indexer import GlobalMasterIndexer; GlobalMasterIndexer().sync_all()"

# 4. Run Full Master System Regression Verification Suite
python core/verify_master_system.py
```

For complete class specifications, parameter types, and return models, refer to [docs/03_folder_and_file_reference/02_core_and_api_file_reference.md](../docs/03_folder_and_file_reference/02_core_and_api_file_reference.md).
