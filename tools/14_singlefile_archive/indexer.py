"""
tools/14_singlefile_archive/indexer.py
======================================
Dedicated Indexer for 14_singlefile_archive.
Extracts singlefile size kb, inlined css count, inlined images base64 count, and scripts stripped count.
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
    def __init__(self, tool_id: str = "14_singlefile_archive"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "singlefile_size_kb": 0.0,
            "inlined_css_count": 0,
            "inlined_images_base64_count": 0,
            "scripts_stripped_count": 0,
        }
        manifest_file = cleaned_dir / "inlined_assets_manifest.json"
        if manifest_file.exists():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                size_bytes = data.get("final_html_size_bytes", 0)
                metrics["singlefile_size_kb"] = round(size_bytes / 1024.0, 2)
                metrics["inlined_css_count"] = data.get("stylesheets_count", 0)
                metrics["inlined_images_base64_count"] = data.get("images_count", 0)
                metrics["scripts_stripped_count"] = data.get("scripts_sanitized_count", 0)
            except Exception:
                pass

        snapshot = raw_dir / "snapshot.singlefile.html"
        if snapshot.exists() and metrics["singlefile_size_kb"] == 0.0:
            metrics["singlefile_size_kb"] = round(snapshot.stat().st_size / 1024.0, 2)

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
