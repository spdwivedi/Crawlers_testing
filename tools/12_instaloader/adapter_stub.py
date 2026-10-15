"""
tools/12_instaloader/adapter_stub.py
====================================
Delegates to real adapter implementation in adapter.py.
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

_mod = importlib.import_module("tools.12_instaloader.adapter")
run_action = _mod.run_action
TOOL_ID = _mod.TOOL_ID


class AdapterStub:
    def __init__(self):
        self.tool_id = TOOL_ID

    def run(self, action_name: str = "scrape_for_insta", target_url: str = "", **kwargs) -> dict:
        return run_action(
            action_name=action_name or "scrape_for_insta",
            target_url=target_url or "https://www.instagram.com/reel/C8XYZ12345/",
            **kwargs,
        )


if __name__ == "__main__":
    import json
    adapter = AdapterStub()
    res = adapter.run()
    print(json.dumps(res, indent=2, default=str))
