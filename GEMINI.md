# 🤖 Antigravity Workspace Governance — GEMINI.md
**Project:** Crawlers_testing | **Stage:** 5 (Standardized Cleaned Schemas & Real Task Pipelines) | **Init:** 2026-10-15

This file is automatically loaded by Antigravity IDE for **every prompt execution** in this workspace. All rules below are **mandatory** and non-negotiable.

---

## Rule 1 — Live State Telemetry (BEFORE ANY TASK)

Before starting any task, update `logs/global/live_state.json` via:

```bash
python core/cli_tracker.py start \
  --stage "Stage X" \
  --step "Step Y.Z" \
  --tool "tool_id" \
  --action "action_name" \
  --subtask "description of current subtask"
```

- Update `progress_percent` as sub-steps complete (0 → 100).
- Call `python core/cli_tracker.py complete` on success.
- Call `python core/cli_tracker.py fail --reason "..."` on failure.
- Mark `completed` or `failed` at the end — never leave `is_running: true`.

---

## Rule 2 — 4-Tier Logging (EVERY PROMPT EXECUTION)

Every prompt execution MUST append structured entries to ALL four tiers:

| Tier | File |
|------|------|
| Global JSONL | `logs/global/antigravity_prompt_log.jsonl` |
| Global MD | `logs/global/antigravity_prompt_log.md` |
| Stage Log | `logs/stages/stage_<N>_<name>.jsonl` |
| Action Run Log | `data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl` |

Use `core/logger_engine.py` — never write raw `print()` for structured logging.

---

## Rule 3 — Strict Data Isolation

All tool output MUST be written via `core/folder_manager.py`:

```python
from core.folder_manager import create_action_run
run_info = create_action_run(
    tool_id="01_curl_cffi",
    action_name="scrape_for_leetcode",
    target_url="https://leetcode.com/problems/..."
)
# Output path: data/01_curl_cffi/scrape_for_leetcode/<YYYY-MM-DD>/run_<HHMMSS>_<uuid>/
```

Every run directory contains:
- `raw/` — unprocessed outputs
- `cleaned/` — parsed/structured outputs
- `logs/action_run.jsonl` — per-run log
- `run_manifest.json` — metadata including git commit hash

---

## Rule 4 — Atomic Git Commits

Every development action MUST end with an atomic Git commit:

| Prefix | When to Use |
|--------|------------|
| `[SCAFFOLD]` | New structure, init, or directory creation |
| `[TOOL-INSTALL]` | Installing or verifying a tool |
| `[UPDATE]` | Modifying existing code/config |
| `[FIX]` | Bug fix or error correction |
| `[RUN-LOG]` | After a tool run completes |

```bash
git add -A
git commit -m "[PREFIX] Brief description — Stage X Step Y.Z"
```

Record the resulting commit hash into `logs/global/antigravity_prompt_log.jsonl`.

---

## Rule 5 — Auto-Indexing (EVERY COMPLETED RUN)

Every completed tool action run MUST automatically update its dedicated tool index in `index_store/tool_indexes/<tool_id>.sqlite` and its companion `index_store/tool_indexes/<tool_id>_index.json`.

- Triggered automatically via `core/folder_manager.py:complete_action_run()`.
- Captures run metadata, file manifests with SHA256 hashes & content previews, 4-tier logs, and tool-specific domain metrics.
- All 20 tool indexes must be queryable via the FastAPI backend (`GET /api/tool-indexes` and `GET /api/tool-indexes/{tool_id}`).

---

## Rule 6 — Zero-Plaintext Credential & Vault Security

All credentials, passwords, session cookies, tokens, 2FA secrets, and proxy passwords MUST be encrypted via `core/crypto_engine.py` (AES-256-GCM) before storage in `vault_store/`. Plaintext secrets, `.env`, and `vault_store/*.sqlite*` must NEVER be logged or committed to Git.

- `.env` holds the master key (`VAULT_MASTER_KEY`) and PBKDF2 salt (`VAULT_KDF_SALT`) and is strictly ignored by Git.
- A safe `.env.example` template contains placeholder keys only.
- Pre-commit secret scanning in `core/git_manager.py` automatically blocks accidental staging of credentials, `.env`, and vault databases.

---

## Rule 7 — Human Simulation & Timing Discipline

When running in human or stealth modes, scrapers must strictly use `core/human_timing.py` distributions rather than static integer sleep intervals to prevent fingerprinting. All delays must be drawn from statistical models (`gaussian_delay`, `log_normal_delay`, `exponential_backoff_jitter`) or contextual action calculators (`keystroke_delay`, `reading_pause`, `chunk_download_pacing`, `session_burst_delay`).

---

## Rule 8 — Data Lake Silver Tier Contract Enforcement

All transformed files saved into `cleaned/` directories must conform strictly to standardized schemas enforced by `core/cleaning_pipeline.py`. Arbitrary unvalidated dumps are strictly prohibited.

---

## Quick Reference — Core Modules

```
core/
├── folder_manager.py    # create_action_run() — Rule 3 & complete_action_run() Auto-Index Hook — Rule 5
├── cleaning_pipeline.py # CleaningPipeline & Silver Tier Contracts — Rule 8
├── base_indexer.py      # BaseToolIndexer SQLite/JSON engine — Rule 5
├── global_indexer.py    # GlobalMasterIndexer FTS5 federated engine — Rule 5
├── crypto_engine.py     # AES-256-GCM authenticated encryption & KDF — Rule 6
├── human_timing.py      # Statistical delays, human jitter & contextual pacing — Rule 7
├── state_tracker.py     # live_state.json R/W — Rule 1
├── cli_tracker.py       # CLI wrapper for state_tracker — Rule 1
├── logger_engine.py     # 4-tier logger — Rule 2
└── git_manager.py       # Atomic commits + secret guard — Rule 4 & 6

index_store/
├── global_master_index.sqlite  # Federated FTS5 search across all runs & logs
└── tool_indexes/               # 20 SQLite (.sqlite) + JSON (_index.json) tool index databases

vault_store/
├── README_VAULT.md             # Security architecture & usage guide
├── vault_stats_public.json     # Non-sensitive aggregate metrics (Git tracked)
└── *.sqlite                    # Encrypted credential & session databases (Git ignored)

logs/
├── global/
│   ├── live_state.json
│   ├── antigravity_prompt_log.jsonl
│   └── antigravity_prompt_log.md
└── stages/
    ├── stage_1_scaffolding.jsonl
    ├── stage_2_indexing.jsonl
    ├── stage_3_credential_vault.jsonl
    ├── stage_4_working_ways.jsonl
    └── stage_5_real_pipelines.jsonl

tools/
└── registry.json        # 20-tool manifest

backend/app.py           # FastAPI telemetry & index server :8000
frontend/index.html      # Control Center UI
```

---

*Auto-enforced by Antigravity IDE — do not delete or modify this file.*


