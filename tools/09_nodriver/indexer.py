"""
tools/09_nodriver/indexer.py
============================
Dedicated Indexer for 09_nodriver.
Extracts cdp direct mode, links extracted count, and dom size bytes.
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
    def __init__(self, tool_id: str = "09_nodriver"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "cdp_direct_mode": True,
            "links_extracted_count": 0,
            "dom_size_bytes": 0,
        }
        extracted_file = cleaned_dir / "cdp_extracted.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                links = data.get("extracted_links", [])
                metrics["links_extracted_count"] = len(links) if isinstance(links, list) else 0
            except Exception:
                pass

        dom_file = raw_dir / "cdp_dom.html"
        if dom_file.exists():
            metrics["dom_size_bytes"] = dom_file.stat().st_size
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
