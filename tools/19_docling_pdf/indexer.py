"""
tools/19_docling_pdf/indexer.py
===============================
Dedicated Indexer for 19_docling_pdf.
Extracts pdf pages count, hierarchy nodes count, and pdf tables parsed.
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
    def __init__(self, tool_id: str = "19_docling_pdf"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "pdf_pages_count": 1,
            "hierarchy_nodes_count": 0,
            "pdf_tables_parsed": 0,
        }
        doc_file = cleaned_dir / "document_hierarchy.json"
        if doc_file.exists():
            try:
                data = json.loads(doc_file.read_text(encoding="utf-8"))
                metrics["pdf_pages_count"] = data.get("page_count", 1)
                metrics["hierarchy_nodes_count"] = data.get("total_nodes", 0)
                metrics["pdf_tables_parsed"] = data.get("tables_count", 0)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
