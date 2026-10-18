# Developer Operations & Execution Runbook
**Project:** `Crawlers_testing` | **Status:** Operational Runbook | **Stage:** Stage 3 Active

---

## 1. System Environment & Server Operations

The `Crawlers_testing` platform combines a high-throughput crawler engine with a FastAPI telemetry and WebSocket control plane. Operating this hybrid environment safely requires adhering to defined startup and worker management protocols.

### 1.1 Starting the FastAPI Control Center

To launch the FastAPI server (:8000) for development and production telemetry:

```powershell
# Standard Production / Long-Running Mode (Recommended)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Development Mode with Selective Reload (Prevents reload loops)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

> [!IMPORTANT]
> **Never run raw `--reload` without `--reload-dir backend`**. Scraping engines continuously write raw and cleaned outputs into `data/` and append log files in `logs/`. An unrestricted `--reload` flag will detect these writes and restart the Uvicorn server in an infinite reload loop, terminating active crawlers and dropping WebSocket connections.

### 1.2 Accessing the Web Control Center

Once launched, navigate to:
- **Control Center UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **OpenAPI / Swagger Spec:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Interactive Spec:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 1.3 Background Process Management & Worker Telemetry

The platform automatically tracks child worker processes (Playwright browser instances, FFmpeg demuxing threads, Python crawler subprocesses) via `psutil`.

To inspect active worker processes from the CLI:

```powershell
# Check current system telemetry and worker PIDs
.\.venv\Scripts\python.exe core/cli_tracker.py status

# Inspect active worker process resource consumption (CPU%, RAM MB, Runtime)
.\.venv\Scripts\python.exe -c "from core.state_tracker import scan_worker_processes; import json; print(json.dumps(scan_worker_processes(), indent=2))"
```

---

## 2. CLI & Automation Runbook

Every component in `Crawlers_testing` is fully operable from the command line without launching the browser UI.

### 2.1 Invoking the 20 Tool Adapters Directly

All tool adapters conform to a uniform invocation interface:

```powershell
# Example: Run 01_curl_cffi for LeetCode scraping
.\.venv\Scripts\python.exe tools/01_curl_cffi/adapter.py --url "https://leetcode.com/problems/two-sum/" --action "scrape_for_leetcode"

# Example: Run 06_playwright for dynamic single-page applications
.\.venv\Scripts\python.exe tools/06_playwright/adapter.py --url "https://example.com" --action "scrape_for_leetcode"

# Example: Run 11_yt_dlp_ffmpeg for media stream extraction
.\.venv\Scripts\python.exe tools/11_yt_dlp_ffmpeg/adapter.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --action "video_download"

# Example: Run 16_crawl4ai for LLM-ready markdown extraction
.\.venv\Scripts\python.exe tools/16_crawl4ai/adapter.py --url "https://news.ycombinator.com" --action "llm_ready_scrape"
```

### 2.2 Triggering Per-Tool & Global Search Re-Indexing

When runs are created via CLI scripts or manual tests, indexes can be refreshed on-demand:

```powershell
# Re-index an individual tool run database
.\.venv\Scripts\python.exe -c "from tools.01_curl_cffi.indexer import Tool01Indexer; Tool01Indexer().sync_index()"

# Federate all 20 tool databases into the Global Master FTS5 Search Index
.\.venv\Scripts\python.exe -c "from core.global_indexer import GlobalMasterIndexer; print(GlobalMasterIndexer().sync_all())"
```

### 2.3 Manual State Telemetry Overrides (Rule 1 Enforcement)

When developing or executing custom crawler actions, manage telemetry manually:

```powershell
# 1. Start a task
.\.venv\Scripts\python.exe core/cli_tracker.py start --stage "Stage 3" --step "Step 3.6" --tool "01_curl_cffi" --action "scrape_for_leetcode" --subtask "Scraping problem metadata"

# 2. Update progress percentage (0 - 100)
.\.venv\Scripts\python.exe core/cli_tracker.py update --progress 45 --subtask "Parsing HTML with Selectolax"

# 3. Complete task cleanly
.\.venv\Scripts\python.exe core/cli_tracker.py complete

# 4. Or fail task on unhandled error
.\.venv\Scripts\python.exe core/cli_tracker.py fail --reason "HTTP 403 Forbidden - Cloudflare Turnstile block"
```

---

## 3. Credential & Vault Operations

The zero-plaintext credential vault stores and rotates encrypted identities for authenticated scraping.

### 3.1 Adding an Encrypted Account Profile

```powershell
# Ingest an account with username, password, and 2FA TOTP seed
.\.venv\Scripts\python.exe -c "
from core.credential_vault import get_credential_vault
vault = get_credential_vault()
acc_id = vault.add_account(
    platform='instagram',
    account_label='Instagram Scraping Bot 01',
    username='my_scraper_user',
    password='SuperSecretPassword123!',
    totp_secret='JBSWY3DPEHPK3PXP',
    follows_targets=['@target_celebrity', '@tech_crunch'],
    daily_quota_limit=100
)
print('Account created:', acc_id)
"
```

### 3.2 Bulk Ingesting Accounts (Netscape / JSONL / CSV)

To bulk-import up to 1,000 accounts in a single transaction:

```powershell
# Bulk import from Netscape cookies.txt file
.\.venv\Scripts\python.exe -c "
from core.vault_importer import VaultImporter
from pathlib import Path
importer = VaultImporter()
summary = importer.import_netscape_file(
    Path('sample_cookies.txt'),
    platform='instagram',
    follows_targets=['@private_target']
)
print('Import summary:', summary)
"
```

### 3.3 Generating On-Demand 2FA TOTP Codes

Generate 6-digit TOTP codes for any vault account without exposing the raw Base32 seed:

```powershell
# Via Account ID
.\.venv\Scripts\python.exe -c "
from core.totp_helper import TOTPHelper
from core.credential_vault import get_credential_vault
vault = get_credential_vault()
print(TOTPHelper.get_totp_for_account(vault, 'acc_insta_179232_...'))
"
```

Output:
```json
{
  "code": "492018",
  "time_remaining_sec": 24,
  "period_sec": 30,
  "valid": true
}
```

### 3.4 Launching Interactive & Headless Browser Session Captures

Capture live sessions and cookies from an interactive browser window:

```powershell
# Launches visible Chromium browser. User logs in manually. Session cookies are encrypted directly into the vault.
.\.venv\Scripts\python.exe -c "
from core.browser_session_recorder import BrowserSessionRecorder
recorder = BrowserSessionRecorder()
summary = recorder.record_browser_session(
    platform='instagram',
    login_url='https://www.instagram.com/accounts/login/',
    account_label='Instagram Manual Session',
    interactive=True,
    wait_seconds=45,
    follows_targets=['@private_target']
)
print('Session captured:', summary)
"
```

### 3.5 Testing Authenticated Session Injection with Ephemeral Shredding

Test that an account is leased, an ephemeral `.cookies.txt` file is generated, passed to a tool, and immediately shredded upon exit:

```powershell
.\.venv\Scripts\python.exe -c "
from core.auth_injector import AuthInjector
injector = AuthInjector()
with injector.authenticated_session(tool_id='11_yt_dlp_ffmpeg', platform='instagram') as auth:
    print('Leased account:', auth.account_id)
    print('Ephemeral cookie path:', auth.cookie_file_path)
    # File exists and contains valid cookies
print('Context exited! Ephemeral cookie file shredded and unlinked.')
"
```

---

## 4. Verification Suites & Regression Testing

Every stage and milestone includes an automated verification script enforcing all six Antigravity Governance rules.

```
+==================================================================================================+
| TEST SUITE                    | COMMAND                                                          |
+-------------------------------+------------------------------------------------------------------+
| Stage 1: Scaffolding          | .\.venv\Scripts\python.exe core/verify_step_1_3.py               |
| Stage 2: Dual-Tier Indexing   | .\.venv\Scripts\python.exe core/verify_step_2_4.py               |
| Stage 3.1: Crypto Engine      | .\.venv\Scripts\python.exe core/verify_step_3_1.py               |
| Stage 3.2: Credential Vault   | .\.venv\Scripts\python.exe core/verify_step_3_2.py               |
| Stage 3.3: TOTP & Importer    | .\.venv\Scripts\python.exe core/verify_step_3_3.py               |
| Stage 3.4: Account Router     | .\.venv\Scripts\python.exe core/verify_step_3_4.py               |
| Stage 3.5: Auth Injector      | .\.venv\Scripts\python.exe core/verify_step_3_5.py               |
| Stage 3.6: Master Vault API   | .\.venv\Scripts\python.exe core/verify_step_3_6.py               |
| Doc Milestone D.1: Architecture| .\.venv\Scripts\python.exe core/verify_step_d_1.py              |
| Doc Milestone D.2: Database/Sec| .\.venv\Scripts\python.exe core/verify_step_d_2.py              |
| Doc Milestone D.3: File Ref   | .\.venv\Scripts\python.exe core/verify_step_d_3.py               |
| Doc Milestone D.4: Operations | .\.venv\Scripts\python.exe core/verify_step_d_4.py               |
+==================================================================================================+
```

To run all Stage 3 verification suites in sequence:

```powershell
.\.venv\Scripts\python.exe -c "
import subprocess, sys
scripts = [
    'core/verify_step_3_1.py',
    'core/verify_step_3_2.py',
    'core/verify_step_3_3.py',
    'core/verify_step_3_4.py',
    'core/verify_step_3_5.py',
    'core/verify_step_3_6.py'
]
for s in scripts:
    print('='*70); print(f'RUNNING {s}...'); print('='*70)
    res = subprocess.run([sys.executable, s])
    if res.returncode != 0:
        print(f'FAILED: {s}'); sys.exit(1)
print('ALL STAGE 3 SUITES PASSED SUCCESSFULLY!')
"
```
