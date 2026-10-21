"""
core/benchmark_engine.py
========================
Master 20-Tool Performance & Quality Matrix Engine — Stage 6 / Step 6.1
(Master Benchmarking, Resilience Testing & Project Exporter — Rule 9).

Provides reproducible, non-destructive statistical benchmarking across all 20 crawler/extractor tools:
1. Multi-Iteration Statistical Profiling (p50, p90, p99 latency, mean, min, max, std dev).
2. Deep Process Telemetry (RSS RAM delta in MB, peak CPU utilization % via psutil).
3. Data Lake Yield Efficiency (Cleaned Output Bytes / Raw Ingested Bytes).
4. Weighted Composite Quality Scoring:
   Composite = (0.35 * Speed) + (0.30 * Richness) + (0.25 * Stealth) + (0.10 * Memory)
5. Multi-Cohort Battery Tournaments with Radar/Spider Matrix Vectors ([Speed, Richness, Stealth, Memory, Reliability]).
6. Persistent Structured Reports (JSON + Human-Readable Markdown in index_store/benchmark_reports/).
7. Stage 6 4-Tier Structured Logging to logs/stages/stage_6_benchmarking.jsonl.
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

from core.human_timing import HumanTimingEngine
from core.logger_engine import LogEngine, log_global
from core.state_tracker import update_progress

BENCHMARK_REPORTS_DIR = ROOT / "index_store" / "benchmark_reports"
REGISTRY_PATH = ROOT / "tools" / "registry.json"

# Representative multi-cohort squad when tool_ids is None
DEFAULT_BENCHMARK_SQUAD = [
    "01_curl_cffi",
    "04_httpx_parsel",
    "06_playwright",
    "16_crawl4ai",
]


class BenchmarkEngine:
    """
    Coordinates single-tool and multi-cohort battery benchmarking with statistical
    latency percentiles, process footprint measurement, data yield efficiency,
    and composite multi-vector scoring.
    """

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or BENCHMARK_REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
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

    # ------------------------------------------------------------------
    # Statistical & Score Calculators
    # ------------------------------------------------------------------

    @staticmethod
    def compute_percentiles(latencies: list[float]) -> dict[str, float]:
        """
        Calculates p50, p90, p99, mean, min, max, and std_dev from a list of latencies
        using linear quantile interpolation (NIST method).
        """
        if not latencies:
            return {
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std_dev": 0.0,
            }

        sorted_vals = sorted(latencies)
        n = len(sorted_vals)

        def _quantile(q: float) -> float:
            if n == 1:
                return sorted_vals[0]
            idx = (n - 1) * q
            lower = int(idx)
            upper = min(lower + 1, n - 1)
            weight = idx - lower
            return sorted_vals[lower] + weight * (sorted_vals[upper] - sorted_vals[lower])

        mean_val = sum(sorted_vals) / n
        variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n
        std_dev = variance ** 0.5

        return {
            "p50": round(_quantile(0.50), 3),
            "p90": round(_quantile(0.90), 3),
            "p99": round(_quantile(0.99), 3),
            "mean": round(mean_val, 3),
            "min": round(sorted_vals[0], 3),
            "max": round(sorted_vals[-1], 3),
            "std_dev": round(std_dev, 3),
        }

    @staticmethod
    def compute_composite_score(
        speed_score: float,
        richness_score: float,
        stealth_score: float,
        memory_efficiency_score: float,
    ) -> float:
        """
        Calculates normalized weighted composite quality score bounded in [0.0, 100.0]:
        Composite = (0.35 * Speed) + (0.30 * Richness) + (0.25 * Stealth) + (0.10 * Memory)
        """
        sp = max(0.0, min(100.0, float(speed_score)))
        rc = max(0.0, min(100.0, float(richness_score)))
        st = max(0.0, min(100.0, float(stealth_score)))
        me = max(0.0, min(100.0, float(memory_efficiency_score)))

        composite = (0.35 * sp) + (0.30 * rc) + (0.25 * st) + (0.10 * me)
        return round(max(0.0, min(100.0, composite)), 2)

    @staticmethod
    def resolve_stealth_score(tool_id: str, default: float = 88.0) -> float:
        """Derives architectural stealth baseline score based on anti-detection mechanisms."""
        stealth_map = {
            "07_patchright": 98.0,
            "08_camoufox": 98.0,
            "09_nodriver": 98.0,
            "01_curl_cffi": 95.0,
            "10_scrapling": 95.0,
            "06_playwright": 92.0,
            "16_crawl4ai": 92.0,
            "04_httpx_parsel": 85.0,
            "02_scrappy": 85.0,
            "03_selenium": 80.0,
        }
        return stealth_map.get(tool_id, default)

    # ------------------------------------------------------------------
    # Single Tool Benchmark Execution
    # ------------------------------------------------------------------

    def run_tool_benchmark(
        self,
        tool_id: str,
        target_url: str = "https://quotes.toscrape.com",
        iterations: int = 3,
        human_mode: bool = False,
        timing_profile: str = "FAST_AUTOMATED",
        auth_account_id: str = "",
        action_name: str = "benchmark_run",
    ) -> dict[str, Any]:
        """
        Executes N consecutive runs of a specific tool against target_url.
        Measures per-iteration latency, RSS RAM footprint delta, peak CPU %,
        raw ingested bytes, and cleaned data yield.
        Returns summarized tool benchmark metrics including p50, p90, p99, and composite score.
        """
        iterations = max(1, iterations)
        process = psutil.Process(os.getpid())

        iteration_records: list[dict[str, Any]] = []
        latencies: list[float] = []
        ram_deltas: list[float] = []
        cpu_samples: list[float] = []
        raw_bytes_list: list[int] = []
        cleaned_bytes_list: list[int] = []

        log_global(
            message=f"Starting benchmark for '{tool_id}' on '{target_url}' ({iterations} iterations, human_mode={human_mode})",
            level="INFO",
            stage="Stage 6",
            step="Step 6.1",
            tool_id=tool_id,
            action_name=action_name,
            stage_log_name="stage_6_benchmarking",
        )

        for i in range(iterations):
            # Pre-iteration telemetry
            process.cpu_percent(interval=None)
            mem_before = process.memory_info().rss / (1024 * 1024)
            t0 = time.perf_counter()

            adapter_mod_name = f"tools.{tool_id}.adapter"
            status = "failed"
            error_msg = ""
            raw_result: Any = None

            try:
                adapter = importlib.import_module(adapter_mod_name)
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
                    # Generic runner lookup
                    candidate_fn = None
                    for attr in dir(adapter):
                        if attr.startswith("run_") and callable(getattr(adapter, attr)):
                            candidate_fn = getattr(adapter, attr)
                            break
                    if candidate_fn:
                        raw_result = candidate_fn(
                            target_url=target_url,
                            action_name=action_name,
                            human_mode=human_mode,
                            timing_profile=timing_profile,
                        )
                    else:
                        raise AttributeError(f"No run/run_action entrypoint found in {adapter_mod_name}")

                status = "completed"
            except Exception as exc:
                error_msg = str(exc)
                log_global(
                    message=f"Benchmark iteration {i + 1}/{iterations} error for '{tool_id}': {exc}",
                    level="WARN",
                    stage="Stage 6",
                    step="Step 6.1",
                    tool_id=tool_id,
                    action_name=action_name,
                    stage_log_name="stage_6_benchmarking",
                )

            elapsed_sec = round(time.perf_counter() - t0, 3)
            mem_after = process.memory_info().rss / (1024 * 1024)
            mem_delta_mb = round(max(0.0, mem_after - mem_before), 2)
            cpu_pct = round(process.cpu_percent(interval=None), 1)

            # Artifact discovery & byte measurement
            raw_b = 0
            cleaned_b = 0
            run_dir_path: Path | None = None

            if isinstance(raw_result, dict):
                run_info = raw_result.get("run_info") or {}
                if run_info.get("run_dir"):
                    run_dir_path = Path(run_info["run_dir"])

            if not run_dir_path or not run_dir_path.exists():
                tool_data_dir = ROOT / "data" / tool_id
                if tool_data_dir.exists():
                    all_runs = sorted(tool_data_dir.glob("*/*/*"), key=lambda p: p.stat().st_mtime, reverse=True)
                    for r in all_runs:
                        if (r / "run_manifest.json").exists():
                            run_dir_path = r
                            break

            if run_dir_path and run_dir_path.exists():
                raw_dir = run_dir_path / "raw"
                if raw_dir.exists():
                    for f in raw_dir.iterdir():
                        if f.is_file():
                            raw_b += f.stat().st_size
                cleaned_dir = run_dir_path / "cleaned"
                if cleaned_dir.exists():
                    for f in cleaned_dir.iterdir():
                        if f.is_file():
                            cleaned_b += f.stat().st_size

            yield_ratio = round(cleaned_b / max(1, raw_b), 4)

            iter_rec = {
                "iteration": i + 1,
                "status": status,
                "elapsed_sec": elapsed_sec,
                "mem_delta_mb": mem_delta_mb,
                "cpu_percent": cpu_pct,
                "raw_bytes": raw_b,
                "cleaned_bytes": cleaned_b,
                "yield_ratio": yield_ratio,
                "error": error_msg,
            }
            iteration_records.append(iter_rec)
            latencies.append(elapsed_sec)
            ram_deltas.append(mem_delta_mb)
            cpu_samples.append(cpu_pct)
            raw_bytes_list.append(raw_b)
            cleaned_bytes_list.append(cleaned_b)

        # Statistical Summaries
        percentiles = self.compute_percentiles(latencies)
        completed_count = sum(1 for r in iteration_records if r["status"] == "completed")
        error_rate = round((iterations - completed_count) / iterations, 3)

        avg_raw_bytes = int(sum(raw_bytes_list) / iterations) if raw_bytes_list else 0
        avg_cleaned_bytes = int(sum(cleaned_bytes_list) / iterations) if cleaned_bytes_list else 0
        avg_yield_ratio = round(avg_cleaned_bytes / max(1, avg_raw_bytes), 4)
        mean_mem_delta_mb = round(sum(ram_deltas) / iterations, 2) if ram_deltas else 0.0
        max_mem_delta_mb = round(max(ram_deltas), 2) if ram_deltas else 0.0
        mean_cpu_pct = round(sum(cpu_samples) / iterations, 1) if cpu_samples else 0.0

        # Quality Scores (0.0 to 100.0)
        # Speed: normalized vs. 1.0s target baseline
        p50 = percentiles["p50"]
        speed_score = round(max(5.0, min(100.0, 100.0 / (1.0 + max(0.0, p50 - 0.4) / 1.8))), 1)

        # Richness: non-zero cleaned yield
        if avg_cleaned_bytes > 0:
            richness_score = round(min(100.0, max(25.0, (min(avg_cleaned_bytes, 8000) / 8000.0) * 75.0 + (min(avg_yield_ratio, 1.0) * 25.0))), 1)
        else:
            richness_score = 10.0 if completed_count > 0 else 0.0

        # Stealth: tool evasion profile
        base_stealth = self.resolve_stealth_score(tool_id)
        stealth_score = round(base_stealth if error_rate == 0.0 else max(10.0, base_stealth * (1.0 - error_rate)), 1)

        # Memory: low RAM footprint delta
        memory_score = round(max(10.0, min(100.0, 100.0 - (mean_mem_delta_mb / 60.0) * 60.0)), 1)

        # Reliability
        reliability_score = round(100.0 * (1.0 - error_rate), 1)

        # Composite score
        composite_score = self.compute_composite_score(
            speed_score=speed_score,
            richness_score=richness_score,
            stealth_score=stealth_score,
            memory_efficiency_score=memory_score,
        )

        radar_vector = [speed_score, richness_score, stealth_score, memory_score, reliability_score]

        result = {
            "tool_id": tool_id,
            "status": "completed" if completed_count > 0 else "failed",
            "iterations": iterations,
            "completed_iterations": completed_count,
            "error_rate": error_rate,
            "p50_sec": p50,
            "p90_sec": percentiles["p90"],
            "p99_sec": percentiles["p99"],
            "mean_sec": percentiles["mean"],
            "min_sec": percentiles["min"],
            "max_sec": percentiles["max"],
            "std_dev_sec": percentiles["std_dev"],
            "mem_delta_mb": mean_mem_delta_mb,
            "max_mem_delta_mb": max_mem_delta_mb,
            "cpu_percent": mean_cpu_pct,
            "raw_bytes": avg_raw_bytes,
            "cleaned_bytes": avg_cleaned_bytes,
            "yield_ratio": avg_yield_ratio,
            "speed_score": speed_score,
            "richness_score": richness_score,
            "stealth_score": stealth_score,
            "memory_score": memory_score,
            "reliability_score": reliability_score,
            "composite_score": composite_score,
            "radar_vector": radar_vector,
            "iterations_data": iteration_records,
        }

        log_global(
            message=f"Tool benchmark finished for '{tool_id}': p50={p50}s, RAM_delta={mean_mem_delta_mb}MB, Composite={composite_score}",
            level="INFO",
            stage="Stage 6",
            step="Step 6.1",
            tool_id=tool_id,
            action_name=action_name,
            stage_log_name="stage_6_benchmarking",
        )
        return result

    # ------------------------------------------------------------------
    # Multi-Cohort Battery Benchmark Execution
    # ------------------------------------------------------------------

    def run_battery_benchmark(
        self,
        tool_ids: list[str] | str | None = None,
        target_url: str = "https://quotes.toscrape.com",
        iterations: int = 2,
        human_mode: bool = False,
        battery_label: str = "cohort_comparison",
        timing_profile: str = "FAST_AUTOMATED",
    ) -> dict[str, Any]:
        """
        Executes a comparative benchmark tournament across multiple candidate tools.
        Generates leaderboard rankings, radar vectors, and persists structured JSON & MD reports.
        """
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%Y%m%d_%H%M%S")
        report_uuid = uuid.uuid4().hex[:8]
        report_id = f"benchmark_battery_{time_str}_{report_uuid}"

        # 1. Resolve Tool Cohort
        candidate_tools: list[str] = []
        if tool_ids is None or tool_ids == [] or tool_ids == "":
            candidate_tools = list(DEFAULT_BENCHMARK_SQUAD)
        elif tool_ids == "all" or tool_ids == ["all"]:
            candidate_tools = self._get_installed_tools()
        elif isinstance(tool_ids, str):
            candidate_tools = [t.strip() for t in tool_ids.split(",") if t.strip()]
        else:
            candidate_tools = list(tool_ids)

        seen = set()
        resolved_tools: list[str] = []
        for t in candidate_tools:
            if t and t not in seen:
                seen.add(t)
                resolved_tools.append(t)

        total_tools = len(resolved_tools)
        if total_tools == 0:
            raise ValueError("No valid candidate tool IDs provided for battery benchmark.")

        log_global(
            message=f"Launching Benchmark Battery '{report_id}': {total_tools} tools vs. '{target_url}' ({iterations} iters/tool)",
            level="INFO",
            stage="Stage 6",
            step="Step 6.1",
            tool_id="core_benchmark_engine",
            action_name="run_battery_benchmark",
            stage_log_name="stage_6_benchmarking",
        )

        battery_start_t = time.perf_counter()
        tool_results: list[dict[str, Any]] = []

        # 2. Sequential Tool Execution with Telemetry
        for idx, tool_id in enumerate(resolved_tools):
            pct_start = int((idx / total_tools) * 90)
            update_progress(
                pct_start,
                subtask=f"Benchmark: Testing {tool_id} (Iteration 1/{iterations})",
            )

            tool_metrics = self.run_tool_benchmark(
                tool_id=tool_id,
                target_url=target_url,
                iterations=iterations,
                human_mode=human_mode,
                timing_profile=timing_profile,
                action_name=battery_label,
            )
            tool_results.append(tool_metrics)

            pct_end = int(((idx + 1) / total_tools) * 90)
            update_progress(
                pct_end,
                subtask=f"Benchmark: Finished {tool_id} (Composite: {tool_metrics.get('composite_score', 0)})",
            )

        total_elapsed_sec = round(time.perf_counter() - battery_start_t, 3)

        # 3. Rankings & Leaderboard Sorting
        # Sort by composite_score desc, then p50_sec asc
        ranked = sorted(
            tool_results,
            key=lambda x: (x.get("composite_score", 0), -x.get("p50_sec", 999)),
            reverse=True,
        )

        for rank_idx, item in enumerate(ranked):
            item["rank"] = rank_idx + 1

        winner_tool = ranked[0]["tool_id"] if ranked else "None"
        winner_score = ranked[0]["composite_score"] if ranked else 0.0

        if ranked and ranked[0]["status"] == "completed":
            top = ranked[0]
            winner_rationale = (
                f"Winner '{winner_tool}' achieved the highest composite score of {winner_score}/100 "
                f"(Speed: {top['speed_score']}, Richness: {top['richness_score']}, Stealth: {top['stealth_score']}, "
                f"Memory: {top['memory_score']}) with p50 latency of {top['p50_sec']}s and yield ratio of {top['yield_ratio']}."
            )
        else:
            winner_rationale = "No candidate tool completed all benchmark iterations successfully."

        # Radar Matrix Mapping
        radar_matrix = {
            t["tool_id"]: t.get("radar_vector", [0, 0, 0, 0, 0])
            for t in ranked
        }

        # 4. Assemble Battery Report Document
        report_data = {
            "report_id": report_id,
            "created_at": now.isoformat(),
            "target_url": target_url,
            "battery_label": battery_label,
            "iterations_per_tool": iterations,
            "human_mode": human_mode,
            "timing_profile": timing_profile,
            "total_tools": total_tools,
            "tools_tested": resolved_tools,
            "total_elapsed_sec": total_elapsed_sec,
            "winner_tool": winner_tool,
            "winner_composite_score": winner_score,
            "winner_rationale": winner_rationale,
            "radar_axes": ["Speed", "Richness", "Stealth", "Memory", "Reliability"],
            "radar_matrix": radar_matrix,
            "leaderboard": ranked,
        }

        # 5. Persist JSON & Markdown Reports
        json_path = self.reports_dir / f"{report_id}.json"
        md_path = self.reports_dir / f"{report_id}.md"

        json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
        markdown_content = self._render_markdown_report(report_data)
        md_path.write_text(markdown_content, encoding="utf-8")

        report_data["json_report_path"] = str(json_path.relative_to(ROOT)).replace("\\", "/")
        report_data["md_report_path"] = str(md_path.relative_to(ROOT)).replace("\\", "/")

        update_progress(100, subtask=f"Benchmark battery complete. Winner: {winner_tool} ({winner_score}/100)")
        log_global(
            message=f"Benchmark battery '{report_id}' complete. Winner: {winner_tool} ({winner_score}/100). Reports saved.",
            level="INFO",
            stage="Stage 6",
            step="Step 6.1",
            tool_id="core_benchmark_engine",
            action_name="run_battery_benchmark",
            stage_log_name="stage_6_benchmarking",
        )

        return report_data

    # ------------------------------------------------------------------
    # Markdown Report Renderer
    # ------------------------------------------------------------------

    def _render_markdown_report(self, report: dict[str, Any]) -> str:
        """Renders comprehensive, human-readable Markdown benchmark report."""
        created_at = report.get("created_at", "")
        target_url = report.get("target_url", "")
        winner = report.get("winner_tool", "N/A")
        winner_score = report.get("winner_composite_score", 0.0)
        leaderboard = report.get("leaderboard", [])

        md = [
            f"# 📊 20-Tool Benchmark Performance Matrix Report",
            f"**Report ID:** `{report.get('report_id')}` | **Target:** `{target_url}` | **Date:** {created_at}",
            "",
            f"> 🏆 **Tournament Winner:** `{winner}` — **Composite Score:** **{winner_score} / 100**",
            f"> *{report.get('winner_rationale', '')}*",
            "",
            "---",
            "",
            "## 1. Executive Performance Leaderboard",
            "",
            "| Rank | Tool ID | Status | p50 (s) | p90 (s) | p99 (s) | RAM Δ (MB) | CPU % | Yield Ratio | Speed | Richness | Stealth | Memory | **Composite** |",
            "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]

        for item in leaderboard:
            rank = item.get("rank", 99)
            badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            status_ico = "✅" if item.get("status") == "completed" else "❌"
            md.append(
                f"| {badge} | `{item.get('tool_id')}` | {status_ico} | "
                f"{item.get('p50_sec', 0.0)}s | {item.get('p90_sec', 0.0)}s | {item.get('p99_sec', 0.0)}s | "
                f"{item.get('mem_delta_mb', 0.0)} MB | {item.get('cpu_percent', 0.0)}% | {item.get('yield_ratio', 0.0)} | "
                f"{item.get('speed_score', 0.0)} | {item.get('richness_score', 0.0)} | {item.get('stealth_score', 0.0)} | "
                f"{item.get('memory_score', 0.0)} | **{item.get('composite_score', 0.0)}** |"
            )

        md.extend([
            "",
            "## 2. Multi-Vector Radar Matrix (0–100 Scale)",
            "",
            "| Tool ID | Speed (35%) | Richness (30%) | Stealth (25%) | Memory (10%) | Reliability |",
            "|:---|:---:|:---:|:---:|:---:|:---:|",
        ])

        for item in leaderboard:
            v = item.get("radar_vector", [0, 0, 0, 0, 0])
            md.append(f"| `{item.get('tool_id')}` | {v[0]} | {v[1]} | {v[2]} | {v[3]} | {v[4]} |")

        md.extend([
            "",
            "## 3. Detailed Per-Tool Iteration Telemetry",
            "",
        ])

        for item in leaderboard:
            tool_id = item.get("tool_id", "unknown")
            md.extend([
                f"### Tool: `{tool_id}`",
                f"- **Iterations Completed:** {item.get('completed_iterations')}/{item.get('iterations')} (Error Rate: {item.get('error_rate')})",
                f"- **Latency Distribution:** Mean: {item.get('mean_sec')}s | Min: {item.get('min_sec')}s | Max: {item.get('max_sec')}s | StdDev: {item.get('std_dev_sec')}s",
                f"- **Data Lake Ingest:** Raw: {item.get('raw_bytes', 0):,} bytes | Cleaned: {item.get('cleaned_bytes', 0):,} bytes | Yield: {item.get('yield_ratio', 0.0)}",
                "",
                "| Iteration | Status | Elapsed (s) | RAM Δ (MB) | CPU % | Raw Bytes | Cleaned Bytes | Yield |",
                "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
            ])
            for it in item.get("iterations_data", []):
                st_ico = "✅" if it.get("status") == "completed" else "❌"
                md.append(
                    f"| #{it.get('iteration')} | {st_ico} | {it.get('elapsed_sec')}s | "
                    f"{it.get('mem_delta_mb')} MB | {it.get('cpu_percent')}% | {it.get('raw_bytes', 0):,} | "
                    f"{it.get('cleaned_bytes', 0):,} | {it.get('yield_ratio', 0.0)} |"
                )
            md.append("")

        md.extend([
            "---",
            "## 4. Governance & Reproducibility Notice",
            f"- Generated by `core/benchmark_engine.py` under Antigravity Rule 9 (Benchmark Traceability & Non-Destructive Testing).",
            f"- Telemetry logged into `logs/stages/stage_6_benchmarking.jsonl`.",
            f"- Master index synchronized with `index_store/global_master_index.sqlite`.",
        ])

        return "\n".join(md)

    # ------------------------------------------------------------------
    # Discovery & Retrieval APIs
    # ------------------------------------------------------------------

    def list_benchmark_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        """Scans and lists historical benchmark reports from index_store/benchmark_reports/."""
        reports: list[dict[str, Any]] = []
        if not self.reports_dir.exists():
            return reports

        for f in self.reports_dir.glob("*.json"):
            if f.name.endswith(".gitkeep"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                reports.append({
                    "report_id": data.get("report_id", f.stem),
                    "created_at": data.get("created_at"),
                    "battery_label": data.get("battery_label", ""),
                    "target_url": data.get("target_url", ""),
                    "tools_count": len(data.get("tools_tested", [])),
                    "winner_tool": data.get("winner_tool", "N/A"),
                    "winner_composite_score": data.get("winner_composite_score", 0.0),
                    "total_elapsed_sec": data.get("total_elapsed_sec", 0.0),
                    "json_path": str(f.relative_to(ROOT)).replace("\\", "/"),
                    "md_path": str(f.with_suffix(".md").relative_to(ROOT)).replace("\\", "/") if f.with_suffix(".md").exists() else "",
                })
            except Exception:
                continue

        reports.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return reports[:limit]

    def get_benchmark_report(self, report_id: str) -> dict[str, Any] | None:
        """Retrieves a specific benchmark report (JSON + Markdown content)."""
        clean_id = report_id.replace(".json", "").replace(".md", "")
        json_file = self.reports_dir / f"{clean_id}.json"
        md_file = self.reports_dir / f"{clean_id}.md"

        if not json_file.exists():
            return None

        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if md_file.exists():
                data["markdown_content"] = md_file.read_text(encoding="utf-8")
            return data
        except Exception:
            return None


def get_benchmark_engine(reports_dir: Path | None = None) -> BenchmarkEngine:
    """Convenience factory returning a BenchmarkEngine instance."""
    return BenchmarkEngine(reports_dir=reports_dir)
