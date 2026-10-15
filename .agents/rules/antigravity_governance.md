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

---

*See `GEMINI.md` in the project root for the full reference with examples.*
