"""
tools/02_selectolax_lxml/indexer.py
===================================
Dedicated Indexer for 02_selectolax_lxml.
Extracts items parsed, selectolax parse us, lxml parse us, and speedup factor.
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
    def __init__(self, tool_id: str = "02_selectolax_lxml"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "items_parsed": 0,
            "selectolax_parse_us": None,
            "lxml_parse_us": None,
            "speedup_factor": None,
        }
        cat_file = cleaned_dir / "parsed_catalog.json"
        if cat_file.exists():
            try:
                data = json.loads(cat_file.read_text(encoding="utf-8"))
                items = data.get("items", [])
                metrics["items_parsed"] = len(items)
                bench = data.get("benchmark", {})
                metrics["selectolax_parse_us"] = bench.get("selectolax_us")
                metrics["lxml_parse_us"] = bench.get("lxml_us")
                metrics["speedup_factor"] = bench.get("speedup_factor")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
