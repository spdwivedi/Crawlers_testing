"""
core/task_router.py
===================
Precision Task Router & Multi-Tool Chaining Engine — Stage 4 / Step 4.5
(The 3 Working Ways: Working Way 3 Precision Task Router & Multi-Tool Chaining).

Orchestrates multi-stage tool pipelines with explicit artifact hand-offs,
telemetry progression, consolidated deliverables, and unified reporting:
1. Pipeline Stage Contract & Architecture (PipelineStage specification).
2. Contextual Artifact Resolution & Automatic Predecessor Handoffs.
3. Canonical Pipeline Recipes (GraphQL -> Markdown, Stream -> Whisper, Browser -> OCR).
4. Consolidated Deliverables & Structured Reporting (.json & .md in index_store/pipeline_reports/).
5. Query and Retrieval APIs (list_pipeline_reports, get_pipeline_report).
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
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

PIPELINE_REPORTS_DIR = ROOT / "index_store" / "pipeline_reports"
REGISTRY_PATH = ROOT / "tools" / "registry.json"


@dataclass
class PipelineStage:
    """
    Specification for a single stage within a multi-tool chained pipeline.
    """
    stage_id: str
    tool_id: str
    action_name: str
    input_from_stage: str | None = None
    input_artifact_keys: list[str] = field(default_factory=list)
    stage_kwargs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineStage:
        return cls(
            stage_id=data["stage_id"],
            tool_id=data["tool_id"],
            action_name=data["action_name"],
            input_from_stage=data.get("input_from_stage"),
            input_artifact_keys=list(data.get("input_artifact_keys", [])),
            stage_kwargs=dict(data.get("stage_kwargs", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PrecisionTaskRouter:
    """
    Orchestrates multi-stage crawler and extractor tool pipelines with
    safe artifact hand-offs, live telemetry tracking, and consolidated reports.
    """

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or PIPELINE_REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        # Ensure .gitkeep is present
        gitkeep = self.reports_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Track pipeline reports\n", encoding="utf-8")
        self.timing_engine = HumanTimingEngine()
        self.registry = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        """Loads tools/registry.json if present."""
        if REGISTRY_PATH.exists():
            try:
                return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    # -------------------------------------------------------------------------
    # Canonical Pipeline Recipes
    # -------------------------------------------------------------------------

    @staticmethod
    def build_graphql_markdown_pipeline(
        target_url: str = "https://leetcode.com/problems/two-sum/",
    ) -> dict[str, Any]:
        """
        Recipe 1: High-Speed Web Extraction & LLM-Ready Markdown Pipeline.
        Stage 1: 01_curl_cffi fetches raw LeetCode/GraphQL payload with TLS browser impersonation.
        Stage 2: 16_crawl4ai ingests payload/HTML and splits content into semantic token-aware Markdown chunks.
        """
        return {
            "pipeline_id": "graphql_markdown_chain",
            "target_url": target_url,
            "pipeline_label": "Two-Stage GraphQL Fetch to LLM-Ready Markdown Chunker",
            "stages": [
                {
                    "stage_id": "fetch",
                    "tool_id": "01_curl_cffi",
                    "action_name": "scrape_for_leetcode",
                    "input_from_stage": None,
                    "input_artifact_keys": [],
                    "stage_kwargs": {},
                },
                {
                    "stage_id": "clean_markdown",
                    "tool_id": "16_crawl4ai",
                    "action_name": "markdown_harvest",
                    "input_from_stage": "fetch",
                    "input_artifact_keys": ["raw_page.html", "graphql_payload.json", "two_sum.md"],
                    "stage_kwargs": {},
                },
            ],
        }

    @staticmethod
    def build_stream_whisper_pipeline(
        target_url: str = "https://www.instagram.com/reel/C8XYZ12345/",
    ) -> dict[str, Any]:
        """
        Recipe 2: Media Stream Interception to Speech & Knowledge Graph Pipeline.
        Stage 1: 11_yt_dlp_ffmpeg intercepts stream chunks, muxes MP4, and demuxes 16kHz mono WAV audio.
        Stage 2: 20_faster_whisper_scrapegraph transcribes WAV audio into timestamped SRT and entity knowledge graph.
        """
        return {
            "pipeline_id": "stream_whisper_chain",
            "target_url": target_url,
            "pipeline_label": "Two-Stage Stream Capture & Demux to Faster-Whisper Speech & Knowledge Graph",
            "stages": [
                {
                    "stage_id": "capture_stream",
                    "tool_id": "11_yt_dlp_ffmpeg",
                    "action_name": "stream_capture",
                    "input_from_stage": None,
                    "input_artifact_keys": [],
                    "stage_kwargs": {},
                },
                {
                    "stage_id": "transcribe_audio",
                    "tool_id": "20_faster_whisper_scrapegraph",
                    "action_name": "audio_transcribe",
                    "input_from_stage": "capture_stream",
                    "input_artifact_keys": ["audio_16k.wav", "extracted_audio.wav"],
                    "stage_kwargs": {},
                },
            ],
        }

    @staticmethod
    def build_browser_ocr_pipeline(
        target_url: str = "https://quotes.toscrape.com/js/",
    ) -> dict[str, Any]:
        """
        Recipe 3: Browser Kinematics Snapshot to Visual ONNX OCR Pipeline.
        Stage 1: 06_playwright executes browser human flow, renders dynamic JS, and captures visual screenshot.
        Stage 2: 17_surya_ocr extracts text bounding boxes and reconstructs structured assessment sheet.
        """
        return {
            "pipeline_id": "browser_ocr_chain",
            "target_url": target_url,
            "pipeline_label": "Two-Stage Browser Kinematic Capture to ONNX OCR Exam Extractor",
            "stages": [
                {
                    "stage_id": "browse_and_capture",
                    "tool_id": "06_playwright",
                    "action_name": "secured_page_origin",
                    "input_from_stage": None,
                    "input_artifact_keys": [],
                    "stage_kwargs": {},
                },
                {
                    "stage_id": "visual_ocr",
                    "tool_id": "17_surya_ocr",
                    "action_name": "visual_test_ocr",
                    "input_from_stage": "browse_and_capture",
                    "input_artifact_keys": ["screenshot.png"],
                    "stage_kwargs": {},
                },
            ],
        }

    # -------------------------------------------------------------------------
    # Pipeline Execution Engine
    # -------------------------------------------------------------------------

    def execute_pipeline(
        self,
        pipeline_id: str,
        target_url: str,
        stages: list[PipelineStage | dict[str, Any]],
        pipeline_label: str = "",
        human_mode: bool = False,
        timing_profile: str = "BALANCED_HUMAN",
        auth_account_id: str = "",
        auth_target: str = "",
    ) -> dict[str, Any]:
        """
        Sequentially executes chained stages, dynamically passing predecessor artifacts forward,
        tracking live state telemetry, consolidating deliverables, and generating reports.
        """
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%Y%m%d_%H%M%S")
        report_uuid = uuid.uuid4().hex[:8]
        report_id = f"pipeline_run_{time_str}_{report_uuid}"

        # Normalize stages to PipelineStage instances
        normalized_stages: list[PipelineStage] = []
        for s in stages:
            if isinstance(s, PipelineStage):
                normalized_stages.append(s)
            elif isinstance(s, dict):
                normalized_stages.append(PipelineStage.from_dict(s))
            else:
                raise TypeError(f"Invalid stage specification type: {type(s)}")

        total_stages = len(normalized_stages)
        if total_stages == 0:
            raise ValueError("Pipeline has no stages defined.")

        log_global(
            message=f"Task Router launched pipeline '{pipeline_id}' ({report_id}) with {total_stages} stages on '{target_url}'",
            level="INFO",
            stage="Stage 4",
            step="Step 4.5",
            tool_id="task_router",
            action_name="execute_pipeline",
            stage_log_name="stage_4_working_ways",
        )

        pipeline_start_t = time.perf_counter()
        stage_records: list[dict[str, Any]] = []
        stage_artifacts_store: dict[str, dict[str, Any]] = {}

        overall_status = "completed"
        pipeline_error = ""

        # Sequential Stage Execution
        for idx, stage in enumerate(normalized_stages):
            progress_pct = int(10 + (idx / total_stages) * 80)
            subtask_msg = f"Pipeline [{pipeline_id}]: Executing Stage '{stage.stage_id}' via {stage.tool_id} ({idx + 1}/{total_stages})"
            update_progress(progress_pct, subtask=subtask_msg)

            # Resolve predecessor artifacts
            consumed_artifacts: list[dict[str, Any]] = []
            resolved_kwargs: dict[str, Any] = dict(stage.stage_kwargs)

            if stage.input_from_stage:
                pred_stage_id = stage.input_from_stage
                pred_data = stage_artifacts_store.get(pred_stage_id)
                if not pred_data:
                    log_global(
                        message=f"Warning: Predecessor stage '{pred_stage_id}' artifacts not found in store.",
                        level="WARN",
                        stage="Stage 4",
                        step="Step 4.5",
                        tool_id="task_router",
                        action_name="resolve_artifacts",
                        stage_log_name="stage_4_working_ways",
                    )
                else:
                    pred_cleaned = Path(pred_data.get("cleaned_dir", ""))
                    pred_raw = Path(pred_data.get("raw_dir", ""))

                    # 1. Check explicitly requested artifact keys
                    found_keys = set()
                    for req_key in stage.input_artifact_keys:
                        # Check in cleaned dir first, then raw dir
                        target_file = None
                        if pred_cleaned.exists() and (pred_cleaned / req_key).exists():
                            target_file = pred_cleaned / req_key
                        elif pred_raw.exists() and (pred_raw / req_key).exists():
                            target_file = pred_raw / req_key

                        if target_file and target_file.exists():
                            found_keys.add(req_key)
                            consumed_artifacts.append({
                                "key": req_key,
                                "source_stage": pred_stage_id,
                                "path": str(target_file.relative_to(ROOT)),
                                "size_bytes": target_file.stat().st_size,
                            })
                            # Contextual injection based on extension / key
                            if target_file.suffix in [".html", ".json", ".md", ".txt"]:
                                resolved_kwargs.setdefault("input_file", str(target_file))
                                resolved_kwargs.setdefault("html_content", target_file.read_text(encoding="utf-8", errors="ignore"))
                            elif target_file.suffix in [".wav", ".mp3", ".m4a"]:
                                resolved_kwargs.setdefault("audio_path", str(target_file))
                                resolved_kwargs.setdefault("input_file", str(target_file))
                            elif target_file.suffix in [".png", ".jpg", ".jpeg"]:
                                resolved_kwargs.setdefault("image_path", str(target_file))
                                resolved_kwargs.setdefault("input_file", str(target_file))

                    # 2. Contextual Auto-Resolution if specific keys weren't matched
                    if not consumed_artifacts:
                        # Contextual matching for 16_crawl4ai
                        if stage.tool_id == "16_crawl4ai":
                            for candidate in ["raw_page.html", "response_page.html", "rendered_dom.html", "graphql_payload.json", "two_sum.md"]:
                                p = (pred_raw / candidate) if (pred_raw / candidate).exists() else (pred_cleaned / candidate)
                                if p.exists():
                                    resolved_kwargs["input_file"] = str(p)
                                    resolved_kwargs["html_content"] = p.read_text(encoding="utf-8", errors="ignore")
                                    consumed_artifacts.append({
                                        "key": candidate,
                                        "source_stage": pred_stage_id,
                                        "path": str(p.relative_to(ROOT)),
                                        "size_bytes": p.stat().st_size,
                                    })
                                    break

                        # Contextual matching for 20_faster_whisper_scrapegraph
                        elif stage.tool_id == "20_faster_whisper_scrapegraph":
                            for candidate in ["audio_16k.wav", "extracted_audio.wav", "audio.mp3"]:
                                p = (pred_cleaned / candidate) if (pred_cleaned / candidate).exists() else (pred_raw / candidate)
                                if p.exists():
                                    resolved_kwargs["audio_path"] = str(p)
                                    resolved_kwargs["input_file"] = str(p)
                                    consumed_artifacts.append({
                                        "key": candidate,
                                        "source_stage": pred_stage_id,
                                        "path": str(p.relative_to(ROOT)),
                                        "size_bytes": p.stat().st_size,
                                    })
                                    break

                        # Contextual matching for 17_surya_ocr
                        elif stage.tool_id == "17_surya_ocr":
                            for candidate in ["screenshot.png", "image_based_test_question.png"]:
                                p = (pred_raw / candidate) if (pred_raw / candidate).exists() else (pred_cleaned / candidate)
                                if p.exists():
                                    resolved_kwargs["image_path"] = str(p)
                                    resolved_kwargs["input_file"] = str(p)
                                    consumed_artifacts.append({
                                        "key": candidate,
                                        "source_stage": pred_stage_id,
                                        "path": str(p.relative_to(ROOT)),
                                        "size_bytes": p.stat().st_size,
                                    })
                                    break

            # Execute Stage Tool
            stage_res = self._execute_stage_tool(
                tool_id=stage.tool_id,
                stage_id=stage.stage_id,
                action_name=stage.action_name,
                target_url=target_url,
                human_mode=human_mode,
                timing_profile=timing_profile,
                resolved_kwargs=resolved_kwargs,
            )

            # Record produced artifacts
            produced_artifacts: list[dict[str, Any]] = []
            cleaned_dir_path = Path(stage_res.get("cleaned_dir", ""))
            raw_dir_path = Path(stage_res.get("raw_dir", ""))

            if cleaned_dir_path.exists():
                for f in cleaned_dir_path.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        produced_artifacts.append({
                            "name": f.name,
                            "tier": "cleaned",
                            "path": str(f.relative_to(ROOT)),
                            "size_bytes": f.stat().st_size,
                        })

            if raw_dir_path.exists():
                for f in raw_dir_path.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        produced_artifacts.append({
                            "name": f.name,
                            "tier": "raw",
                            "path": str(f.relative_to(ROOT)),
                            "size_bytes": f.stat().st_size,
                        })

            stage_data = {
                "stage_id": stage.stage_id,
                "tool_id": stage.tool_id,
                "action_name": stage.action_name,
                "status": stage_res.get("status", "failed"),
                "elapsed_sec": stage_res.get("elapsed_sec", 0.0),
                "peak_rss_mb": stage_res.get("peak_rss_mb", 0.0),
                "run_id": stage_res.get("run_id", ""),
                "run_dir": stage_res.get("run_dir", ""),
                "raw_dir": stage_res.get("raw_dir", ""),
                "cleaned_dir": stage_res.get("cleaned_dir", ""),
                "artifacts_consumed": consumed_artifacts,
                "artifacts_produced": produced_artifacts,
                "error": stage_res.get("error", ""),
            }

            stage_records.append(stage_data)
            stage_artifacts_store[stage.stage_id] = stage_data

            if stage_res.get("status") != "completed":
                overall_status = "failed"
                pipeline_error = f"Stage '{stage.stage_id}' ({stage.tool_id}) failed: {stage_res.get('error')}"
                log_global(
                    message=pipeline_error,
                    level="ERROR",
                    stage="Stage 4",
                    step="Step 4.5",
                    tool_id="task_router",
                    action_name="execute_pipeline",
                    stage_log_name="stage_4_working_ways",
                )
                break

        total_elapsed_sec = round(time.perf_counter() - pipeline_start_t, 3)

        # Consolidate Deliverables from all completed stages
        consolidated_deliverables: list[dict[str, Any]] = []
        for s in stage_records:
            if s.get("status") == "completed":
                for art in s.get("artifacts_produced", []):
                    if art.get("tier") == "cleaned":
                        consolidated_deliverables.append({
                            "stage_id": s["stage_id"],
                            "tool_id": s["tool_id"],
                            "name": art["name"],
                            "path": art["path"],
                            "size_bytes": art["size_bytes"],
                        })

        # Construct Unified Pipeline Report
        report_data = {
            "report_id": report_id,
            "pipeline_id": pipeline_id,
            "pipeline_label": pipeline_label or f"Chained Pipeline: {pipeline_id}",
            "created_at": now.isoformat(),
            "target_url": target_url,
            "status": overall_status,
            "human_mode": human_mode,
            "timing_profile": timing_profile,
            "total_stages": total_stages,
            "stages_executed": len(stage_records),
            "total_elapsed_sec": total_elapsed_sec,
            "error": pipeline_error,
            "stage_records": stage_records,
            "consolidated_deliverables": consolidated_deliverables,
        }

        # Persist JSON & Markdown Reports
        json_report_path = self.reports_dir / f"{report_id}.json"
        md_report_path = self.reports_dir / f"{report_id}.md"

        json_report_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
        markdown_content = self._render_markdown_report(report_data)
        md_report_path.write_text(markdown_content, encoding="utf-8")

        update_progress(100, subtask=f"Pipeline [{pipeline_id}] execution complete ({overall_status})")
        log_global(
            message=f"Pipeline '{pipeline_id}' ({report_id}) finished with status '{overall_status}' in {total_elapsed_sec}s ({len(consolidated_deliverables)} deliverables).",
            level="INFO" if overall_status == "completed" else "ERROR",
            stage="Stage 4",
            step="Step 4.5",
            tool_id="task_router",
            action_name="execute_pipeline",
            stage_log_name="stage_4_working_ways",
        )

        report_data["json_report_path"] = str(json_report_path.relative_to(ROOT))
        report_data["md_report_path"] = str(md_report_path.relative_to(ROOT))
        return report_data

    # -------------------------------------------------------------------------
    # In-Process Stage Execution Helper
    # -------------------------------------------------------------------------

    def _execute_stage_tool(
        self,
        tool_id: str,
        stage_id: str,
        action_name: str,
        target_url: str,
        human_mode: bool,
        timing_profile: str,
        resolved_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executes an individual tool adapter for a pipeline stage with memory tracking.
        """
        process = psutil.Process(os.getpid())
        t0 = time.perf_counter()
        adapter_module_name = f"tools.{tool_id}.adapter"
        adapter = None
        exec_error = ""
        raw_result: Any = None
        status = "failed"

        try:
            adapter = importlib.import_module(adapter_module_name)
            call_kwargs = dict(resolved_kwargs)
            call_kwargs["human_mode"] = human_mode
            call_kwargs["timing_profile"] = timing_profile

            # Try entrypoints: run(), run_action(), or candidate func
            if hasattr(adapter, "run") and callable(getattr(adapter, "run")):
                raw_result = adapter.run(
                    target_url=target_url,
                    action_name=action_name,
                    **call_kwargs,
                )
            elif hasattr(adapter, "run_action") and callable(getattr(adapter, "run_action")):
                raw_result = adapter.run_action(
                    action_name=action_name,
                    target_url=target_url,
                    **call_kwargs,
                )
            else:
                candidate_func = None
                for attr in dir(adapter):
                    if attr.startswith("run_") and callable(getattr(adapter, attr)):
                        candidate_func = getattr(adapter, attr)
                        break
                if candidate_func:
                    raw_result = candidate_func(
                        target_url=target_url,
                        action_name=action_name,
                        **call_kwargs,
                    )
                else:
                    raise AttributeError(f"Adapter {adapter_module_name} has no recognized run/run_action entrypoint.")

            status = "completed"
        except Exception as exc:
            exec_error = str(exc)
            log_global(
                message=f"Pipeline Stage '{stage_id}' execution failed on {tool_id}: {exc}",
                level="ERROR",
                stage="Stage 4",
                step="Step 4.5",
                tool_id="task_router",
                action_name=action_name,
                stage_log_name="stage_4_working_ways",
            )

        elapsed_sec = round(time.perf_counter() - t0, 3)
        rss_mb = round(process.memory_info().rss / (1024 * 1024), 2)

        # Extract run_dir, raw_dir, cleaned_dir from raw_result
        run_info = {}
        if isinstance(raw_result, dict):
            run_info = raw_result.get("run_info", {})
            if not run_info and "manifest" in raw_result:
                run_info = raw_result["manifest"]

        run_id = run_info.get("run_id", "")
        raw_dir = str(run_info.get("raw_dir", ""))
        cleaned_dir = str(run_info.get("cleaned_dir", ""))
        run_dir = str(run_info.get("run_dir", ""))
        if not run_dir and raw_dir:
            run_dir = str(Path(raw_dir).parent)

        return {
            "tool_id": tool_id,
            "stage_id": stage_id,
            "action_name": action_name,
            "status": status,
            "elapsed_sec": elapsed_sec,
            "peak_rss_mb": rss_mb,
            "run_id": run_id,
            "run_dir": run_dir,
            "raw_dir": raw_dir,
            "cleaned_dir": cleaned_dir,
            "raw_result": raw_result,
            "error": exec_error,
        }

    # -------------------------------------------------------------------------
    # Markdown Report Generation
    # -------------------------------------------------------------------------

    def _render_markdown_report(self, report: dict[str, Any]) -> str:
        """
        Renders a textbook-grade Markdown summary of the chained pipeline run.
        """
        stages = report.get("stage_records", [])
        deliverables = report.get("consolidated_deliverables", [])
        status_badge = "✅ COMPLETED" if report.get("status") == "completed" else "❌ FAILED"

        # Construct Mermaid Flowchart
        mermaid_lines = ["```mermaid", "flowchart LR"]
        for idx, s in enumerate(stages):
            node_id = f"S{idx}"
            node_label = f"{s['stage_id']}\\n({s['tool_id']})"
            mermaid_lines.append(f'    {node_id}["{node_label}"]')
            if idx > 0:
                prev_id = f"S{idx - 1}"
                mermaid_lines.append(f"    {prev_id} --> {node_id}")
        mermaid_lines.append("```")
        mermaid_block = "\n".join(mermaid_lines)

        # Stage table rows
        stage_rows = []
        for idx, s in enumerate(stages, 1):
            consumed_str = ", ".join(f"`{c['key']}`" for c in s.get("artifacts_consumed", [])) or "*(Initial Input)*"
            produced_count = len(s.get("artifacts_produced", []))
            stage_rows.append(
                f"| {idx} | `{s['stage_id']}` | `{s['tool_id']}` | `{s['action_name']}` | {s['elapsed_sec']}s | `{s['status']}` | {consumed_str} | {produced_count} files |"
            )
        stages_table = "\n".join(stage_rows)

        # Deliverables table rows
        deliv_rows = []
        for idx, d in enumerate(deliverables, 1):
            deliv_rows.append(
                f"| {idx} | `{d['name']}` | `{d['stage_id']}` | `{d['tool_id']}` | {round(d['size_bytes'] / 1024, 1)} KB | `{d['path']}` |"
            )
        deliv_table = "\n".join(deliv_rows) if deliv_rows else "| - | No deliverables produced | - | - | - | - |"

        return f"""# 🔗 Precision Pipeline Chaining Report: `{report.get('report_id')}`

- **Pipeline ID:** `{report.get('pipeline_id')}`
- **Label:** {report.get('pipeline_label')}
- **Target URL:** `{report.get('target_url')}`
- **Execution Status:** **{status_badge}**
- **Total Pipeline Latency:** `{report.get('total_elapsed_sec')}s`
- **Execution Mode:** `human_mode={report.get('human_mode')}` (`{report.get('timing_profile')}`)
- **Total Stages:** {report.get('total_stages')}

---

## 1. Pipeline Stage Handoff Architecture

{mermaid_block}

---

## 2. Stage-by-Stage Execution Breakdown

| # | Stage ID | Tool ID | Action Name | Duration | Status | Artifacts Ingested | Deliverables |
|:---:|:---|:---|:---|:---:|:---:|:---|:---:|
{stages_table}

---

## 3. Consolidated End-to-End Deliverables

| # | Artifact Name | Producing Stage | Producing Tool | Size | Workspace Relative Path |
|:---:|:---|:---|:---|:---:|:---|
{deliv_table}

---

*Report automatically generated by Antigravity PrecisionTaskRouter (Stage 4 / Step 4.5). Auto-indexed into GlobalMasterIndexer.*
"""

    # -------------------------------------------------------------------------
    # Report Retrieval APIs
    # -------------------------------------------------------------------------

    def list_pipeline_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Returns metadata summaries of historical pipeline executions sorted newest first.
        """
        if not self.reports_dir.exists():
            return []

        summaries: list[dict[str, Any]] = []
        for report_file in self.reports_dir.glob("pipeline_run_*.json"):
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
                summaries.append({
                    "report_id": data.get("report_id", report_file.stem),
                    "pipeline_id": data.get("pipeline_id"),
                    "pipeline_label": data.get("pipeline_label"),
                    "created_at": data.get("created_at"),
                    "status": data.get("status"),
                    "target_url": data.get("target_url"),
                    "total_stages": data.get("total_stages"),
                    "total_elapsed_sec": data.get("total_elapsed_sec"),
                    "deliverables_count": len(data.get("consolidated_deliverables", [])),
                    "json_report_path": str(report_file.relative_to(ROOT)),
                    "md_report_path": str((self.reports_dir / f"{report_file.stem}.md").relative_to(ROOT)),
                })
            except Exception:
                continue

        summaries.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return summaries[:limit]

    def get_pipeline_report(self, report_id: str) -> dict[str, Any] | None:
        """
        Retrieves full structured JSON data for a specific pipeline execution report.
        """
        target_path = self.reports_dir / f"{report_id}.json"
        if not target_path.exists():
            # Try report_id directly as path
            candidate = Path(report_id)
            if candidate.exists() and candidate.is_file():
                target_path = candidate
            else:
                return None

        try:
            return json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return None


if __name__ == "__main__":
    router = PrecisionTaskRouter()
    print(f"Task Router initialized with {len(router.list_pipeline_reports())} existing reports.")
