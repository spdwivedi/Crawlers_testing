# 🚀 Production Task Pipelines Architecture (Stage 5)

This directory hosts the 4 production-grade end-to-end task pipelines that chain specialized crawler tools, credential vault authentication, human timing & kinematics, and Silver-Tier contract enforcement.

---

## 🏗️ The 4 Production Task Pipelines

| Pipeline | Script | Status | Core Adapters Chained | Primary Deliverable Contract | Description |
|---|---|---|---|---|---|
| **Pipeline 1** | `01_leetcode_archiver.py` | `VERIFIED` | `01_curl_cffi` (TLS JA3), `core/cleaning_pipeline.py` | `CleanedCodeProblemContract` | Fetches LeetCode catalog and problem specifications via GraphQL, converts HTML problem statements to CommonMark, parses test cases and constraints, and extracts boilerplate starter codes for Python, JS, C++, and Java. |
| **Pipeline 2** | `02_social_media_pipeline.py` | `ACTIVE` | `11_yt_dlp_ffmpeg`, `20_faster_whisper`, `core/auth_injector.py` | `CleanedSocialMediaContract` | Authenticated social media post and reel archiver with video demuxing, Whisper INT8 transcription, and entity knowledge graph extraction. |
| **Pipeline 3** | `03_secured_snapshot_forensics.py` | `ACTIVE` | `14_singlefile_archive`, `07_patchright`, `06_playwright`, `core/cleaning_pipeline.py` | `CleanedForensicsContract` | Deep website security audit, wire forensics, single-file self-contained HTML archival, API endpoint discovery, and third-party tracker audit. |
| **Pipeline 4** | `04_multimodal_auto_resolver.py` | `ACTIVE` | `06_playwright`, `17_surya_ocr`, `18_paddleocr_img2table`, `19_docling_pdf`, `core/cleaning_pipeline.py` | `CleanedMultimodalContract` | Visual question extraction, multi-column exam sheet parsing, table grid 3D matrix extraction, and document tree layout hierarchy analysis. |

---

## 🏛️ Governance & Data Lake Silver Tier Contracts

All pipelines strictly adhere to the mandatory Antigravity governance rules:
1. **Rule 1 (Live State Telemetry):** Telemetry state is maintained via `core/cli_tracker.py` and `core/state_tracker.py`.
2. **Rule 2 (4-Tier Logging):** Events are recorded to Global JSONL/MD, `logs/stages/stage_5_real_pipelines.jsonl`, and action run logs.
3. **Rule 3 (Strict Data Isolation):** Output files are created under `data/pipelines/<pipeline_id>/<date>/<run_id>/` with isolated `raw/`, `cleaned/`, and `logs/` directories.
4. **Rule 4 (Atomic Git Commits):** Every pipeline phase concludes with an atomic Git commit guarded by pre-commit secret scanning.
5. **Rule 5 (Auto-Indexing):** Runs automatically update tool and master SQLite FTS5 indexes.
6. **Rule 6 (Zero-Plaintext Security):** Sensitive credentials and cookies are managed by `core/crypto_engine.py` and `core/credential_vault.py`.
7. **Rule 7 (Human Simulation & Timing Discipline):** Pacing delays follow `core/human_timing.py` statistical distributions.
8. **Rule 8 (Data Lake Silver Tier Contract Enforcement):** Outputs in `cleaned/` must validate against Pydantic schema contracts in `core/cleaning_pipeline.py`.
