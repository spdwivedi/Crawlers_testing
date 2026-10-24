# Dual-Tier Search Index & Persistent Reports Store (`index_store/`)

The `index_store/` directory houses the Gold Tier storage databases, full-text search indexes, and structured analytical report repositories that enable sub-millisecond discovery, tournament evaluation, and historical telemetry analysis across all scraped artifacts and logs.

---

## 🏛️ Storage Layout & Directory Structure

```
index_store/
├── global_master_index.sqlite         # Federated SQLite FTS5 Search Database (WAL Mode)
├── global_master_index.json           # Git-Tracked Master Metadata Snapshot
│
├── tool_indexes/                      # 20 Dedicated Tool SQLite Databases
│   ├── 01_curl_cffi.sqlite            # Tool 01 runs, files, and domain metrics
│   ├── 01_curl_cffi_index.json        # Git-tracked JSON companion mirror
│   └── ... [02 through 20]
│
├── arena_reports/                     # Safe Arena Multi-Tool Tournament Reports
│   ├── arena_run_<timestamp>_<id>.json # Structured tournament comparison matrix
│   └── arena_run_<timestamp>_<id>.md   # Human-readable executive evaluation markdown
│
├── pipeline_reports/                  # Production Task Pipeline Execution Reports
│   ├── pipeline_run_<timestamp>_<id>.json # Multi-stage pipeline execution metrics
│   └── pipeline_run_<timestamp>_<id>.md   # Human-readable pipeline summary report
│
├── benchmark_reports/                 # 20-Tool Master Benchmark Performance Reports
│   ├── benchmark_run_<timestamp>_<id>.json # Statistical latency percentiles (p50/p90/p99)
│   └── benchmark_run_<timestamp>_<id>.md   # Radar matrix & composite scoring report
│
└── resilience_reports/                # Chaos & Anti-Bot Stress Test Reports
    ├── resilience_run_<timestamp>_<id>.json # Fault-injection drill evaluations
    └── resilience_run_<timestamp>_<id>.md   # Chaos test recovery analysis report
```

---

## 🔍 Database Architecture & Search Specifications

### 1. The 20 Isolated Tool Databases (`tool_indexes/<tool_id>.sqlite`)
- Encapsulates tool-specific execution histories, file manifests, and unique domain metrics (`domain_metrics_json`).
- Prevents database contention: concurrent writes from different crawler engines operate in completely separate SQLite files.

### 2. Global Master Index (`global_master_index.sqlite`)
- Federates all tool runs, data lake files, and 4-tier logs into unified tables:
  - `global_tools`: Aggregate tool metrics, total runs, total bytes, and latest domain KPIs.
  - `global_runs`: Run-level telemetry, elapsed time, status, target URL, and git commit hash.
  - `global_files`: File catalog with SHA-256 digests, size bytes, and content previews.
  - `global_logs`: Unified audit log records across all stages and prompt executions.
- **SQLite FTS5 Full-Text Search:**
  - `fts_artifacts`: Virtual table indexing filename, content preview, and domain metrics using `tokenize='porter unicode61'`.
  - `fts_logs`: Virtual table indexing log level, stage, step, tool, and diagnostic message text.
  - Supports Okapi BM25 ranked queries, prefix matching (`q*`), and boolean operators (`AND`, `OR`, `NOT`).

### 3. Persistent Analytical Report Catalogs
- **Arena Reports (`arena_reports/`):** Captured by `SafeArenaRunner`. Documents candidate tools, staggered delay offsets, speed/richness/stealth/memory score breakdowns, and elected winner.
- **Pipeline Reports (`pipeline_reports/`):** Captured by `PrecisionTaskRouter`. Documents multi-stage dependency execution, artifact handoff manifests, and Silver-tier deliverable schemas.
- **Benchmark Reports (`benchmark_reports/`):** Captured by `BenchmarkEngine`. Documents multi-iteration latency percentiles ($p50/p90/p99$), memory RSS deltas, yield ratios, and radar spider matrix vectors.
- **Resilience Reports (`resilience_reports/`):** Captured by `ResilienceTester`. Documents fault injection drills across HTTP 429 backoff, DOM mutation fuzzing, socket faults, and Pydantic schema fuzzing.

---

## ⚡ Concurrency & Integrity PRAGMAs

All SQLite databases in `index_store/` strictly enforce high-performance write-ahead logging:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

For complete database schema specifications and BM25 formulations, refer to [docs/02_database_and_security/01_database_schemas_and_er_diagrams.md](../docs/02_database_and_security/01_database_schemas_and_er_diagrams.md).
