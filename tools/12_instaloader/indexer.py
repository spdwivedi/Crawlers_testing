"""
tools/12_instaloader/indexer.py
===============================
Dedicated Indexer for 12_instaloader.
Extracts insta shortcode, auth mode, likes count, comments count, and hashtags count.
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
    def __init__(self, tool_id: str = "12_instaloader"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "insta_shortcode": "test_shortcode",
            "auth_mode": "anonymous_guest",
            "likes_count": 0,
            "comments_count": 0,
            "hashtags_count": 0,
        }
        post_file = cleaned_dir / "insta_post_structured.json"
        if post_file.exists():
            try:
                data = json.loads(post_file.read_text(encoding="utf-8"))
                metrics["insta_shortcode"] = data.get("shortcode", "test_shortcode")
                prov = data.get("provenance", {})
                metrics["auth_mode"] = prov.get("auth_mode", "anonymous_guest")
                eng = data.get("engagement", {})
                metrics["likes_count"] = eng.get("likes", 0)
                metrics["comments_count"] = eng.get("comments", 0)
                content = data.get("content", {})
                tags = content.get("hashtags", [])
                metrics["hashtags_count"] = len(tags) if isinstance(tags, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
