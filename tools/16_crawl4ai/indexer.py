"""
tools/16_crawl4ai/indexer.py
============================
Dedicated Indexer for 16_crawl4ai.
Extracts semantic chunks count, markdown length chars, links discovered count, and media discovered count.
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
    def __init__(self, tool_id: str = "16_crawl4ai"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "semantic_chunks_count": 0,
            "markdown_length_chars": 0,
            "links_discovered_count": 0,
            "media_discovered_count": 0,
        }
        chunks_file = cleaned_dir / "semantic_chunks.json"
        if chunks_file.exists():
            try:
                data = json.loads(chunks_file.read_text(encoding="utf-8"))
                metrics["semantic_chunks_count"] = data.get("total_chunks", 0)
            except Exception:
                pass

        md_file = cleaned_dir / "llm_ready.md"
        if md_file.exists():
            metrics["markdown_length_chars"] = len(md_file.read_text(encoding="utf-8", errors="replace"))

        media_links = cleaned_dir / "media_and_links.json"
        if media_links.exists():
            try:
                data = json.loads(media_links.read_text(encoding="utf-8"))
                metrics["links_discovered_count"] = data.get("total_links", 0)
                metrics["media_discovered_count"] = data.get("total_media", 0)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
