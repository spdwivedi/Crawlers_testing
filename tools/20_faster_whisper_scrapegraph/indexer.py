"""
tools/20_faster_whisper_scrapegraph/indexer.py
==============================================
Dedicated Indexer for 20_faster_whisper_scrapegraph.
Extracts audio duration sec, srt segments count, knowledge graph nodes, and knowledge graph edges.
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
    def __init__(self, tool_id: str = "20_faster_whisper_scrapegraph"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "audio_duration_sec": 0.0,
            "srt_segments_count": 0,
            "knowledge_graph_nodes": 0,
            "knowledge_graph_edges": 0,
        }
        seg_file = cleaned_dir / "transcript_segments.json"
        if seg_file.exists():
            try:
                data = json.loads(seg_file.read_text(encoding="utf-8"))
                metrics["audio_duration_sec"] = float(data.get("duration_seconds", 0.0))
                metrics["srt_segments_count"] = data.get("segments_count", 0)
            except Exception:
                pass

        kg_file = cleaned_dir / "knowledge_graph.json"
        if kg_file.exists():
            try:
                data = json.loads(kg_file.read_text(encoding="utf-8"))
                metrics["knowledge_graph_nodes"] = data.get("nodes_count", 0)
                metrics["knowledge_graph_edges"] = data.get("edges_count", 0)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
