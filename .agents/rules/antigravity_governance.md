# 🤖 Antigravity Workspace Governance Rules
**File:** `.agents/rules/antigravity_governance.md`
**Project:** Crawlers_testing | **Init:** 2026-10-15

> This file is auto-loaded by the Antigravity agent system. Mirror also exists at `.agent/rules/antigravity_governance.md`.

---

## Rule 1 — Live State Telemetry (BEFORE ANY TASK)

Before starting any task, update `logs/global/live_state.json` via:

```bash
python core/cli_tracker.py start \
  --stage "Stage X" --step "Step Y.Z" \
  --tool "tool_id" --action "action_name" \
  --subtask "description"
```

Update `progress_percent` incrementally. Always call `complete` or `fail` at the end.

## Rule 2 — 4-Tier Logging (EVERY PROMPT EXECUTION)

Append to ALL four tiers simultaneously using `core/logger_engine.py`:
1. `logs/global/antigravity_prompt_log.jsonl`
2. `logs/global/antigravity_prompt_log.md`
3. `logs/stages/stage_<N>_<name>.jsonl`
4. `data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl`

## Rule 3 — Strict Data Isolation

Use `core/folder_manager.py → create_action_run()` for ALL tool outputs.
Output structure: `data/<tool_id>/<action_name>/<YYYY-MM-DD>/run_<HHMMSS>_<uuid>/{raw,cleaned,logs}/`
Include `run_manifest.json` in every run directory.

## Rule 4 — Atomic Git Commits

End every action with a commit using prefixes:
`[SCAFFOLD]` | `[TOOL-INSTALL]` | `[UPDATE]` | `[FIX]` | `[RUN-LOG]`

Record commit hash in `logs/global/antigravity_prompt_log.jsonl`.

## Rule 5 — Auto-Indexing (EVERY COMPLETED RUN)

Every completed tool action run automatically updates its SQLite & JSON tool index in `index_store/tool_indexes/<tool_id>.sqlite` and federates to `index_store/global_master_index.sqlite`.

## Rule 6 — Zero-Plaintext Credential & Vault Security

All credentials, passwords, session cookies, tokens, 2FA secrets, and proxy passwords MUST be encrypted via `core/crypto_engine.py` (AES-256-GCM) before storage in `vault_store/`. Plaintext secrets, `.env`, and `vault_store/*.sqlite*` must NEVER be logged or committed to Git.

## Rule 7 — Human Simulation & Timing Discipline

When running in human or stealth modes, scrapers must strictly use `core/human_timing.py` distributions rather than static integer sleep intervals to prevent fingerprinting. All delays must be drawn from statistical models (`gaussian_delay`, `log_normal_delay`, `exponential_backoff_jitter`) or contextual action calculators (`keystroke_delay`, `reading_pause`, `chunk_download_pacing`, `session_burst_delay`).

## Rule 8 — Data Lake Silver Tier Contract Enforcement

All transformed files saved into `cleaned/` directories must conform strictly to standardized schemas enforced by `core/cleaning_pipeline.py`. Arbitrary unvalidated dumps are strictly prohibited.

## Rule 9 — Benchmark Traceability & Non-Destructive Testing

Benchmark runs must record reproducible telemetry (p50/p90/p99 latency, RAM delta, CPU utilization, raw/cleaned byte efficiency, and stealth score) into structured benchmark reports and log all executions to `logs/stages/stage_6_benchmarking.jsonl`.

---

*See `GEMINI.md` in the project root for the full reference with examples.*

