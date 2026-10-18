# 20-Tool Scraping Engines & Adapter Modules (`tools/`)

The `tools/` directory hosts the 20 specialized crawling, archiving, and multimodal extraction engines that power `Crawlers_testing`.

---

## 📂 Subdirectory Architecture

Each tool maintains an isolated package adhering to a standardized contract:

```
tools/<tool_id>/
├── adapter.py              # Standardized crawler execution wrapper
├── indexer.py              # Tool-specific domain metric extractor (BaseToolIndexer)
├── config.json             # Tool metadata, runtime flags, and supported actions
└── logs/
    └── tool_ops.jsonl      # Tier 2 tool operations log (Rule 2 Compliance)
```

---

## 🗂️ Cohort Breakdown

### Batch 1: High-Speed HTTP & DOM Slicers
- `01_curl_cffi`: TLS/JA3/JA4 fingerprint impersonation linked against Google BoringSSL.
- `02_selectolax_lxml`: Ultra-fast C-engine HTML parser (Modest engine) avoiding Python GIL overhead.
- `03_scrapy`: Industrial-grade async crawling framework with built-in item pipelines.
- `04_httpx_parsel`: Modern async HTTP/2 client paired with Scrapy-grade Parsel selectors.
- `05_trafilatura`: Density-based boilerplate slicer producing clean CommonMark editorial text.

### Batch 2: Standard, Stealth & Adaptive Browsers
- `06_playwright`: Cross-browser automation engine for Chromium, Firefox, and WebKit.
- `07_patchright`: C++ binary-patched Playwright fork removing internal CDP detection leaks.
- `08_camoufox`: Anti-detect Firefox engine randomizing canvas, WebGL, and font entropy per run.
- `09_nodriver`: Webdriver-less controller communicating via raw asynchronous WebSocket CDP frames.
- `10_scrapling`: AI-powered adaptive scraper that auto-heals broken selectors via semantic graph distance.

### Batch 3: Stream Demuxing, Archivers & MITM Interceptors
- `11_yt_dlp_ffmpeg`: Universal media downloader and stream demuxer for HLS (`.m3u8`) and DASH (`.mpd`).
- `12_instaloader`: Dedicated Instagram GraphQL archiver for profiles, reels, and feeds.
- `13_gallery_dl`: Command-line gallery downloader for 200+ visual communities (Reddit, Pinterest).
- `14_singlefile_archive`: Inlines all CSS, fonts, and images into Base64 for offline single-file HTML archives.
- `15_mitmproxy_interceptor`: In-memory TLS proxy capturing raw XHR/GraphQL streams before DOM rendering.

### Batch 4: Multimodal Visual OCR, Document AI & Speech Graphs
- `16_crawl4ai`: Async crawler producing token-efficient, LLM-ready Markdown chunks.
- `17_surya_ocr`: 90+ language document layout OCR with reading-order detection.
- `18_paddleocr_img2table`: Combines PaddleOCR with img2table to parse raster tables into CSV/Excel.
- `19_docling_pdf`: IBM document parsing toolkit converting multi-column PDFs into structured JSON.
- `20_faster_whisper_scrapegraph`: 4x faster local Whisper speech-to-text + ScrapeGraph knowledge graph AI.

---

## 📄 Manifest

All tools, batches, and supported actions are registered in [`tools/registry.json`](registry.json). For deep profiles of every tool, refer to [docs/03_folder_and_file_reference/03_20_tools_adapter_catalog.md](../docs/03_folder_and_file_reference/03_20_tools_adapter_catalog.md).
