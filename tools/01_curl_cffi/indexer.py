"""
tools/01_curl_cffi/indexer.py
=============================
Dedicated Indexer for 01_curl_cffi.
Extracts TLS impersonation profile, GraphQL problem slug, catalog problem count, and HTTP status.
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
    def __init__(self, tool_id: str = "01_curl_cffi"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "tls_impersonation_profile": "chrome124",
            "graphql_problem_slug": None,
            "catalog_problems_count": 0,
            "http_status": 200,
        }
        headers_file = raw_dir / "response_headers.json"
        if headers_file.exists():
            try:
                hd = json.loads(headers_file.read_text(encoding="utf-8"))
                metrics["http_status"] = hd.get("status_code", hd.get("status", 200))
            except Exception:
                pass

        cat_file = cleaned_dir / "catalog_index.json"
        if cat_file.exists():
            try:
                items = json.loads(cat_file.read_text(encoding="utf-8"))
                if isinstance(items, list):
                    metrics["catalog_problems_count"] = len(items)
                    if items and isinstance(items[0], dict):
                        metrics["graphql_problem_slug"] = items[0].get("slug")
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
