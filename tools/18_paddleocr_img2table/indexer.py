"""
tools/18_paddleocr_img2table/indexer.py
=======================================
Dedicated Indexer for 18_paddleocr_img2table.
Extracts tables detected count, table rows, table cols, and cells extracted count.
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
    def __init__(self, tool_id: str = "18_paddleocr_img2table"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "tables_detected_count": 0,
            "table_rows": 0,
            "table_cols": 0,
            "cells_extracted_count": 0,
        }
        table_file = cleaned_dir / "extracted_table.json"
        if table_file.exists():
            try:
                data = json.loads(table_file.read_text(encoding="utf-8"))
                rows = data.get("row_count", 0)
                cols = data.get("column_count", 0)
                metrics["tables_detected_count"] = 1 if rows > 0 else 0
                metrics["table_rows"] = rows
                metrics["table_cols"] = cols
                metrics["cells_extracted_count"] = rows * cols
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
