"""
tools/11_yt_dlp_ffmpeg/indexer.py
=================================
Dedicated Indexer for 11_yt_dlp_ffmpeg.
Extracts raw hls chunks count, combined video bytes, extracted audio wav bytes, video codec, and duration sec.
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
    def __init__(self, tool_id: str = "11_yt_dlp_ffmpeg"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "raw_hls_chunks_count": 0,
            "combined_video_bytes": 0,
            "extracted_audio_wav_bytes": 0,
            "video_codec": "h264",
            "duration_sec": 3.0,
        }
        if raw_dir.exists():
            chunks = list(raw_dir.glob("*.ts"))
            metrics["raw_hls_chunks_count"] = len(chunks)

        analysis_file = cleaned_dir / "media_analysis.json"
        if analysis_file.exists():
            try:
                data = json.loads(analysis_file.read_text(encoding="utf-8"))
                meta = data.get("metadata", {})
                metrics["duration_sec"] = float(meta.get("duration_seconds", 3.0))
                stream_pipe = data.get("stream_pipeline", {})
                if "raw_hls_chunks_count" in stream_pipe:
                    metrics["raw_hls_chunks_count"] = stream_pipe.get("raw_hls_chunks_count")
                vid = data.get("combined_video", {})
                metrics["combined_video_bytes"] = vid.get("size_bytes", 0)
                metrics["video_codec"] = vid.get("codec", "h264")
                wav = data.get("extracted_audio_wav", {})
                metrics["extracted_audio_wav_bytes"] = wav.get("size_bytes", 0)
            except Exception:
                pass
        
        vid_file = cleaned_dir / "combined_video.mp4"
        if vid_file.exists() and metrics["combined_video_bytes"] == 0:
            metrics["combined_video_bytes"] = vid_file.stat().st_size
        wav_file = cleaned_dir / "extracted_audio.wav"
        if wav_file.exists() and metrics["extracted_audio_wav_bytes"] == 0:
            metrics["extracted_audio_wav_bytes"] = wav_file.stat().st_size

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
