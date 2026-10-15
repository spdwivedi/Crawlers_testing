"""
tools/02_selectolax_lxml/adapter.py
===================================
Mechanism: C-Engine Lexbor CSS + lxml XPath Tree Parsing
Default actions: catalog_parse, scrape_for_leetcode

Benchmarks ultra-fast C-based Lexbor HTML parsing against lxml XPath tree navigation,
extracting structured catalog data and comparing microsecond execution speeds.
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

import urllib.request
from selectolax.lexbor import LexborHTMLParser
import lxml.html

TOOL_ID = "02_selectolax_lxml"

# High-fidelity fallback catalog HTML fixture if network unavailable
CATALOG_FIXTURE = """
<!DOCTYPE html>
<html lang="en">
<head><title>Algorithms & Data Structures Catalog</title></head>
<body>
  <div class="container">
    <header><h1>Problem & Catalog Index</h1></header>
    <main class="catalog-grid">
      <article class="problem-card" data-id="1" data-difficulty="Easy">
        <h3 class="problem-title"><a href="/problems/two-sum">Two Sum</a></h3>
        <span class="difficulty easy">Easy</span>
        <div class="tags"><span class="tag">Array</span><span class="tag">Hash Table</span></div>
        <p class="description">Given an array of integers nums and an integer target, return indices of the two numbers.</p>
        <span class="acceptance">Acceptance: 52.4%</span>
      </article>
      <article class="problem-card" data-id="2" data-difficulty="Medium">
        <h3 class="problem-title"><a href="/problems/add-two-numbers">Add Two Numbers</a></h3>
        <span class="difficulty medium">Medium</span>
        <div class="tags"><span class="tag">Linked List</span><span class="tag">Math</span></div>
        <p class="description">You are given two non-empty linked lists representing two non-negative integers.</p>
        <span class="acceptance">Acceptance: 43.1%</span>
      </article>
      <article class="problem-card" data-id="3" data-difficulty="Medium">
        <h3 class="problem-title"><a href="/problems/longest-substring">Longest Substring Without Repeating Characters</a></h3>
        <span class="difficulty medium">Medium</span>
        <div class="tags"><span class="tag">Hash Table</span><span class="tag">Sliding Window</span></div>
        <p class="description">Given a string s, find the length of the longest substring without duplicate characters.</p>
        <span class="acceptance">Acceptance: 35.8%</span>
      </article>
      <article class="problem-card" data-id="4" data-difficulty="Hard">
        <h3 class="problem-title"><a href="/problems/median-of-two-sorted-arrays">Median of Two Sorted Arrays</a></h3>
        <span class="difficulty hard">Hard</span>
        <div class="tags"><span class="tag">Array</span><span class="tag">Binary Search</span></div>
        <p class="description">Given two sorted arrays nums1 and nums2, return the median of the two sorted arrays.</p>
        <span class="acceptance">Acceptance: 40.2%</span>
      </article>
      <article class="problem-card" data-id="5" data-difficulty="Medium">
        <h3 class="problem-title"><a href="/problems/longest-palindromic-substring">Longest Palindromic Substring</a></h3>
        <span class="difficulty medium">Medium</span>
        <div class="tags"><span class="tag">String</span><span class="tag">Dynamic Programming</span></div>
        <p class="description">Given a string s, return the longest palindromic substring in s.</p>
        <span class="acceptance">Acceptance: 34.5%</span>
      </article>
    </main>
  </div>
</body>
</html>
"""


def run_catalog_parse(
    target_url: str = "https://books.toscrape.com/",
    action_name: str = "scrape_for_leetcode",
) -> dict[str, Any]:
    """Execute dual parsing benchmark using Selectolax Lexbor (CSS) and lxml (XPath)."""
    start_task(
        stage="Stage 1",
        step="Step 1.1",
        tool_id=TOOL_ID,
        action=action_name,
        subtask="Initializing Selectolax Lexbor and lxml parsers",
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

    logger.info(f"Initialized dual-parser run {run_info['run_id']}", progress_pct=10)
    update_progress(20, subtask="Fetching catalog source HTML")

    html_content = ""
    source_type = "live"

    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html_content = response.read().decode("utf-8", errors="replace")
        logger.info(f"Fetched live HTML from {target_url} ({len(html_content)} bytes)", progress_pct=35)
    except Exception as exc:
        source_type = "fixture"
        html_content = CATALOG_FIXTURE.strip()
        logger.warn(f"Live fetch failed ({exc}); using rich HTML catalog fixture", progress_pct=35)

    # Save RAW HTML
    update_progress(45, subtask="Writing raw source page HTML to disk")
    (raw_dir / "source_page.html").write_text(html_content, encoding="utf-8")

    # ─── BENCHMARK 1: Selectolax Lexbor (C Engine, CSS Selectors) ──────────────
    update_progress(55, subtask="Benchmarking Selectolax Lexbor C engine parser")
    t0 = time.perf_counter_ns()
    parser_lex = LexborHTMLParser(html_content)
    # Extract items using CSS
    selectolax_items = []
    # Try problem card selectors first, then fallback to books.toscrape selectors
    cards = parser_lex.css("article.problem-card") or parser_lex.css("article.product_pod")
    for card in cards:
        title_el = card.css_first("h3 a")
        title = title_el.text(strip=True) if title_el else ""
        href = title_el.attributes.get("href", "") if title_el else ""
        diff_el = card.css_first(".difficulty") or card.css_first(".star-rating")
        difficulty = diff_el.text(strip=True) if diff_el else (diff_el.attributes.get("class", "") if diff_el else "")
        tags = [t.text(strip=True) for t in card.css(".tag")]
        desc_el = card.css_first("p.description") or card.css_first(".price_color")
        desc = desc_el.text(strip=True) if desc_el else ""
        selectolax_items.append({
            "title": title,
            "url": href,
            "difficulty": difficulty,
            "tags": tags,
            "description_or_meta": desc,
        })
    t_lexbor_ns = time.perf_counter_ns() - t0
    t_lexbor_us = round(t_lexbor_ns / 1_000, 2)
    t_lexbor_ms = round(t_lexbor_ns / 1_000_000, 3)

    logger.info(f"Selectolax parsed {len(selectolax_items)} items in {t_lexbor_us} us ({t_lexbor_ms} ms)", progress_pct=65)

    # ─── BENCHMARK 2: lxml XPath Tree ──────────────────────────────────────────
    update_progress(75, subtask="Benchmarking lxml XPath tree navigation")
    t1 = time.perf_counter_ns()
    tree = lxml.html.fromstring(html_content.encode("utf-8"))
    lxml_items = []
    nodes = tree.xpath("//article[contains(@class, 'problem-card')] | //article[contains(@class, 'product_pod')]")
    for node in nodes:
        title_nodes = node.xpath(".//h3/a")
        title = title_nodes[0].text_content().strip() if title_nodes else ""
        href = title_nodes[0].get("href", "") if title_nodes else ""
        diff_nodes = node.xpath(".//*[contains(@class, 'difficulty')] | .//*[contains(@class, 'star-rating')]")
        difficulty = diff_nodes[0].text_content().strip() if diff_nodes else ""
        tag_nodes = node.xpath(".//*[contains(@class, 'tag')]")
        tags = [t.text_content().strip() for t in tag_nodes]
        desc_nodes = node.xpath(".//p[contains(@class, 'description')] | .//*[contains(@class, 'price_color')]")
        desc = desc_nodes[0].text_content().strip() if desc_nodes else ""
        lxml_items.append({
            "title": title,
            "url": href,
            "difficulty": difficulty,
            "tags": tags,
            "description_or_meta": desc,
        })
    t_lxml_ns = time.perf_counter_ns() - t1
    t_lxml_us = round(t_lxml_ns / 1_000, 2)
    t_lxml_ms = round(t_lxml_ns / 1_000_000, 3)

    logger.info(f"lxml XPath parsed {len(lxml_items)} items in {t_lxml_us} us ({t_lxml_ms} ms)", progress_pct=85)

    # Calculate comparison
    ratio = round(t_lxml_us / max(t_lexbor_us, 0.001), 2)
    faster = "selectolax (Lexbor C Engine)" if t_lexbor_us <= t_lxml_us else "lxml"

    benchmark_stats = {
        "source_type": source_type,
        "html_bytes": len(html_content),
        "items_extracted": len(selectolax_items),
        "selectolax_lexbor_us": t_lexbor_us,
        "selectolax_lexbor_ms": t_lexbor_ms,
        "lxml_xpath_us": t_lxml_us,
        "lxml_xpath_ms": t_lxml_ms,
        "ratio_speedup": f"{ratio}x",
        "faster_engine": faster,
    }

    # ─── SAVE CLEANED OUTPUTS ──────────────────────────────────────────────────
    update_progress(90, subtask="Saving structured catalog and benchmark report")
    output_data = {
        "benchmark": benchmark_stats,
        "items": selectolax_items,
    }
    (cleaned_dir / "parsed_catalog.json").write_text(
        json.dumps(output_data, indent=2), encoding="utf-8"
    )

    summary_md = f"""# Parser Benchmark Summary — Selectolax vs lxml

**Tool:** `02_selectolax_lxml`
**Source:** `{source_type}` ({len(html_content)} bytes)
**Items Extracted:** `{len(selectolax_items)}`

---

## Benchmark Results

| Parser Engine | Selector Syntax | Time (μs) | Time (ms) | Speed Rank |
|---|---|---|---|---|
| **Selectolax (Lexbor C Engine)** | CSS Selectors | `{t_lexbor_us} μs` | `{t_lexbor_ms} ms` | {'1st (Fastest)' if faster.startswith('selectolax') else '2nd'} |
| **lxml (libxml2 / libxslt)** | XPath Tree | `{t_lxml_us} μs` | `{t_lxml_ms} ms` | {'1st (Fastest)' if faster.startswith('lxml') else '2nd'} |

**Performance Factor:** `{faster}` was `{ratio}x` as fast in this benchmark.

---

## Extracted Catalog Items (Sample)

{json.dumps(selectolax_items[:3], indent=2)}
"""
    (cleaned_dir / "summary.md").write_text(summary_md, encoding="utf-8")

    update_progress(100, subtask="Selectolax + lxml parse and benchmark complete")
    complete_action_run(run_info, status="completed")
    complete_task(message=f"02_selectolax_lxml parse complete: {len(selectolax_items)} items in {t_lexbor_ms}ms (Selectolax) vs {t_lxml_ms}ms (lxml)")

    logger.info("Run manifest finalized, 4-tier logs synchronized", progress_pct=100)

    return {
        "status": "completed",
        "tool_id": TOOL_ID,
        "action_name": action_name,
        "run_info": run_info,
        "benchmark": benchmark_stats,
        "items_count": len(selectolax_items),
    }


if __name__ == "__main__":
    res = run_catalog_parse()
    print(json.dumps(res, indent=2, default=str))
