# 🤖 Antigravity Workspace Governance Rules
**File:** `.agent/rules/antigravity_governance.md`
**Project:** Crawlers_testing | **Init:** 2026-10-15

> Mirror of `.agents/rules/antigravity_governance.md`. Both are auto-loaded.

---

## Rule 1 — Live State Telemetry (BEFORE ANY TASK)

Before starting any task, update `logs/global/live_state.json` via:
```bash
python core/cli_tracker.py start --stage "..." --step "..." --tool "..." --action "..." --subtask "..."
```
Update `progress_percent` as sub-steps complete. Mark `completed` or `failed` at the end.

## Rule 2 — 4-Tier Logging (EVERY PROMPT EXECUTION)

Append structured entries to:
1. `logs/global/antigravity_prompt_log.jsonl`
2. `logs/global/antigravity_prompt_log.md`
3. `logs/stages/stage_<N>_<name>.jsonl`
4. `data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl`

## Rule 3 — Strict Data Isolation

Use `core/folder_manager.py → create_action_run()` for ALL outputs.
Structure: `data/<tool_id>/<action_name>/<YYYY-MM-DD>/run_<HHMMSS>_<uuid>/{raw,cleaned,logs}/`

## Rule 4 — Atomic Git Commits

Prefix: `[SCAFFOLD]` | `[TOOL-INSTALL]` | `[UPDATE]` | `[FIX]` | `[RUN-LOG]`
Record commit hash in `logs/global/antigravity_prompt_log.jsonl`.

## Rule 5 — Auto-Indexing (EVERY COMPLETED RUN)

Every completed tool action run automatically updates its SQLite & JSON tool index in `index_store/tool_indexes/<tool_id>.sqlite` and federates to `index_store/global_master_index.sqlite`.

## Rule 6 — Zero-Plaintext Credential & Vault Security

All credentials, passwords, session cookies, tokens, 2FA secrets, and proxy passwords MUST be encrypted via `core/crypto_engine.py` (AES-256-GCM) before storage in `vault_store/`. Plaintext secrets, `.env`, and `vault_store/*.sqlite*` must NEVER be logged or committed to Git.

*See `GEMINI.md` for full reference.*

