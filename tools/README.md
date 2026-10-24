# 20-Tool Scraping Engines & Adapter Modules (`tools/`)

The `tools/` directory hosts the 20 specialized crawling, archiving, browser automation, and multimodal extraction engines that power `Crawlers_testing`.

---

## 📂 Adapter Architecture & Contract Standards

Every tool is encapsulated within its own isolated package adhering strictly to the three-tier adapter contract:

```
tools/<tool_id>/
├── adapter.py              # Standardized crawler execution wrapper
├── indexer.py              # Tool-specific domain metric extractor (BaseToolIndexer)
├── config.json             # Engine metadata, capabilities, and supported actions
└── logs/
    └── tool_ops.jsonl      # Tier 2 tool operations log (Rule 2 Compliance)
```

### 1. The `adapter.py` Execution Contract
Every `adapter.py` must expose a primary entrypoint function:
```python
def run(
    target_url: str,
    action_name: str = "default_action",
    human_mode: bool = False,
    timing_profile: str = "BALANCED_HUMAN",
    auth_account_id: str = "",
    auth_target: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Executes the crawler against target_url.
    Returns:
        {
            "run_id": str,
            "status": "success" | "failed",
            "elapsed_seconds": float,
            "raw_output_path": str,
            "cleaned_output_path": str,
            "domain_metrics": dict[str, Any]
        }
    """
```

### 2. The `indexer.py` Extraction Contract
Inherits from `core.base_indexer.BaseToolIndexer`:
```python
class ToolIndexer(BaseToolIndexer):
    def extract_domain_metrics(self, run_info: dict[str, Any]) -> dict[str, Any]:
        """Extracts tool-specific KPIs (e.g. JA3 hash, OCR confidence, demux duration)."""
```

### 3. The `config.json` Manifest Contract
Defines tool identification, cohort assignment, and execution capabilities:
```json
{
  "tool_id": "01_curl_cffi",
  "name": "Curl CFFI (TLS Impersonation)",
  "batch": 1,
  "mechanism_type": "HTTP / TLS Impersonation",
  "supported_actions": ["scrape_for_leetcode", "tls_fingerprint_test"],
  "human_mode_supported": true
}
```

---

## 🗂️ Cohort Breakdown (Batches 1 to 4)

### Batch 1: High-Speed HTTP & DOM Slicers
- `01_curl_cffi`: TLS/JA3/JA4 fingerprint impersonation linked against Google BoringSSL. Bypasses Cloudflare JA3 checks.
  - *Domain Metrics:* `ja3_fingerprint`, `http_version`, `tls_negotiated_cipher`.
- `02_selectolax_lxml`: Ultra-fast C-engine HTML parser (Modest engine) avoiding Python object allocations.
  - *Domain Metrics:* `nodes_parsed_per_sec`, `memory_rss_delta_mb`.
- `03_scrapy`: Industrial-grade async crawling framework with built-in item pipelines and autothrottle.
  - *Domain Metrics:* `items_scraped_count`, `response_status_distribution`.
- `04_httpx_parsel`: Modern async HTTP/2 client paired with Scrapy-grade Parsel selectors.
  - *Domain Metrics:* `http2_stream_id`, `async_concurrency_level`.
- `05_trafilatura`: Density-based boilerplate slicer producing clean CommonMark editorial text.
  - *Domain Metrics:* `boilerplate_reduction_pct`, `word_count`.

### Batch 2: Standard, Stealth & Adaptive Browsers
- `06_playwright`: Cross-browser automation engine for Chromium, Firefox, and WebKit.
  - *Domain Metrics:* `navigation_timing_dom_content_loaded`, `har_network_requests_count`.
- `07_patchright`: C++ binary-patched Playwright fork removing internal CDP detection leaks.
  - *Domain Metrics:* `window_cdc_unhooked`, `turnstile_passed`.
- `08_camoufox`: Anti-detect Firefox engine randomizing canvas, WebGL, and font entropy per run.
  - *Domain Metrics:* `font_fingerprint_hash`, `webgl_vendor_spoofed`.
- `09_nodriver`: Webdriver-less controller communicating via raw asynchronous WebSocket CDP frames.
  - *Domain Metrics:* `raw_cdp_frames_exchanged`, `memory_peak_mb`.
- `10_scrapling`: AI-powered adaptive scraper that auto-heals broken selectors via semantic graph distance.
  - *Domain Metrics:* `selector_healed_count`, `semantic_confidence_score`.

### Batch 3: Stream Demuxing, Archivers & MITM Interceptors
- `11_yt_dlp_ffmpeg`: Universal media downloader and stream demuxer for HLS (`.m3u8`) and DASH (`.mpd`).
  - *Domain Metrics:* `demuxed_video_duration_sec`, `audio_sample_rate_hz`.
- `12_instaloader`: Dedicated Instagram GraphQL archiver for profiles, reels, and feeds.
  - *Domain Metrics:* `graphql_query_hashes`, `posts_harvested_count`.
- `13_gallery_dl`: Command-line gallery downloader for 200+ visual communities (Reddit, Pinterest).
  - *Domain Metrics:* `images_downloaded_count`, `total_media_bytes`.
- `14_singlefile_archive`: Inlines all CSS, fonts, and images into Base64 for offline single-file HTML archives.
  - *Domain Metrics:* `inlined_assets_count`, `archive_size_bytes`.
- `15_mitmproxy_interceptor`: In-memory TLS proxy capturing raw XHR/GraphQL streams before DOM rendering.
  - *Domain Metrics:* `xhr_endpoints_intercepted_count`, `decrypted_tls_flows_count`.

### Batch 4: Multimodal Visual OCR, Document AI & Speech Graphs
- `16_crawl4ai`: Async crawler producing token-efficient, LLM-ready Markdown chunks.
  - *Domain Metrics:* `llm_markdown_tokens_est`, `compression_ratio`.
- `17_surya_ocr`: 90+ language document layout OCR with reading-order detection.
  - *Domain Metrics:* `ocr_confidence_mean`, `bounding_boxes_count`.
- `18_paddleocr_img2table`: Combines PaddleOCR with img2table to parse raster tables into CSV/Excel.
  - *Domain Metrics:* `tables_detected_count`, `matrix_dimensions_cells`.
- `19_docling_pdf`: IBM document parsing toolkit converting multi-column PDFs into structured JSON.
  - *Domain Metrics:* `document_nodes_count`, `footnotes_and_formulas_count`.
- `20_faster_whisper_scrapegraph`: 4x faster local Whisper speech-to-text + ScrapeGraph knowledge graph AI.
  - *Domain Metrics:* `transcript_word_error_rate_est`, `entities_extracted_count`.

---

## 📄 Registry Manifest

All tools, cohorts, and supported actions are registered in [`tools/registry.json`](registry.json). For deep profiles of every tool, refer to [docs/03_folder_and_file_reference/03_20_tools_adapter_catalog.md](../docs/03_folder_and_file_reference/03_20_tools_adapter_catalog.md).
