"""
tools/15_mitmproxy_interceptor/indexer.py
=========================================
Dedicated Indexer for 15_mitmproxy_interceptor.
Extracts intercepted flows count, discovered api endpoints count, and proxy port used.
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
    def __init__(self, tool_id: str = "15_mitmproxy_interceptor"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "intercepted_flows_count": 0,
            "discovered_api_endpoints_count": 0,
            "proxy_port_used": 8080,
        }
        apis_file = cleaned_dir / "discovered_apis.json"
        if apis_file.exists():
            try:
                data = json.loads(apis_file.read_text(encoding="utf-8"))
                metrics["intercepted_flows_count"] = data.get("total_flows_intercepted", 0)
                metrics["discovered_api_endpoints_count"] = data.get("discovered_apis_count", 0)
                metrics["proxy_port_used"] = data.get("proxy_port_used", 8080)
            except Exception:
                pass

        flows_file = raw_dir / "intercepted_flows.jsonl"
        if flows_file.exists() and metrics["intercepted_flows_count"] == 0:
            try:
                lines = [l for l in flows_file.read_text(encoding="utf-8").splitlines() if l.strip()]
                metrics["intercepted_flows_count"] = len(lines)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
