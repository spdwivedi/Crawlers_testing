# 4-Tier Structured Logging Directory (`logs/`)

The `logs/` directory houses the global audit trails, real-time telemetry state, and stage-isolated milestone records enforcing Antigravity Governance Rule 2 (4-Tier Logging).

---

## 🏛️ 4-Tier Logging Architecture

Every diagnostic event, crawler run status, pipeline execution, or system milestone is written to four distinct log tiers simultaneously via `core/logger_engine.py`:

```
logs/
├── global/                            # TIER 1 & TIER 2 LOGS
│   ├── antigravity_prompt_log.jsonl   # Tier 1: Machine-readable historical prompt log
│   ├── antigravity_prompt_log.md      # Tier 2: Human-readable markdown milestone table
│   └── live_state.json                # Live Telemetry State (WebSocket HUD feed at 1 Hz)
│
└── stages/                            # TIER 3 LOGS (Isolated by Stage)
    ├── stage_1_scaffolding.jsonl      # Stage 1: Architecture, 20 tools & scaffolding milestones
    ├── stage_2_indexing.jsonl         # Stage 2: Dual-tier SQLite FTS5 search milestones
    ├── stage_3_credential_vault.jsonl # Stage 3: AES-256-GCM vault & 2FA authentication milestones
    ├── stage_4_working_ways.jsonl     # Stage 4: Human engine, Safe Arena & Task Router milestones
    ├── stage_5_real_pipelines.jsonl   # Stage 5: Real-world task pipelines & Silver contracts
    └── stage_6_benchmarking.jsonl     # Stage 6: Benchmarks, chaos drills & standalone exports

# TIER 4 LOGS (Located in Data Lake per Run):
# data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl
```

---

## 📜 Simultaneous 4-Tier Write Model

When `log_global()` or `LogEngine` records an event:
1. **Tier 1 (Global JSONL):** Appends a single-line JSON record to `logs/global/antigravity_prompt_log.jsonl`.
2. **Tier 2 (Global Markdown):** Appends a formatted table row to `logs/global/antigravity_prompt_log.md` with timestamp, stage, step, tool ID, message, and elapsed time.
3. **Tier 3 (Stage Log):** Appends the event to the active stage JSONL log in `logs/stages/` (e.g. `stage_6_benchmarking.jsonl`), isolating stage histories.
4. **Tier 4 (Action Run Log):** If executed inside an action run context (`create_action_run`), appends to `data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl`, binding diagnostic telemetry directly to raw and cleaned artifacts.

---

## 📜 Structured JSONL Record Schema

```json
{
  "timestamp": "2026-10-24T06:29:47.688852+00:00",
  "level": "INFO",
  "stage": "Master Verification",
  "step": "Final Audit",
  "tool_id": "master_verifier",
  "action_name": "verify_master_system",
  "run_id": "run_062947_17b3",
  "message": "MASTER CHECK PASSED: Pre-Push Secret Guard reports ZERO violations in staged files",
  "elapsed_ms": 142,
  "progress_pct": 100
}
```

---

## ⚡ Live Log Streaming via WebSockets

The FastAPI backend (:8000) monitors `logs/global/*.jsonl` using OS-native kernel file notifications (`watchdog`). Newly appended lines are immediately broadcast over `/ws/logs`, streaming into the virtual-scrolling console on frontend Tab 1 and Tab 4 with sub-2ms latency.

---

## 🛡️ Log Retention & Deduplication Rules

1. **No Plaintext Credential Logging:** Passwords, session cookies, and 2FA recovery keys are stripped or masked before logging.
2. **Deterministic Deduplication:** Duplicate high-frequency telemetry events (e.g. repeated progress ticks) are coalesced by `state_tracker.py` to prevent disk bloat.
3. **Immutability:** Log files are append-only; historical entries are never overwritten or reordered.

For complete logging specifications, refer to [docs/03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md](../docs/03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md).
