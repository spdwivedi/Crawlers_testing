# Core Governance, Telemetry & Security Engine (`core/`)

The `core/` package forms the operational backbone of `Crawlers_testing`. It enforces the six mandatory governance rules, manages real-time telemetry, provisions isolated data lake run directories, executes 4-tier structured logging, and powers the AES-256-GCM zero-plaintext credential vault.

---

## 📂 Subsystem Overview

| Module | Architectural Role | Governance Rule Enforced |
|:---|:---|:---:|
| `state_tracker.py` | Thread-safe `live_state.json` read/write & `psutil` background process monitoring | **Rule 1** (Live Telemetry) |
| `cli_tracker.py` | Command-line interface for telemetry state transitions (`start`, `update`, `complete`, `fail`) | **Rule 1** (Live Telemetry) |
| `logger_engine.py` | Simultaneous 4-tier logger formatting JSONL events and markdown summary tables | **Rule 2** (4-Tier Logging) |
| `folder_manager.py` | Medallion run directory allocator (`raw/`, `cleaned/`, `manifest.json`) & Rule 5 hook | **Rule 3** (Data Isolation) |
| `git_manager.py` | Atomic Git commits with standardized prefixes and Pre-Commit Secret Guard scanning | **Rule 4** & **Rule 6** |
| `base_indexer.py` | Base SQLite WAL indexer extracting domain-specific KPIs for the 20 tools | **Rule 5** (Auto-Indexing) |
| `global_indexer.py` | Global Master Indexer federating all 20 tool databases into SQLite FTS5 | **Rule 5** (Auto-Indexing) |
| `crypto_engine.py` | PBKDF2-HMAC-SHA256 (600k iters), AES-256-GCM authenticated encryption & blind hashing | **Rule 6** (Zero-Plaintext) |
| `credential_vault.py` | Encrypted SQLite credential repository with row-binding and junction target access | **Rule 6** (Zero-Plaintext) |
| `totp_helper.py` | RFC 6238 2FA TOTP generator with Base32 sanitization and clock-skew tolerance | **Rule 6** (Zero-Plaintext) |
| `vault_importer.py` | Netscape `cookies.txt`, CSV, JSONL parser with 1,000-account single-transaction import | **Rule 6** (Zero-Plaintext) |
| `account_router.py` | Account pool manager with cooldown auto-release, quotas, and private-target matching | **Rule 6** (Zero-Plaintext) |
| `browser_session_recorder.py` | Playwright interactive and headless session recorder storing encrypted storage state | **Rule 6** (Zero-Plaintext) |
| `auth_injector.py` | Universal auth bundle synthesizer & context manager with zero-fill cookie shredding | **Rule 6** (Zero-Plaintext) |

---

## 🛠️ Usage Examples

```powershell
# 1. Update live telemetry from CLI
python core/cli_tracker.py update --progress 50 --subtask "Parsing HTML"

# 2. Derive on-demand 2FA TOTP code for account
python -c "from core.totp_helper import TOTPHelper; from core.credential_vault import get_credential_vault; print(TOTPHelper.get_totp_for_account(get_credential_vault(), 'acc_insta_...'))"

# 3. Synchronize all 20 tool databases into the master search index
python -c "from core.global_indexer import GlobalMasterIndexer; GlobalMasterIndexer().sync_all()"
```

For complete class specifications and method signatures, refer to [docs/03_folder_and_file_reference/02_core_and_api_file_reference.md](../docs/03_folder_and_file_reference/02_core_and_api_file_reference.md).
