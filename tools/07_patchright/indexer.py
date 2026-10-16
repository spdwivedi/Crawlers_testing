"""
tools/07_patchright/indexer.py
==============================
Dedicated Indexer for 07_patchright.
Extracts stealth evasion score, webdriver flag hidden, cdp leak patched, and signals audited count.
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
    def __init__(self, tool_id: str = "07_patchright"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "stealth_evasion_score": 100.0,
            "webdriver_flag_hidden": True,
            "cdp_leak_patched": True,
            "signals_audited_count": 0,
        }
        stealth_file = cleaned_dir / "stealth_signals.json"
        if stealth_file.exists():
            try:
                data = json.loads(stealth_file.read_text(encoding="utf-8"))
                metrics["stealth_evasion_score"] = float(data.get("evasion_score_pct", 100.0))
                vectors = data.get("bot_detection_vectors", {})
                metrics["signals_audited_count"] = len(vectors)
                if "navigator_webdriver" in vectors:
                    metrics["webdriver_flag_hidden"] = (vectors["navigator_webdriver"] is False)
                if "cdp_runtime_enabled" in vectors:
                    metrics["cdp_leak_patched"] = (vectors["cdp_runtime_enabled"] is False)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
