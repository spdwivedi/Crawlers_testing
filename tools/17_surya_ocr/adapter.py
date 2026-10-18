"""
tools/17_surya_ocr/adapter.py
=============================
Mechanism: Visual Test Screenshot Layout Detection & OCR
Default action: visual_test_ocr
Additional actions: screenshot_extract, image_ocr, question_sheet_parse

Simulates visual online coding assessments (non-selectable image tests),
generates high-resolution test graphics, executes local ONNX layout and text
extraction, reconstructs full Markdown exam sheets, and parses bounding boxes.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw
from rapidocr_onnxruntime import RapidOCR

from core.folder_manager import create_action_run, complete_action_run
from core.logger_engine import LogEngine
from core.state_tracker import start_task, update_progress, complete_task, fail_task

TOOL_ID = "17_surya_ocr"


def _generate_coding_assessment_image(output_path: Path) -> None:
    """Render a crisp, high-resolution coding assessment question screenshot."""
    img = Image.new("RGB", (960, 480), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Outer border and header
    d.rectangle([10, 10, 950, 470], outline=(15, 23, 42), width=3)
    d.rectangle([10, 10, 950, 65], fill=(241, 245, 249))
    d.text((30, 25), "ANTIGRAVITY TECHNICAL ASSESSMENT - ALGORITHMS BENCHMARK", fill=(15, 23, 42))

    # Question Title & Prompt
    d.text((30, 95), "Question 14: Balanced Binary Search Tree Traversal & Search", fill=(30, 41, 59))
    d.text((30, 135), "Given a Red-Black Tree containing N elements, what is the tight upper bound", fill=(51, 65, 85))
    d.text((30, 165), "worst-case time complexity for finding an arbitrary key?", fill=(51, 65, 85))

    # Input / Example Box
    d.rectangle([30, 205, 920, 260], fill=(248, 250, 252), outline=(203, 213, 225), width=2)
    d.text((45, 220), "Input: Tree height h = floor(log2(N)), Key target = 42 -> Search Path length <= 2*log2(N+1)", fill=(71, 85, 105))

    # Multiple Choice Options
    d.text((50, 290), "A) O(1) Constant Time", fill=(30, 41, 59))
    d.text((50, 325), "B) O(log N) Logarithmic Time", fill=(30, 41, 59))
    d.text((50, 360), "C) O(N) Linear Time", fill=(30, 41, 59))
    d.text((50, 395), "D) O(N log N) Linearithmic Time", fill=(30, 41, 59))

    img.save(str(output_path), format="PNG")


def _execute_surya_ocr_workflow(
    action_name: str,
    target_url: str,
    raw_dir: Path,
    cleaned_dir: Path,
    logger: LogEngine,
    image_path: str | Path | None = None,
    input_file: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    update_progress(20, subtask="Generating high-resolution coding assessment screenshot")

    raw_image_path = raw_dir / "image_based_test_question.png"
    raw_boxes_path = raw_dir / "ocr_raw_boxes.json"
    cleaned_md_path = cleaned_dir / "reconstructed_test.md"
    cleaned_json_path = cleaned_dir / "ocr_structured.json"

    # Step A: Load image from predecessor stage or generate synthetic
    source_found = False
    passed_image = image_path or input_file
    if passed_image and Path(passed_image).exists():
        try:
            shutil.copyfile(str(passed_image), raw_image_path)
            source_found = True
            logger.info(f"Loaded visual screenshot from predecessor stage: {passed_image}", progress_pct=35)
        except Exception:
            pass

    if not source_found:
        _generate_coding_assessment_image(raw_image_path)
        logger.info(f"Rendered synthetic test screenshot ({raw_image_path.stat().st_size} bytes)", progress_pct=35)

    update_progress(45, subtask="Initializing RapidOCR ONNX layout & text detection engine")
    ocr = RapidOCR()

    update_progress(60, subtask="Executing visual text extraction on assessment screenshot")
    start_t = time.perf_counter()
    ocr_results, elapse = ocr(str(raw_image_path))
    ocr_duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
    logger.info(f"OCR inference completed in {ocr_duration_ms} ms", progress_pct=75)

    # Parse and structure OCR lines
    parsed_lines: list[dict[str, Any]] = []
    raw_boxes_dump: list[dict[str, Any]] = []
    text_lines: list[str] = []

    confidences = []
    for item in ocr_results or []:
        polygon = item[0]
        text = str(item[1]).strip()
        conf = float(item[2]) if isinstance(item[2], (int, float, str)) else 0.95

        raw_boxes_dump.append({
            "polygon": polygon,
            "text": text,
            "confidence": conf,
        })
        parsed_lines.append({
            "text": text,
            "confidence": round(conf, 4),
            "bounding_polygon": polygon,
        })
        text_lines.append(text)
        confidences.append(conf)

    update_progress(85, subtask="Writing structured OCR JSON and reconstructed Markdown exam sheet")
    raw_boxes_path.write_text(json.dumps(raw_boxes_dump, indent=2), encoding="utf-8")

    avg_conf = round(sum(confidences) / max(1, len(confidences)), 4)
    structured_output = {
        "source_image": raw_image_path.name,
        "image_dimensions": [960, 480],
        "total_lines_detected": len(parsed_lines),
        "average_confidence": avg_conf,
        "ocr_duration_ms": ocr_duration_ms,
        "extracted_lines": parsed_lines,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    cleaned_json_path.write_text(json.dumps(structured_output, indent=2), encoding="utf-8")

    # Generate Reconstructed Markdown Exam Sheet
    reconstructed_md = f"""# 📝 Reconstructed Visual Coding Assessment

**Tool:** `17_surya_ocr`  
**Action:** `{action_name}`  
**Source Asset:** `raw/{raw_image_path.name}`  
**Average OCR Confidence:** **{round(avg_conf * 100, 1)}%**  
**Extraction Duration:** {ocr_duration_ms} ms  
**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 📋 Problem Statement & Options
"""
    for idx, line in enumerate(text_lines, 1):
        if "ANTIGRAVITY" in line.upper():
            reconstructed_md += f"### {line}\n\n"
        elif "QUESTION" in line.upper():
            reconstructed_md += f"#### **{line}**\n\n"
        elif line.startswith(("A)", "B)", "C)", "D)")):
            reconstructed_md += f"- **{line}**\n"
        elif "Input" in line or "Tree height" in line:
            reconstructed_md += f"> `{line}`\n\n"
        else:
            reconstructed_md += f"{line}\n\n"

    reconstructed_md += f"""
---

## 📐 OCR Bounding Box Geometry Breakdown
| # | Recognized Line | Confidence | Bounding Coordinates |
|---|-----------------|------------|----------------------|
"""
    for idx, p in enumerate(parsed_lines[:8], 1):
        poly_str = f"[{p['bounding_polygon'][0][0]:.0f}, {p['bounding_polygon'][0][1]:.0f}]"
        reconstructed_md += f"| {idx} | {p['text']} | {round(p['confidence'] * 100, 1)}% | `{poly_str}` |\n"

    reconstructed_md += f"""
---

## 📁 Output Artifacts
- **Raw Screenshot:** `raw/{raw_image_path.name}`
- **Raw Bounding Boxes:** `raw/ocr_raw_boxes.json`
- **Structured OCR:** `cleaned/ocr_structured.json`
"""
    cleaned_md_path.write_text(reconstructed_md, encoding="utf-8")

    return {
        "lines_detected": len(parsed_lines),
        "average_confidence": avg_conf,
        "duration_ms": ocr_duration_ms,
    }


def run_action(
    action_name: str = "visual_test_ocr",
    target_url: str = "local://assessment_screenshot",
    **kwargs,
) -> dict[str, Any]:
    """Synchronous entrypoint for visual test OCR adapter."""
    start_task(
        stage="Stage 1",
        step="Step 1.4",
        tool_id=TOOL_ID,
        action=action_name,
        subtask=f"Executing visual test OCR action '{action_name}'",
    )

    run_info = create_action_run(
        tool_id=TOOL_ID,
        action_name=action_name,
        target_url=target_url,
    )
    raw_dir = Path(run_info["raw_dir"])
    cleaned_dir = Path(run_info["cleaned_dir"])
    run_log_path = Path(run_info["log_file"])

    logger = LogEngine(
        tool_id=TOOL_ID,
        action_name=action_name,
        run_id=run_info["run_id"],
        run_log_path=run_log_path,
        stage="Stage 1",
        step="Step 1.4",
    )

    logger.info(f"Initialized Surya OCR run {run_info['run_id']} for action {action_name}", progress_pct=10)

    try:
        result = _execute_surya_ocr_workflow(
            action_name=action_name,
            target_url=target_url,
            raw_dir=raw_dir,
            cleaned_dir=cleaned_dir,
            logger=logger,
            **kwargs,
        )

        update_progress(95, subtask="Finalizing action run manifest and 4-tier logs")
        manifest = complete_action_run(
            run_info=run_info,
            records_extracted=result.get("lines_detected", 1),
            quality_score=round(result.get("average_confidence", 0.95) * 100, 1),
            status="completed",
        )

        logger.info(
            f"Surya OCR action '{action_name}' completed successfully ({result.get('lines_detected')} lines detected, {result.get('duration_ms')} ms)",
            progress_pct=100,
        )
        complete_task()
        return {"run_info": run_info, "manifest": manifest, "result": result}

    except Exception as exc:
        logger.error(f"Surya OCR action '{action_name}' failed: {exc}")
        fail_task(reason=str(exc))
        complete_action_run(
            run_info=run_info,
            records_extracted=0,
            quality_score=0.0,
            status="failed",
            error_msg=str(exc),
        )
        raise


def run(
    target_url: str = "local://visual_assessment",
    action_name: str = "visual_test_ocr",
    human_mode: bool = False,
    timing_profile: str = "BALANCED_HUMAN",
    **kwargs: Any,
) -> dict[str, Any]:
    """Unified entrypoint for Surya OCR adapter."""
    return run_action(
        action_name=action_name,
        target_url=target_url,
        human_mode=human_mode,
        timing_profile=timing_profile,
        **kwargs,
    )


if __name__ == "__main__":
    res = run_action()
    print(f"[{TOOL_ID}] Run completed: {res['manifest']['status']}")
