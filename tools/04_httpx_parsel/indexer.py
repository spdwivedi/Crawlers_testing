"""
tools/04_httpx_parsel/indexer.py
================================
Dedicated Indexer for 04_httpx_parsel.
Extracts http2 enabled, concurrent requests count, jmespath fields extracted, and xpath nodes extracted.
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
    def __init__(self, tool_id: str = "04_httpx_parsel"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "http2_enabled": True,
            "concurrent_requests_count": 1,
            "jmespath_fields_extracted": 0,
            "xpath_nodes_extracted": 0,
        }
        extracted_file = cleaned_dir / "async_extracted.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                meta = data.get("fetch_metadata", {})
                metrics["http2_enabled"] = meta.get("http2", True)
                metrics["concurrent_requests_count"] = meta.get("concurrent_requests", 1)
                
                jmes = data.get("json_jmespath_extracted", {})
                metrics["jmespath_fields_extracted"] = len(jmes) if isinstance(jmes, dict) else len(jmes) if isinstance(jmes, list) else 0

                html_nodes = data.get("html_parsel_extracted", {})
                metrics["xpath_nodes_extracted"] = len(html_nodes) if isinstance(html_nodes, dict) else len(html_nodes) if isinstance(html_nodes, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
