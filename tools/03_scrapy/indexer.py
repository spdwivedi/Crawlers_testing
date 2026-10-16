"""
tools/03_scrapy/indexer.py
==========================
Dedicated Indexer for 03_scrapy.
Extracts spider items scraped, spider elapsed sec, and pipeline status.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import sys
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.base_indexer import BaseToolIndexer

class ToolIndexer(BaseToolIndexer):
    def __init__(self, tool_id: str = "03_scrapy"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "spider_items_scraped": 0,
            "spider_elapsed_sec": 0.0,
            "pipeline_status": "unknown",
        }
        stats_file = cleaned_dir / "spider_stats.json"
        if stats_file.exists():
            try:
                data = json.loads(stats_file.read_text(encoding="utf-8"))
                metrics["spider_items_scraped"] = data.get("items_scraped", 0)
                metrics["spider_elapsed_sec"] = data.get("elapsed_seconds", 0.0)
                metrics["pipeline_status"] = data.get("close_reason", "finished")
            except Exception:
                pass
        
        items_file = cleaned_dir / "scrapy_items.jsonl"
        if items_file.exists() and metrics["spider_items_scraped"] == 0:
            try:
                lines = [l for l in items_file.read_text(encoding="utf-8").splitlines() if l.strip()]
                metrics["spider_items_scraped"] = len(lines)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
