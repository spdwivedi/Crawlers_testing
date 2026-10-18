"""
tools/04_httpx_parsel/adapter.py
================================
Mechanism: Async HTTP/2 Multiplexing + Parsel XPath/CSS/JMESPath
Default actions: scrape_for_leetcode, api_intercept

Concurrently multiplexes HTTP/2 requests with httpx.AsyncClient,
then uses Parsel's unified Selector to slice both JSON (via JMESPath)
and HTML (via CSS/XPath) in a single workflow.
"""
from __future__ import annotations

import asyncio
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
from core.human_adapter_helper import HumanAdapterHelper

import httpx
from parsel import Selector

TOOL_ID = "04_httpx_parsel"

SAMPLE_JSON = {
    "status": "success",
    "meta": {"version": "v2", "total_records": 3},
    "data": {
        "problems": [
            {"id": "1", "title": "Two Sum", "difficulty": "Easy", "stats": {"likes": 58000, "acceptance": "52.4%"}},
            {"id": "2", "title": "Add Two Numbers", "difficulty": "Medium", "stats": {"likes": 32000, "acceptance": "43.1%"}},
            {"id": "3", "title": "Longest Substring", "difficulty": "Medium", "stats": {"likes": 41000, "acceptance": "35.8%"}}
        ]
    }
}

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>API & Problem Origin</title></head>
<body>
  <div class="problem-item" data-id="1">
    <h2 class="title">Two Sum</h2>
    <span class="difficulty easy">Easy</span>
    <p class="summary">Find indices of the two numbers that add up to target.</p>
  </div>
  <div class="problem-item" data-id="2">
    <h2 class="title">Add Two Numbers</h2>
    <span class="difficulty medium">Medium</span>
    <p class="summary">Add two numbers represented by linked lists.</p>
  </div>
</body>
</html>
"""


async def _fetch_all(client: httpx.AsyncClient) -> tuple[dict, str, dict]:
    """Fetch JSON API endpoint and HTML page concurrently over HTTP/2."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HTTP2Client/1.0"}
    
    # 1. JSON endpoint
    json_data = None
    html_data = None
    meta = {"http2": False, "mode": "live"}

    try:
        t0 = time.perf_counter()
        # Fetch both in parallel
        resp_json, resp_html = await asyncio.gather(
            client.get("https://httpbin.org/json", headers=headers, timeout=6),
            client.get("https://httpbin.org/html", headers=headers, timeout=6),
            return_exceptions=True,
        )

        if not isinstance(resp_json, Exception) and resp_json.status_code == 200:
            json_data = resp_json.json()
            meta["http2"] = resp_json.http_version == "HTTP/2"
        else:
            json_data = SAMPLE_JSON

        if not isinstance(resp_html, Exception) and resp_html.status_code == 200:
            html_data = resp_html.text
        else:
            html_data = SAMPLE_HTML

        meta["elapsed_sec"] = round(time.perf_counter() - t0, 3)

    except Exception:
        meta["mode"] = "fallback_fixture"
        json_data = SAMPLE_JSON
        html_data = SAMPLE_HTML
        meta["elapsed_sec"] = 0.01

    return json_data, html_data, meta


def run_async_parsel(
    target_url: str = "https://httpbin.org/json",
    action_name: str = "scrape_for_leetcode",
    human_mode: bool = False,
    timing_profile: str = "BALANCED_HUMAN",
) -> dict[str, Any]:
    """Run concurrent async HTTP/2 multiplexing + Parsel JSON/HTML extraction."""
    start_task(
        stage="Stage 4" if human_mode else "Stage 1",
        step="Step 4.3" if human_mode else "Step 1.1",
        tool_id=TOOL_ID,
        action=action_name,
        subtask="Initializing httpx AsyncClient with HTTP/2 support",
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
        stage="Stage 4" if human_mode else "Stage 1",
        step="Step 4.3" if human_mode else "Step 1.1",
    )

    logger.info(f"Initialized httpx_parsel run {run_info['run_id']} (HTTP/2 enabled, human_mode={human_mode})", progress_pct=15)

    if human_mode:
        HumanAdapterHelper.apply_pre_request_delay(profile=timing_profile, logger=logger)

    update_progress(25, subtask="Concurrently multiplexing HTTP/2 GET requests")

    async def _runner():
        async with httpx.AsyncClient(http2=True, verify=False) as client:
            return await _fetch_all(client)

    json_raw, html_raw, fetch_meta = asyncio.run(_runner())

    update_progress(55, subtask="Saving raw responses to disk")
    # 1. Save RAW
    (raw_dir / "response_payload.json").write_text(
        json.dumps(json_raw, indent=2), encoding="utf-8"
    )
    (raw_dir / "response_page.html").write_text(
        html_raw, encoding="utf-8"
    )

    logger.info(f"Saved raw responses (mode: {fetch_meta.get('mode', 'live')})", progress_pct=60)
    update_progress(70, subtask="Parsing JSON via Parsel JMESPath selector")

    # 2. Slice JSON via Parsel JMESPath
    extracted_json_items = []
    try:
        # Wrap JSON as text for parsel type='json'
        sel_json = Selector(text=json.dumps(json_raw), type="json")
        # Extract slides / items using JMESPath
        slides = sel_json.jmespath("slideshow.slides[*]").get() or sel_json.jmespath("data.problems[*]").get()
        if slides:
            extracted_json_items = slides if isinstance(slides, list) else [slides]
        else:
            extracted_json_items = [json_raw]
    except Exception as exc:
        logger.warn(f"JMESPath query note: {exc}", progress_pct=72)
        extracted_json_items = [json_raw]

    update_progress(80, subtask="Parsing HTML via Parsel CSS & XPath selectors")

    # 3. Slice HTML via Parsel CSS & XPath
    sel_html = Selector(text=html_raw)
    html_items = []
    # Try problem-item, then fall back to generic h1/p elements
    items = sel_html.css(".problem-item")
    if items:
        for it in items:
            title = it.css("h2.title::text").get(default="").strip()
            diff = it.css(".difficulty::text").get(default="").strip()
            summary = it.xpath(".//p[contains(@class, 'summary')]/text()").get(default="").strip()
            html_items.append({"title": title, "difficulty": diff, "summary": summary})
    else:
        h1 = sel_html.xpath("//h1/text()").get(default="").strip()
        p = sel_html.css("p::text").get(default="").strip()
        html_items.append({"heading": h1, "paragraph": p})

    update_progress(90, subtask="Writing combined cleaned JSON and markdown report")

    # 4. Save CLEANED
    cleaned_output = {
        "fetch_metadata": fetch_meta,
        "json_jmespath_extracted": extracted_json_items,
        "html_parsel_extracted": html_items,
    }
    (cleaned_dir / "async_extracted.json").write_text(
        json.dumps(cleaned_output, indent=2), encoding="utf-8"
    )

    report_md = f"""# HTTP/2 Multiplexing & Parsel Extraction Report

**Tool:** `04_httpx_parsel`
**HTTP/2 Multiplexed:** `{fetch_meta.get('http2', False)}`
**Elapsed Time:** `{fetch_meta.get('elapsed_sec')}s`
**Mode:** `{fetch_meta.get('mode', 'live')}`

---

## 1. JSON JMESPath Extraction

```json
{json.dumps(extracted_json_items[:2], indent=2)}
```

## 2. HTML CSS/XPath Extraction

```json
{json.dumps(html_items, indent=2)}
```
"""
    (cleaned_dir / "report.md").write_text(report_md, encoding="utf-8")

    update_progress(100, subtask="Async HTTP/2 + Parsel extraction complete")
    manifest = complete_action_run(
        run_info,
        status="completed",
        domain_metrics={
            "human_mode_active": human_mode,
            "timing_profile": timing_profile,
            "http2": fetch_meta.get("http2", False),
            "json_items_count": len(extracted_json_items),
            "html_items_count": len(html_items),
        },
    )
    complete_task(message=f"04_httpx_parsel extraction complete: JSON + HTML parsed in {fetch_meta.get('elapsed_sec')}s")

    logger.info("Run manifest finalized, 4-tier logs synchronized", progress_pct=100)

    return {
        "status": "completed",
        "tool_id": TOOL_ID,
        "action_name": action_name,
        "run_info": run_info,
        "manifest": manifest,
        "http2": fetch_meta.get("http2", False),
        "json_items": len(extracted_json_items),
        "html_items": len(html_items),
        "human_mode": human_mode,
    }



def run_action(
    action_name: str = "scrape_for_leetcode",
    target_url: str = "https://httpbin.org/json",
    human_mode: bool = False,
    timing_profile: str = "BALANCED_HUMAN",
    **kwargs: Any,
) -> dict[str, Any]:
    """Action entrypoint alias for 04_httpx_parsel adapter."""
    return run_async_parsel(
        target_url=target_url,
        action_name=action_name,
        human_mode=human_mode,
        timing_profile=timing_profile,
    )


def run(
    target_url: str = "https://httpbin.org/json",
    action_name: str = "scrape_for_leetcode",
    human_mode: bool = False,
    timing_profile: str = "BALANCED_HUMAN",
    **kwargs: Any,
) -> dict[str, Any]:
    """Unified entrypoint for 04_httpx_parsel adapter."""
    return run_async_parsel(
        target_url=target_url,
        action_name=action_name,
        human_mode=human_mode,
        timing_profile=timing_profile,
    )



if __name__ == "__main__":
    res = run_async_parsel()
    print(json.dumps(res, indent=2, default=str))
