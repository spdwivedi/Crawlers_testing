"""
Adapter Stub — 20_faster_whisper_scrapegraph
Mechanism: AI/Audio-Graph | Batch: 4
Status: SCAFFOLDED (not yet installed)

Replace this stub with the actual adapter implementation when installing.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Add project root to sys.path for core imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.folder_manager import create_action_run
from core.logger_engine import ToolLogger

TOOL_ID = "20_faster_whisper_scrapegraph"


class AdapterStub:
    """
    Stub adapter for faster_whisper_scrapegraph.
    Replace with real implementation after: pip install faster-whisper-scrapegraph
    """

    def __init__(self):
        self.tool_id = TOOL_ID
        self.logger = ToolLogger(TOOL_ID)

    def run(self, action_name: str, target_url: str = "", **kwargs) -> dict:
        """Entry point for all actions. Returns run_info dict."""
        run_info = create_action_run(
            tool_id=self.tool_id,
            action_name=action_name,
            target_url=target_url,
        )
        self.logger.info(
            message=f"[STUB] faster_whisper_scrapegraph adapter called — not yet installed.",
            action_name=action_name,
            run_id=run_info["run_id"],
        )
        return {
            "status": "stub_not_installed",
            "tool_id": self.tool_id,
            "action_name": action_name,
            "run_info": run_info,
        }


if __name__ == "__main__":
    adapter = AdapterStub()
    result = adapter.run(action_name="scrape_for_leetcode", target_url="https://example.com")
    print(json.dumps(result, indent=2, default=str))
