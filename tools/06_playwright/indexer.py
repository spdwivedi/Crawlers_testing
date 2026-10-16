"""
tools/06_playwright/indexer.py
==============================
Dedicated Indexer for 06_playwright.
Extracts har total requests, unique origins discovered, screenshot bytes, and rendered dom bytes.
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
    def __init__(self, tool_id: str = "06_playwright"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "har_total_requests": 0,
            "unique_origins_discovered": 0,
            "screenshot_bytes": 0,
            "rendered_dom_bytes": 0,
        }
        origin_file = cleaned_dir / "origin_map.json"
        if origin_file.exists():
            try:
                data = json.loads(origin_file.read_text(encoding="utf-8"))
                metrics["har_total_requests"] = data.get("total_requests_recorded", 0)
                origins = data.get("unique_origins", [])
                metrics["unique_origins_discovered"] = len(origins) if isinstance(origins, list) else 0
            except Exception:
                pass

        screenshot = raw_dir / "page_visual.png"
        if screenshot.exists():
            metrics["screenshot_bytes"] = screenshot.stat().st_size

        dom_file = raw_dir / "rendered_dom.html"
        if dom_file.exists():
            metrics["rendered_dom_bytes"] = dom_file.stat().st_size

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
