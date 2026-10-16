"""
tools/05_trafilatura/indexer.py
===============================
Dedicated Indexer for 05_trafilatura.
Extracts raw html bytes, clean md bytes, boilerplate reduction pct, and extracted title.
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
    def __init__(self, tool_id: str = "05_trafilatura"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "raw_html_bytes": 0,
            "clean_md_bytes": 0,
            "boilerplate_reduction_pct": 0.0,
            "extracted_title": "",
        }
        raw_html = raw_dir / "raw_page.html"
        if raw_html.exists():
            metrics["raw_html_bytes"] = raw_html.stat().st_size

        clean_md = cleaned_dir / "extracted_content.md"
        if clean_md.exists():
            metrics["clean_md_bytes"] = clean_md.stat().st_size

        if metrics["raw_html_bytes"] > 0:
            reduction = (1.0 - (metrics["clean_md_bytes"] / metrics["raw_html_bytes"])) * 100.0
            metrics["boilerplate_reduction_pct"] = round(max(0.0, reduction), 2)

        meta_file = cleaned_dir / "metadata.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                metrics["extracted_title"] = data.get("title", "")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
