"""
tools/05_trafilatura/adapter.py
===============================
Mechanism: Main-Content Boilerplate Stripping & Metadata Extraction
Default actions: article_extract, scrape_for_leetcode

Uses Trafilatura's heuristic algorithms to strip ads, navigation, headers,
and footers, extracting clean core markdown and structured document metadata.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.folder_manager import create_action_run, complete_action_run
from core.logger_engine import LogEngine
from core.state_tracker import start_task, update_progress, complete_task, fail_task

import trafilatura

TOOL_ID = "05_trafilatura"

ARTICLE_FIXTURE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Understanding Modern Web Crawlers and TLS Fingerprinting</title>
  <meta name="author" content="Antigravity Research Team">
  <meta name="date" content="2026-10-15">
  <meta name="description" content="A comprehensive analysis of JA3, HTTP/2 multiplexing, and stealth crawling strategies.">
</head>
<body>
  <header>
    <nav><ul><li><a href="/">Home</a></li><li><a href="/about">About</a></li><li><a href="/login">Sign In</a></li></ul></nav>
    <div class="ad-banner">Banner Ad — Subscribe Now!</div>
  </header>
  <main>
    <article>
      <h1>Understanding Modern Web Crawlers and TLS Fingerprinting</h1>
      <p class="byline">Published on October 15, 2026 by Antigravity Team</p>
      <p class="lead">Web scraping in modern production environments requires navigating advanced bot mitigation systems that inspect network protocol details.</p>
      
      <h2>1. TLS and JA3 Fingerprints</h2>
      <p>Traditional HTTP client libraries like Python requests send a fixed TLS Client Hello signature that easily gives away automation. In contrast, tools like <code>curl_cffi</code> impersonate real browser signatures.</p>

      <h2>2. Performance Comparison</h2>
      <p>The table below summarizes parser engine latencies:</p>
      <table>
        <thead>
          <tr><th>Parser</th><th>Engine</th><th>Average Latency</th></tr>
        </thead>
        <tbody>
          <tr><td>Selectolax</td><td>Lexbor (C)</td><td>&lt; 1 ms</td></tr>
          <tr><td>lxml</td><td>libxml2</td><td>~ 2.5 ms</td></tr>
          <tr><td>BeautifulSoup</td><td>Python / html.parser</td><td>~ 15 ms</td></tr>
        </tbody>
      </table>

      <h2>3. Boilerplate Removal</h2>
      <p>Trafilatura employs state-of-the-art text extraction algorithms to eliminate clutter while preserving lists, tables, and Markdown links.</p>
    </article>
  </main>
  <footer>
    <p>&copy; 2026 Crawlers Testing Lab. All rights reserved.</p>
    <div class="cookie-notice">We use cookies to enhance your experience.</div>
  </footer>
</body>
</html>
"""


def run_article_extract(
    target_url: str = "https://en.wikipedia.org/wiki/Web_crawler",
    action_name: str = "article_extract",
) -> dict[str, Any]:
    """Execute Trafilatura extraction with boilerplate removal and metadata parsing."""
    start_task(
        stage="Stage 1",
        step="Step 1.1",
        tool_id=TOOL_ID,
        action=action_name,
        subtask="Initializing Trafilatura extraction pipeline",
    )

    run_info = create_action_run(
        tool_id=TOOL_ID,
        action_name=action_name,
        target_url=target_url,
    )
    raw_dir = Path(run_info["raw_dir"])
    cleaned_dir = Path(run_info["cleaned_dir"])
    run_log_path = Path(run_info["log_file"])

    logger = LogEngine(
        tool_id=TOOL_ID,
        action_name=action_name,
        run_id=run_info["run_id"],
        run_log_path=run_log_path,
        stage="Stage 1",
        step="Step 1.1",
    )

    logger.info(f"Initialized Trafilatura run {run_info['run_id']} for {target_url}", progress_pct=15)
    update_progress(25, subtask="Fetching URL content via trafilatura.fetch_url")

    html_content = None
    fetch_source = "live"

    try:
        t0 = time.perf_counter()
        html_content = trafilatura.fetch_url(target_url)
        if not html_content or len(html_content) < 200:
            raise ValueError("Empty or truncated response")
        fetch_time = round(time.perf_counter() - t0, 3)
        logger.info(f"Fetched live article ({len(html_content)} bytes) in {fetch_time}s", progress_pct=45)
    except Exception as exc:
        fetch_source = "fixture"
        html_content = ARTICLE_FIXTURE.strip()
        logger.warn(f"Live fetch note ({exc}); using rich article fixture", progress_pct=45)

    update_progress(60, subtask="Saving raw HTML page to disk")
    (raw_dir / "raw_page.html").write_text(html_content, encoding="utf-8")

    update_progress(75, subtask="Extracting clean markdown and stripping boilerplates")

    # 1. Extract Markdown with links and tables
    extracted_md = trafilatura.extract(
        html_content,
        output_format="markdown",
        with_metadata=True,
        include_tables=True,
        include_links=True,
        include_images=False,
    ) or ""

    # 2. Extract Document Metadata
    meta_obj = trafilatura.extract_metadata(html_content)
    metadata = {}
    if meta_obj:
        metadata = {
            "title": meta_obj.title,
            "author": meta_obj.author,
            "url": meta_obj.url or target_url,
            "hostname": meta_obj.hostname,
            "description": meta_obj.description,
            "sitename": meta_obj.sitename,
            "date": meta_obj.date,
            "categories": meta_obj.categories,
            "tags": meta_obj.tags,
            "fingerprint": meta_obj.fingerprint,
        }

    update_progress(85, subtask="Writing extracted markdown and metadata JSON to disk")

    (cleaned_dir / "extracted_content.md").write_text(extracted_md, encoding="utf-8")
    (cleaned_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str), encoding="utf-8"
    )

    # Reduction ratio (boilerplate stripped)
    raw_size = len(html_content)
    clean_size = len(extracted_md)
    ratio = round((1.0 - (clean_size / max(raw_size, 1))) * 100, 1)

    logger.info(f"Boilerplate stripping: {raw_size} bytes -> {clean_size} bytes ({ratio}% reduction)", progress_pct=95)

    update_progress(100, subtask="Trafilatura extraction and metadata parsing complete")
    complete_action_run(run_info, status="completed")
    complete_task(message=f"05_trafilatura extract complete: {clean_size} chars extracted ({ratio}% boilerplate stripped)")

    logger.info("Run manifest finalized, 4-tier logs synchronized", progress_pct=100)

    return {
        "status": "completed",
        "tool_id": TOOL_ID,
        "action_name": action_name,
        "run_info": run_info,
        "fetch_source": fetch_source,
        "raw_size": raw_size,
        "cleaned_size": clean_size,
        "boilerplate_reduction_pct": f"{ratio}%",
        "title": metadata.get("title", ""),
    }


if __name__ == "__main__":
    res = run_article_extract()
    print(json.dumps(res, indent=2, default=str))
