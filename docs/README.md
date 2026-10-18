# Master Engineering Documentation Spine (`docs/`)

The `docs/` directory contains the complete, textbook-grade technical specifications, architecture blueprints, data flow diagrams, database schemas, cryptographic proofs, and developer runbooks for `Crawlers_testing`.

---

## 📚 Documentation Modules

```
docs/
├── 01_architecture_and_flows/         # System Architecture, DFDs, State Machines & Sequences
│   ├── 01_system_architecture_overview.md   # 6-Layer Architecture & 7 Scraping Paradigms
│   ├── 02_dfd_level_0_1_2.md                # Data Dictionary & Context/Subsystem/Granular DFDs
│   ├── 03_state_diagrams.md                 # Mathematical State Machines (Telemetry, Vault, Runs)
│   └── 04_process_and_sequence_flows.md     # E2E Execution & Ephemeral Shredding Sequences
├── 02_database_and_security/          # Database Schemas, Search Spec & Cryptography
│   ├── 01_database_schemas_and_er_diagrams.md# Two-Tier Topology, PRAGMAs & 3x ER Diagrams
│   ├── 02_fts5_search_and_indexing_specification.md # Inverted Index, Unicode61 & BM25 Math
│   └── 03_cryptography_and_zero_leak_security_spec.md # AES-GCM Row-Binding Proofs & TOTP
├── 03_folder_and_file_reference/      # Directory Taxonomy, Code Reference & Tool Catalog
│   ├── 01_folder_structure_and_data_taxonomy.md # Bronze/Silver/Gold & Manifest Contracts
│   ├── 02_core_and_api_file_reference.md    # Core OOP Classes, REST Endpoints & WebSockets
│   └── 03_20_tools_adapter_catalog.md       # 20-Row Matrix & 20 Deep-Dive Profiles
└── 04_operations_and_guides/          # Developer Operations, Troubleshooting & Master Index
    ├── 01_developer_operations_and_runbook.md # Server Ops, CLI Commands & Regression Testing
    ├── 02_troubleshooting_and_resilience_guide.md # Windows File Locks & Anti-Bot Recovery
    └── 03_documentation_master_index.md     # Cross-Referenced Knowledge Index & Graph
```

---

## 🧭 Navigation Quicklinks

- **New Developer?** Start with the [System Architecture Overview](01_architecture_and_flows/01_system_architecture_overview.md) and [Developer Operations Runbook](04_operations_and_guides/01_developer_operations_and_runbook.md).
- **Working on Crawler Adapters?** Refer to the [20-Tool Adapter Catalog](03_folder_and_file_reference/03_20_tools_adapter_catalog.md) and [Data Taxonomy](03_folder_and_file_reference/01_folder_structure_and_data_taxonomy.md).
- **Database & Search Queries?** Read [Database Schemas & ER Diagrams](02_database_and_security/01_database_schemas_and_er_diagrams.md) and the [FTS5 Search Specification](02_database_and_security/02_fts5_search_and_indexing_specification.md).
- **Security & Credentials?** Study the [Cryptographic Security Specification](02_database_and_security/03_cryptography_and_zero_leak_security_spec.md).
- **Encountered an Error?** Check the [Troubleshooting & Resilience Guide](04_operations_and_guides/02_troubleshooting_and_resilience_guide.md).

For a complete topic index, see the [Documentation Master Index](04_operations_and_guides/03_documentation_master_index.md).
