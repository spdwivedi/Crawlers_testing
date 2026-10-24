# 🚀 Production Task Pipelines Architecture (`pipelines/`)

The `pipelines/` directory hosts the 4 production-grade end-to-end task pipelines that chain specialized crawler tools, credential vault authentication, human timing & kinematics, and Silver-Tier contract enforcement into automated workflows.

---

## 🏗️ The 4 Production Task Pipelines

| Pipeline | Entrypoint Script | Status | Core Adapters Chained | Primary Deliverable Contract | Operational Scope |
|:---|:---|:---:|:---|:---|:---|
| **Pipeline 1** | [`01_leetcode_archiver.py`](file:///d:/Project_Files/Crawlers_testing/pipelines/01_leetcode_archiver.py) | `VERIFIED` | `01_curl_cffi`, `core/cleaning_pipeline.py` | `CleanedCodeProblemContract` | Fetches LeetCode problem specifications via GraphQL with BoringSSL JA3 impersonation, normalizes HTML statements to CommonMark Markdown, extracts multi-language code templates, and parses test cases. |
| **Pipeline 2** | [`02_social_media_pipeline.py`](file:///d:/Project_Files/Crawlers_testing/pipelines/02_social_media_pipeline.py) | `VERIFIED` | `core/auth_injector.py`, `11_yt_dlp_ffmpeg`, `20_faster_whisper` | `CleanedSocialMediaContract` | Authenticated social media reel/post downloader with video demuxing, 16kHz mono audio extraction, INT8 Whisper speech transcription, and entity knowledge graph extraction. |
| **Pipeline 3** | [`03_secured_snapshot_forensics.py`](file:///d:/Project_Files/Crawlers_testing/pipelines/03_secured_snapshot_forensics.py) | `VERIFIED` | `07_patchright`, `14_singlefile_archive`, `15_mitmproxy_interceptor` | `CleanedForensicsContract` | Deep website security audit, wire forensics, single-file self-contained HTML archival, API endpoint discovery, third-party tracker audit, and security header evaluations. |
| **Pipeline 4** | [`04_multimodal_auto_resolver.py`](file:///d:/Project_Files/Crawlers_testing/pipelines/04_multimodal_auto_resolver.py) | `VERIFIED` | `06_playwright`, `17_surya_ocr`, `18_paddleocr_img2table`, `19_docling_pdf` | `CleanedMultimodalContract` | Visual question extraction, multi-column exam sheet parsing, table grid 3D matrix extraction, and document tree layout hierarchy analysis. |

---

## 🔬 Pipeline Specifications & CLI Operations

### Pipeline 1: LeetCode Problem Archiver
- **CLI Command:**
  ```powershell
  python pipelines/01_leetcode_archiver.py --slug "two-sum" --human-mode
  ```
- **Predecessor Handoffs:**
  - *Stage 1:* `01_curl_cffi` executes GraphQL query against LeetCode backend, saving `raw/graphql_payload.json` and `raw/raw_catalog_slice.json`.
  - *Stage 2:* `CleaningPipeline` normalizes payload into `cleaned/two_sum.md` (CommonMark with YAML frontmatter) and `cleaned/catalog_index.json`.
- **Contract Schema:** `CleanedCodeProblemContract` (`problem_id`, `title`, `slug`, `difficulty`, `tags`, `starter_snippets`, `sample_testcases`, `constraints`).

### Pipeline 2: Authenticated Social Media Reel & Whisper Pipeline
- **CLI Command:**
  ```powershell
  python pipelines/02_social_media_pipeline.py --url "https://instagram.com/reel/xyz" --account-id "acc_insta_001"
  ```
- **Predecessor Handoffs:**
  - *Stage 1:* `core/auth_injector.py` leases account session and injects ephemeral Netscape cookies.
  - *Stage 2:* `11_yt_dlp_ffmpeg` captures video stream, demuxes MP4, and extracts 16kHz WAV audio.
  - *Stage 3:* `20_faster_whisper` transcribes audio into SRT and synthesizes entity knowledge graph.
- **Contract Schema:** `CleanedSocialMediaContract` (`platform`, `post_id`, `author_handle`, `caption_text`, `media_files`, `transcript_srt_path`, `summary_text`).

### Pipeline 3: Secured Page Snapshot & Wire Forensics
- **CLI Command:**
  ```powershell
  python pipelines/03_secured_snapshot_forensics.py --url "https://httpbin.org/html"
  ```
- **Predecessor Handoffs:**
  - *Stage 1:* `07_patchright` navigates stealthily to page, avoiding bot detection markers.
  - *Stage 2:* `14_singlefile_archive` inlines all fonts, CSS, and images into Base64 self-contained HTML.
  - *Stage 3:* `15_mitmproxy_interceptor` audits network traffic, isolating API endpoints and third-party trackers.
- **Contract Schema:** `CleanedForensicsContract` (`target_url`, `final_url`, `status_code`, `singlefile_archive_path`, `discovered_api_endpoints`, `third_party_trackers`, `security_headers_audit`).

### Pipeline 4: Smart Multimodal Auto-Resolver
- **CLI Command:**
  ```powershell
  python pipelines/04_multimodal_auto_resolver.py --target "fixtures/sample_table.png" --modality "table_grid"
  ```
- **Predecessor Handoffs:**
  - *Stage 1:* Modality classifier evaluates file extension, MIME type, and raster content.
  - *Stage 2:* Dispatches to `17_surya_ocr`, `18_paddleocr_img2table`, or `19_docling_pdf`.
  - *Stage 3:* Cleans output into standardized 3D matrix JSON or document tree.
- **Contract Schema:** `CleanedMultimodalContract` (`source_image_or_pdf`, `content_type`, `extracted_text`, `confidence_score`, `table_matrices`, `bounding_boxes`, `structured_elements_count`).

---

## 🏛️ Governance Compliance

All pipelines strictly enforce Antigravity Governance:
- **Rule 1:** Live progress tracking via `core/cli_tracker.py`.
- **Rule 2:** Structured 4-tier logging into `logs/stages/stage_5_real_pipelines.jsonl`.
- **Rule 3:** Strict data isolation under `data/pipelines/<pipeline_id>/<date>/<run_id>/`.
- **Rule 4:** Atomic Git commits with pre-commit secret scanning.
- **Rule 5:** Automatic SQLite FTS5 master index synchronization.
- **Rule 6:** Zero-plaintext credential handling with 0x00 ephemeral cookie shredding.
- **Rule 7:** Statistical human delays via `core/human_timing.py`.
- **Rule 8:** Mandatory Silver-Tier contract validation via `core/cleaning_pipeline.py`.
- **Rule 9:** Non-destructive test traceability into pipeline run reports.
