"""
tools/13_gallery_dl/indexer.py
==============================
Dedicated Indexer for 13_gallery_dl.
Extracts extractor used, platform, gallery items count, and media files downloaded.
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
    def __init__(self, tool_id: str = "13_gallery_dl"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "extractor_used": "gallery-dl",
            "platform": "generic",
            "gallery_items_count": 0,
            "media_files_downloaded": 0,
        }
        cat_file = cleaned_dir / "gallery_catalog.json"
        if cat_file.exists():
            try:
                data = json.loads(cat_file.read_text(encoding="utf-8"))
                metrics["extractor_used"] = data.get("resolved_extractor", "gallery-dl")
                items = data.get("items", [])
                metrics["gallery_items_count"] = len(items) if isinstance(items, list) else data.get("item_count", 0)
                if items and isinstance(items[0], dict):
                    metrics["platform"] = items[0].get("platform", "gallery")
                saved = data.get("raw_media_saved", [])
                metrics["media_files_downloaded"] = len(saved) if isinstance(saved, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
