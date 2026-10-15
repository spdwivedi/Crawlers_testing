"""
tools/01_curl_cffi/adapter_stub.py
==================================
Delegates to real adapter implementation in adapter.py.
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

_mod = importlib.import_module("tools.01_curl_cffi.adapter")
run_scrape_for_leetcode = _mod.run_scrape_for_leetcode
TOOL_ID = _mod.TOOL_ID


class AdapterStub:
    def __init__(self):
        self.tool_id = TOOL_ID

    def run(self, action_name: str = "scrape_for_leetcode", target_url: str = "", **kwargs) -> dict:
        return run_scrape_for_leetcode(target_url=target_url or "https://leetcode.com/problems/two-sum/")


if __name__ == "__main__":
    import json
    adapter = AdapterStub()
    res = adapter.run()
    print(json.dumps(res, indent=2, default=str))
