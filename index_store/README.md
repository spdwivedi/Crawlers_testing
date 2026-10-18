# Dual-Tier Search Index Store (`index_store/`)

The `index_store/` directory houses the Gold Tier storage databases and full-text search indexes that enable sub-millisecond discovery across all scraped artifacts and logs.

---

## 🏛️ Two-Tier Storage Architecture

```
index_store/
├── global_master_index.sqlite         # Federated SQLite FTS5 Search Database (WAL Mode)
├── global_master_index.json           # Git-Tracked Companion Snapshot
└── tool_indexes/                      # 20 Dedicated Tool SQLite Databases
    ├── 01_curl_cffi.sqlite            # Tool 01 runs, files, and domain metrics
    ├── 01_curl_cffi_index.json        # Git-tracked JSON companion mirror
    └── ... [02 through 20]
```

---

## 🔍 Database Roles

1. **20 Isolated Tool Databases (`tool_indexes/<tool_id>.sqlite`):**
   - Stores isolated run histories, file manifests, and tool-specific KPIs (`domain_metrics_json`).
   - Ensures an error or corruption in one tool's database never impacts the other 19 engines.
2. **Global Master Index (`global_master_index.sqlite`):**
   - Federates records from all 20 tool databases into unified tables: `global_tools`, `global_runs`, `global_files`, `global_logs`.
   - Features two SQLite FTS5 virtual tables (`fts_artifacts`, `fts_logs`) compiled with `tokenize='porter unicode61'` for Okapi BM25 ranked full-text queries.
3. **Git-Tracked Companion JSON Files (`*_index.json`):**
   - Formatted JSON snapshots committed to Git to enable cross-platform inspection, code review, and CI verification without requiring SQLite binaries.

---

## ⚡ Concurrency PRAGMAs

All index databases strictly enforce high-concurrency PRAGMAs:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

For complete database schema specifications and BM25 formulations, refer to [docs/02_database_and_security/01_database_schemas_and_er_diagrams.md](../docs/02_database_and_security/01_database_schemas_and_er_diagrams.md).
