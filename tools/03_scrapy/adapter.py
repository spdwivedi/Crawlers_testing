"""
tools/03_scrapy/adapter.py
==========================
Mechanism: Async Spider & Item Pipeline Framework
Default actions: catalog_crawl, scrape_for_leetcode

Executes a self-contained Scrapy spider inside a child subprocess
so Twisted's reactor is cleanly monitored by psutil in the Control Center.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.folder_manager import create_action_run, complete_action_run
from core.logger_engine import LogEngine
from core.state_tracker import start_task, update_progress, complete_task, fail_task

TOOL_ID = "03_scrapy"
SPIDER_RUNNER = Path(__file__).parent / "spider_runner.py"


def run_catalog_crawl(
    target_url: str = "https://quotes.toscrape.com/",
    action_name: str = "catalog_crawl",
) -> dict[str, Any]:
    """Execute Scrapy spider in subprocess and record outputs."""
    start_task(
        stage="Stage 1",
        step="Step 1.1",
        tool_id=TOOL_ID,
        action=action_name,
        subtask="Initializing Scrapy spider environment",
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

    logger.info(f"Initialized Scrapy run {run_info['run_id']} for {target_url}", progress_pct=15)
    update_progress(25, subtask="Spawning Scrapy crawler subprocess with Twisted reactor")

    cmd = [
        sys.executable,
        str(SPIDER_RUNNER),
        "--raw-dir", str(raw_dir),
        "--cleaned-dir", str(cleaned_dir),
        "--target-url", target_url,
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=25)
    elapsed_sec = round(time.perf_counter() - t0, 2)

    update_progress(70, subtask="Scrapy crawl finished — parsing spider output items")
    logger.info(f"Scrapy process finished (exit code {proc.returncode}) in {elapsed_sec}s", progress_pct=75)

    # Check and parse items
    jsonl_path = cleaned_dir / "scrapy_items.jsonl"
    stats_path = cleaned_dir / "spider_stats.json"

    items_count = 0
    if jsonl_path.exists():
        items_count = sum(1 for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip())

    stats = {}
    if stats_path.exists():
        try:
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    update_progress(90, subtask="Generating Scrapy crawl summary markdown")

    # Generate summary markdown
    summary_md = f"""# Scrapy Async Crawler Summary

**Tool:** `03_scrapy`
**Target URL:** `{target_url}`
**Exit Code:** `{proc.returncode}`
**Elapsed Time:** `{elapsed_sec}s`
**Items Scraped:** `{items_count}`
**Reactor:** `Twisted Engine (Subprocess Execution)`

---

## Spider Stats

```json
{json.dumps(stats, indent=2)}
```

## Items Output

Output written to: `cleaned/scrapy_items.jsonl` ({items_count} items).
"""
    (cleaned_dir / "spider_summary.md").write_text(summary_md, encoding="utf-8")

    update_progress(100, subtask="Scrapy crawl and pipeline complete")
    complete_action_run(run_info, status="completed")
    complete_task(message=f"03_scrapy crawl completed: {items_count} items in {elapsed_sec}s")

    logger.info(f"Completed Scrapy run: {items_count} items collected", progress_pct=100)

    return {
        "status": "completed",
        "tool_id": TOOL_ID,
        "action_name": action_name,
        "run_info": run_info,
        "items_scraped": items_count,
        "stats": stats,
    }


if __name__ == "__main__":
    res = run_catalog_crawl()
    print(json.dumps(res, indent=2, default=str))
