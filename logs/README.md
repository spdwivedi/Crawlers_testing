# 4-Tier Structured Logging Directory (`logs/`)

The `logs/` directory houses the global audit logs and stage-isolated milestone records enforcing Antigravity Governance Rule 2.

---

## 🏛️ 4-Tier Logging Architecture

Every diagnostic event, crawler run status, or system milestone is written to four distinct log tiers simultaneously:

```
logs/
├── global/                            # TIER 1 & TIER 2 LOGS
│   ├── antigravity_prompt_log.jsonl   # Tier 1: Machine-readable historical prompt log
│   ├── antigravity_prompt_log.md      # Tier 2: Human-readable markdown milestone table
│   └── live_state.json                # Live Telemetry State (WebSocket HUD feed at 1 Hz)
└── stages/                            # TIER 3 LOGS
    ├── stage_1_scaffolding.jsonl      # Stage 1 execution milestones
    ├── stage_2_indexing.jsonl         # Stage 2 dual-tier indexing milestones
    └── stage_3_credential_vault.jsonl # Stage 3 credential vault & security milestones

# TIER 4 LOGS (Located in Data Lake):
# data/<tool_id>/<action>/<date>/<run_id>/logs/action_run.jsonl
```

---

## 📜 JSONL Log Record Schema

```json
{
  "timestamp": "2026-10-18T18:04:36.192847+00:00",
  "level": "INFO",
  "stage": "Stage 3",
  "step": "Step 3.6",
  "tool_id": "backend",
  "action_name": "build_vault_api_and_tab5",
  "run_id": "run_180436_17b3",
  "message": "CHECK PASSED: POST /api/vault/accounts returns 200 OK",
  "elapsed_ms": 142,
  "progress_pct": 100
}
```

---

## ⚡ Live Log Streaming

The FastAPI backend (:8000) monitors `logs/global/*.jsonl` using the OS-native kernel file notifications (`watchdog`). Newly appended lines are streamed via WebSocket to connected browser clients (`/ws/logs`), rendering into the virtual-scrolling grid on frontend Tab 4 with sub-2ms latency.

For complete logging specifications, refer to [docs/03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md](../docs/03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md).
