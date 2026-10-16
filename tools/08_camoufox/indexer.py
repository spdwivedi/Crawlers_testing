"""
tools/08_camoufox/indexer.py
============================
Dedicated Indexer for 08_camoufox.
Extracts engine used, spoofed oscpu, canvas hash, and webgl renderer.
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
    def __init__(self, tool_id: str = "08_camoufox"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "engine_used": "Camoufox Firefox",
            "spoofed_oscpu": "Windows NT 10.0; Win64; x64",
            "canvas_hash": None,
            "webgl_renderer": None,
        }
        extracted_file = cleaned_dir / "extracted_data.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                metrics["engine_used"] = data.get("engine_used", "Camoufox Firefox")
                fp = data.get("spoofed_fingerprint", {})
                metrics["spoofed_oscpu"] = fp.get("oscpu", metrics["spoofed_oscpu"])
                metrics["canvas_hash"] = fp.get("canvas_hash")
                metrics["webgl_renderer"] = fp.get("webgl_renderer")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
