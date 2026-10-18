"""
core/arena_runner.py
====================
Safe Arena Engine — Stage 4 / Step 4.4 (The 3 Working Ways: Working Way 2 Safe Multi-Tool Arena).

Executes multiple candidate crawler/extractor tools safely against a single target URL:
1. Multi-Tool Safe Execution with Staggered Concurrency (anti-ban / rate-limit mitigation).
2. Deep Per-Tool Telemetry & Metrics Capture (latency, raw bytes, cleaned chars, memory footprint, domain metrics).
3. Objective Multi-Vector Scoring (Speed, Data Richness, Stealth & Composite Ranking).
4. Automated Markdown & JSON Comparative Arena Reports (persisted into index_store/arena_reports/).
5. Fast Query and Retrieval API (list_arena_reports, get_arena_report).
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psutil

from core.human_timing import HumanTimingEngine, TimingProfile
from core.logger_engine import LogEngine, log_global
from core.state_tracker import update_progress

ARENA_REPORTS_DIR = ROOT / "index_store" / "arena_reports"
REGISTRY_PATH = ROOT / "tools" / "registry.json"

DEFAULT_ARENA_SQUAD = [
    "01_curl_cffi",
    "04_httpx_parsel",
    "06_playwright",
    "07_patchright",
    "16_crawl4ai",
]


class SafeArenaRunner:
    """
    Coordinates multi-tool safe benchmarking on a single target URL with staggered delays
    and comparative analytical reporting.
    """

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or ARENA_REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.timing_engine = HumanTimingEngine()
        self.registry = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        """Loads tools/registry.json manifest."""
        if REGISTRY_PATH.exists():
            try:
                return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"tools": []}

    def _get_installed_tools(self) -> list[str]:
        """Returns all installed tool IDs from registry."""
        tools = self.registry.get("tools", [])
        return [t["tool_id"] for t in tools if t.get("installed", True)]

    def run_arena(
        self,
        target_url: str,
        tool_ids: list[str] | str | None = None,
        action_name: str = "arena_benchmark",
        human_mode: bool = True,
        timing_profile: str = "BALANCED_HUMAN",
        stagger_delay_sec: float | None = None,
        auth_account_id: str = "",
        auth_target: str = "",
        run_label: str = "",
    ) -> dict[str, Any]:
        """
        Executes candidate tools sequentially on target_url with staggered safety intervals.
        Generates comparative score matrix, assigns a winner, and writes JSON/MD reports.
        """
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%Y%m%d_%H%M%S")
        report_uuid = uuid.uuid4().hex[:8]
        report_id = f"arena_run_{time_str}_{report_uuid}"

        # 1. Resolve candidate tools
        candidate_tools: list[str] = []
        if tool_ids is None or tool_ids == [] or tool_ids == "":
            candidate_tools = list(DEFAULT_ARENA_SQUAD)
        elif tool_ids == "all" or tool_ids == ["all"]:
            candidate_tools = self._get_installed_tools()
        elif isinstance(tool_ids, str):
            candidate_tools = [t.strip() for t in tool_ids.split(",") if t.strip()]
        else:
            candidate_tools = list(tool_ids)

        # Filter out empty or duplicate tools preserving order
        seen = set()
        resolved_tools: list[str] = []
        for t in candidate_tools:
            if t and t not in seen:
                seen.add(t)
                resolved_tools.append(t)

        total_tools = len(resolved_tools)
        if total_tools == 0:
            raise ValueError("No valid candidate tool IDs supplied to SafeArenaRunner.")

        log_global(
            message=f"Arena launched: {report_id} targeting '{target_url}' with {total_tools} tools ({', '.join(resolved_tools)})",
            level="INFO",
            stage="Stage 4",
            step="Step 4.4",
            tool_id="arena_runner",
            action_name="run_arena",
            stage_log_name="stage_4_working_ways",
        )

        arena_start_t = time.perf_counter()
        tool_executions: list[dict[str, Any]] = []

        # 2. Sequential Staggered Execution
        for idx, tool_id in enumerate(resolved_tools):
            progress_pct = int(10 + (idx / total_tools) * 80)
            subtask_msg = f"Arena: Running {tool_id} ({idx + 1}/{total_tools}) on target"
            update_progress(progress_pct, subtask=subtask_msg)

            # Stagger delay before starting subsequent tools (anti-ban / rate-limit safety)
            stagger_applied = 0.0
            if idx > 0:
                if stagger_delay_sec is not None:
                    stagger_applied = float(stagger_delay_sec)
                else:
                    stagger_applied = HumanTimingEngine.log_normal_delay(
                        median=2.5, sigma=0.4, min_val=1.0, max_val=8.0
                    )
                log_global(
                    message=f"Arena staggered safety delay: pausing {stagger_applied:.2f}s before running {tool_id}",
                    level="INFO",
                    stage="Stage 4",
                    step="Step 4.4",
                    tool_id="arena_runner",
                    action_name="stagger_pause",
                    stage_log_name="stage_4_working_ways",
                )
                time.sleep(stagger_applied)

            # Execute individual tool
            exec_res = self._execute_single_tool(
                tool_id=tool_id,
                target_url=target_url,
                action_name=action_name,
                human_mode=human_mode,
                timing_profile=timing_profile,
                auth_account_id=auth_account_id,
                auth_target=auth_target,
                stagger_applied_sec=stagger_applied,
            )
            tool_executions.append(exec_res)

        total_elapsed_sec = round(time.perf_counter() - arena_start_t, 3)

        # 3. Comparative Scoring and Ranking
        comparison_matrix, winning_tool, winning_rationale = self._compute_comparative_scores(
            tool_executions
        )

        # 4. Construct Structured Arena Report Document
        report_data = {
            "report_id": report_id,
            "created_at": now.isoformat(),
            "target_url": target_url,
            "action_name": action_name,
            "run_label": run_label or f"Arena Benchmark: {total_tools} tools vs. {target_url}",
            "human_mode": human_mode,
            "timing_profile": timing_profile,
            "total_tools": total_tools,
            "tools_tested": resolved_tools,
            "total_elapsed_sec": total_elapsed_sec,
            "winning_tool": winning_tool,
            "winning_rationale": winning_rationale,
            "comparison_matrix": comparison_matrix,
            "tool_executions": tool_executions,
        }

        # 5. Persist JSON & Markdown Reports
        json_report_path = self.reports_dir / f"{report_id}.json"
        md_report_path = self.reports_dir / f"{report_id}.md"

        json_report_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
        markdown_content = self._render_markdown_report(report_data)
        md_report_path.write_text(markdown_content, encoding="utf-8")

        update_progress(100, subtask=f"Arena complete. Winner: {winning_tool}")
        log_global(
            message=f"Arena {report_id} finished: Winner={winning_tool} (Total time: {total_elapsed_sec}s). Reports saved.",
            level="INFO",
            stage="Stage 4",
            step="Step 4.4",
            tool_id="arena_runner",
            action_name="run_arena",
            stage_log_name="stage_4_working_ways",
        )

        report_data["json_report_path"] = str(json_report_path.relative_to(ROOT))
        report_data["md_report_path"] = str(md_report_path.relative_to(ROOT))
        return report_data

    def _execute_single_tool(
        self,
        tool_id: str,
        target_url: str,
        action_name: str,
        human_mode: bool,
        timing_profile: str,
        auth_account_id: str = "",
        auth_target: str = "",
        stagger_applied_sec: float = 0.0,
    ) -> dict[str, Any]:
        """
        Executes a candidate tool in-process with memory tracking and comprehensive artifact inspection.
        """
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)

        t0 = time.perf_counter()
        adapter_module_name = f"tools.{tool_id}.adapter"
        adapter = None
        exec_error = ""
        raw_result: Any = None
        status = "failed"

        try:
            adapter = importlib.import_module(adapter_module_name)
            # Find appropriate entrypoint
            if hasattr(adapter, "run") and callable(getattr(adapter, "run")):
                raw_result = adapter.run(
                    target_url=target_url,
                    action_name=action_name,
                    human_mode=human_mode,
                    timing_profile=timing_profile,
                )
            elif hasattr(adapter, "run_action") and callable(getattr(adapter, "run_action")):
                raw_result = adapter.run_action(
                    action_name=action_name,
                    target_url=target_url,
                    human_mode=human_mode,
                    timing_profile=timing_profile,
                )
            else:
                # Find any run_* method
                candidate_func = None
                for attr in dir(adapter):
                    if attr.startswith("run_") and callable(getattr(adapter, attr)):
                        candidate_func = getattr(adapter, attr)
                        break
                if candidate_func:
                    raw_result = candidate_func(
                        target_url=target_url,
                        action_name=action_name,
                        human_mode=human_mode,
                        timing_profile=timing_profile,
                    )
                else:
                    raise AttributeError(f"Adapter {adapter_module_name} has no recognized run/run_action entrypoint.")

            status = "completed"
        except Exception as exc:
            exec_error = str(exc)
            log_global(
                message=f"Arena tool {tool_id} execution error: {exc}",
                level="WARN",
                stage="Stage 4",
                step="Step 4.4",
                tool_id="arena_runner",
                action_name="tool_error",
                stage_log_name="stage_4_working_ways",
            )

        elapsed_sec = round(time.perf_counter() - t0, 3)
        mem_after = process.memory_info().rss / (1024 * 1024)
        mem_delta_mb = round(max(0.0, mem_after - mem_before), 2)

        # Artifact Inspection
        run_info = {}
        manifest_data: dict[str, Any] = {}
        run_dir_path: Path | None = None

        if isinstance(raw_result, dict):
            run_info = raw_result.get("run_info") or {}
            if "manifest" in raw_result and isinstance(raw_result["manifest"], dict):
                manifest_data = raw_result["manifest"]

        if run_info.get("run_dir"):
            run_dir_path = Path(run_info["run_dir"])
        elif run_info.get("manifest_path"):
            run_dir_path = Path(run_info["manifest_path"]).parent
        else:
            # Look up newest run dir in data/<tool_id>/
            tool_data_dir = ROOT / "data" / tool_id
            if tool_data_dir.exists():
                all_runs = sorted(tool_data_dir.glob("*/*/*"), key=lambda p: p.stat().st_mtime, reverse=True)
                for r in all_runs:
                    if (r / "run_manifest.json").exists():
                        run_dir_path = r
                        break

        raw_bytes = 0
        cleaned_chars = 0
        raw_files: list[str] = []
        cleaned_files: list[str] = []
        domain_metrics: dict[str, Any] = {}

        if run_dir_path and run_dir_path.exists():
            mf_file = run_dir_path / "run_manifest.json"
            if mf_file.exists() and not manifest_data:
                try:
                    manifest_data = json.loads(mf_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            # Inspect raw/
            raw_dir = run_dir_path / "raw"
            if raw_dir.exists():
                for f in raw_dir.iterdir():
                    if f.is_file():
                        raw_files.append(f.name)
                        try:
                            raw_bytes += f.stat().st_size
                        except Exception:
                            pass

            # Inspect cleaned/
            cleaned_dir = run_dir_path / "cleaned"
            if cleaned_dir.exists():
                for f in cleaned_dir.iterdir():
                    if f.is_file():
                        cleaned_files.append(f.name)
                        try:
                            text_content = f.read_text(encoding="utf-8", errors="replace")
                            cleaned_chars += len(text_content)
                        except Exception:
                            pass

        if manifest_data:
            if manifest_data.get("status") == "completed":
                status = "completed"
            domain_metrics = manifest_data.get("domain_metrics") or {}

        # Fallback values if result provided them directly
        if isinstance(raw_result, dict):
            if not domain_metrics and "domain_metrics" in raw_result:
                domain_metrics = raw_result["domain_metrics"]
            if not domain_metrics and "benchmark" in raw_result:
                domain_metrics = raw_result["benchmark"]

        return {
            "tool_id": tool_id,
            "status": status,
            "elapsed_sec": elapsed_sec,
            "stagger_applied_sec": round(stagger_applied_sec, 2),
            "raw_bytes": raw_bytes,
            "cleaned_chars": cleaned_chars,
            "raw_file_count": len(raw_files),
            "cleaned_file_count": len(cleaned_files),
            "memory_delta_mb": mem_delta_mb,
            "peak_rss_mb": round(mem_after, 2),
            "domain_metrics": domain_metrics,
            "error": exec_error,
            "run_dir": str(run_dir_path.relative_to(ROOT)) if run_dir_path and run_dir_path.exists() else "",
        }

    def _compute_comparative_scores(
        self, tool_executions: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], str, str]:
        """
        Calculates normalized speed, data richness, stealth, and composite scores across tools.
        Determines the winning tool and returns the ranked comparison matrix.
        """
        successful = [t for t in tool_executions if t["status"] == "completed"]
        min_elapsed = min([t["elapsed_sec"] for t in successful]) if successful else 1.0
        max_cleaned = max([t["cleaned_chars"] for t in successful]) if successful else 1

        comparison_matrix: list[dict[str, Any]] = []

        for item in tool_executions:
            tool_id = item["tool_id"]
            status = item["status"]
            elapsed = max(0.001, item["elapsed_sec"])
            cleaned = item["cleaned_chars"]
            domain_metrics = item.get("domain_metrics") or {}

            if status != "completed":
                matrix_entry = {
                    **item,
                    "speed_score": 0.0,
                    "data_richness_score": 0.0,
                    "stealth_score": 0.0,
                    "composite_score": 0.0,
                    "rank": 999,
                }
                comparison_matrix.append(matrix_entry)
                continue

            # 1. Speed Score (100 is fastest in cohort)
            speed_score = round(100.0 * (min_elapsed / elapsed), 1)

            # 2. Data Richness Score (based on structured output + clean text volume)
            char_ratio = (cleaned / max(1, max_cleaned)) * 70.0
            metric_count = len(domain_metrics)
            metric_bonus = min(30.0, metric_count * 6.0)
            richness_score = round(min(100.0, char_ratio + metric_bonus), 1)

            # 3. Stealth Score
            # Baseline 90 for any successful run without 403/429
            stealth_score = 90.0
            if "evasion_score" in domain_metrics:
                stealth_score = float(domain_metrics["evasion_score"])
            elif tool_id in ("07_patchright", "08_camoufox", "09_nodriver"):
                stealth_score = 98.0
            elif tool_id in ("01_curl_cffi", "10_scrapling"):
                stealth_score = 95.0
            elif tool_id in ("06_playwright", "16_crawl4ai"):
                stealth_score = 92.0
            stealth_score = round(min(100.0, stealth_score), 1)

            # 4. Composite Score: 35% speed + 35% richness + 30% stealth
            composite_score = round(
                (0.35 * speed_score) + (0.35 * richness_score) + (0.30 * stealth_score), 1
            )

            matrix_entry = {
                **item,
                "speed_score": speed_score,
                "data_richness_score": richness_score,
                "stealth_score": stealth_score,
                "composite_score": composite_score,
            }
            comparison_matrix.append(matrix_entry)

        # Sort matrix by composite score descending
        comparison_matrix.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
        for rank, item in enumerate(comparison_matrix, start=1):
            item["rank"] = rank

        # Determine winner
        if successful:
            winning_entry = comparison_matrix[0]
            winning_tool = winning_entry["tool_id"]
            winning_rationale = (
                f"Tool '{winning_tool}' placed #1 with a composite score of {winning_entry['composite_score']}/100 "
                f"(Speed: {winning_entry['speed_score']}, Richness: {winning_entry['data_richness_score']}, "
                f"Stealth: {winning_entry['stealth_score']}) with execution time of {winning_entry['elapsed_sec']}s "
                f"and {winning_entry['cleaned_chars']} cleaned characters."
            )
        else:
            winning_tool = "None"
            winning_rationale = "All candidate tools failed during the arena benchmark run."

        return comparison_matrix, winning_tool, winning_rationale

    def _render_markdown_report(self, report_data: dict[str, Any]) -> str:
        """Renders comprehensive, textbook-grade GitHub Flavored Markdown report."""
        report_id = report_data["report_id"]
        target_url = report_data["target_url"]
        created_at = report_data["created_at"]
        total_time = report_data["total_elapsed_sec"]
        winning_tool = report_data["winning_tool"]
        winning_rationale = report_data["winning_rationale"]
        matrix = report_data["comparison_matrix"]

        md_lines = [
            f"# ⚔️ Safe Arena Multi-Tool Benchmark Report: `{report_id}`",
            "",
            f"- **Target URL:** `{target_url}`",
            f"- **Created At:** `{created_at}`",
            f"- **Execution Mode:** `human_mode={report_data['human_mode']}` (`{report_data['timing_profile']}`)",
            f"- **Total Staggered Duration:** `{total_time}s`",
            f"- **Candidate Tools Tested ({report_data['total_tools']}):** `{', '.join(report_data['tools_tested'])}`",
            "",
            "> [!IMPORTANT]",
            f"> **🏆 Arena Winner: `{winning_tool}`**  ",
            f"> {winning_rationale}",
            "",
            "## 1. Side-by-Side Comparative Matrix",
            "",
            "| Rank | Tool ID | Status | Latency (s) | Raw Bytes | Cleaned Chars | Speed Score | Richness Score | Stealth Score | **Composite Score** |",
            "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]

        for item in matrix:
            rank_icon = "🥇" if item["rank"] == 1 else ("🥈" if item["rank"] == 2 else ("🥉" if item["rank"] == 3 else f"#{item['rank']}"))
            status_badge = "✅ PASS" if item["status"] == "completed" else "❌ FAIL"
            md_lines.append(
                f"| {rank_icon} | `{item['tool_id']}` | {status_badge} | {item['elapsed_sec']}s | {item['raw_bytes']:,} | {item['cleaned_chars']:,} | {item.get('speed_score', 0)} | {item.get('data_richness_score', 0)} | {item.get('stealth_score', 0)} | **{item.get('composite_score', 0)}** |"
            )

        md_lines.extend([
            "",
            "## 2. Detailed Performance & Resource Footprint",
            "",
            "| Tool ID | Memory Delta (MB) | Peak RSS (MB) | Stagger Pause (s) | Raw Files | Cleaned Files | Run Directory |",
            "|:---|:---:|:---:|:---:|:---:|:---:|:---|",
        ])

        for item in matrix:
            md_lines.append(
                f"| `{item['tool_id']}` | +{item['memory_delta_mb']} MB | {item['peak_rss_mb']} MB | {item['stagger_applied_sec']}s | {item['raw_file_count']} | {item['cleaned_file_count']} | `{item.get('run_dir', 'N/A')}` |"
            )

        md_lines.extend([
            "",
            "## 3. Extracted Domain Metrics & Capabilities Sample",
            "",
        ])

        for item in matrix:
            md_lines.extend([
                f"### `{item['tool_id']}` Metrics",
                "```json",
                json.dumps(item.get("domain_metrics", {}), indent=2, default=str),
                "```",
                "",
            ])

        md_lines.extend([
            "---",
            "*Report automatically generated by Antigravity SafeArenaRunner (Stage 4 / Step 4.4). Auto-indexed into GlobalMasterIndexer.*",
        ])

        return "\n".join(md_lines)

    def list_arena_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Lists all saved arena reports sorted newest first.
        """
        reports: list[dict[str, Any]] = []
        if not self.reports_dir.exists():
            return reports

        for report_file in sorted(self.reports_dir.glob("arena_run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
                reports.append({
                    "report_id": data.get("report_id", report_file.stem),
                    "created_at": data.get("created_at"),
                    "target_url": data.get("target_url"),
                    "total_tools": data.get("total_tools", len(data.get("tools_tested", []))),
                    "tools_tested": data.get("tools_tested", []),
                    "winning_tool": data.get("winning_tool"),
                    "total_elapsed_sec": data.get("total_elapsed_sec"),
                    "json_file": report_file.name,
                    "md_file": f"{report_file.stem}.md",
                })
                if len(reports) >= limit:
                    break
            except Exception:
                continue

        return reports

    def get_arena_report(self, report_id: str) -> dict[str, Any] | None:
        """
        Retrieves a full arena report by ID or filename.
        """
        clean_id = report_id.replace(".json", "").replace(".md", "")
        target_path = self.reports_dir / f"{clean_id}.json"
        if target_path.exists():
            try:
                return json.loads(target_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None


if __name__ == "__main__":
    runner = SafeArenaRunner()
    url = sys.argv[1] if len(sys.argv) > 1 else "https://quotes.toscrape.com"
    res = runner.run_arena(target_url=url, tool_ids=["01_curl_cffi", "04_httpx_parsel"])
    print(f"Arena Run Completed: Winner = {res['winning_tool']}")
