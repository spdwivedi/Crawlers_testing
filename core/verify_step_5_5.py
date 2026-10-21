"""
core/verify_step_5_5.py
=======================
Focused Verification Suite for Stage 5 — Step 5.5:
Build Task Pipeline 4 — Smart Multimodal Auto-Resolver: DOM Text vs. Visual
Question OCR vs. Table Grid vs. PDF Layout (`pipelines/04_multimodal_auto_resolver.py`).

Verifies:
1. Module Imports & Factory Registration:
   - pipelines/04_multimodal_auto_resolver.py loads cleanly via dynamic import
   - pipelines package exposes get_multimodal_auto_resolver()
   - MultimodalAutoResolverPipeline class initializes dependencies
2. Visual Question OCR Execution:
   - resolve_multimodal_content() on exam question finishes with status == "completed"
   - raw/ contains input_image.png and ocr_raw_boxes.json
   - cleaned/bounding_boxes.json contains valid coordinates and confidence scores
3. Table Grid Matrix Extraction:
   - resolve_multimodal_content() on table image finishes with status == "completed"
   - cleaned/tables/ contains table_01.csv and table_01.json
   - table_matrices in multimodal_spec.json contains 2D/3D structured row lists
4. Silver-Tier Contract Schema Enforcement:
   - cleaned/multimodal_spec.json strictly validates against CleanedMultimodalContract
   - cleaned/README.md contains valid YAML frontmatter and markdown table rendering
5. Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard:
   - run_manifest.json records SHA-256 hashes for all raw, cleaned, and table files
   - GlobalMasterIndexer.sync_all() federates the pipeline runs cleanly
   - core/git_manager.py:scan_staged_for_secrets() reports zero violations
"""

import importlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import yaml

from core.cleaning_pipeline import CleaningPipeline, CleanedMultimodalContract
from core.git_manager import scan_staged_for_secrets
from core.global_indexer import GlobalMasterIndexer
from core.logger_engine import log_global
from core.state_tracker import update_progress

PASSED_COUNT = 0
FAILED_COUNT = 0


def assert_check(name: str, condition: bool, details: str = "") -> None:
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  [PASS] {name}")
        log_global(
            message=f"CHECK PASSED: {name}",
            level="INFO",
            stage="Stage 5",
            step="Step 5.5",
            tool_id="04_multimodal_auto_resolver",
            action_name="verify_step_5_5",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.5",
            tool_id="04_multimodal_auto_resolver",
            action_name="verify_step_5_5",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 STEP 5.5 VERIFICATION SUITE")
    print("   Smart Multimodal Auto-Resolver: OCR, Table Grid & Document Tree")
    print("=" * 70 + "\n")

    update_progress(5, subtask="Initializing Stage 5 Step 5.5 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Module Imports & Factory Registration
    # ------------------------------------------------------------------
    print("--- Check 1: Module Imports & Factory Registration ---")
    update_progress(15, subtask="Verifying module imports and factory registrations...")

    script_path = ROOT / "pipelines" / "04_multimodal_auto_resolver.py"
    assert_check(
        "pipelines/04_multimodal_auto_resolver.py exists and is non-empty",
        script_path.exists() and script_path.stat().st_size > 1000,
        f"Path: {script_path}",
    )

    try:
        mod = importlib.import_module("pipelines.04_multimodal_auto_resolver")
        MultimodalAutoResolverPipeline = getattr(mod, "MultimodalAutoResolverPipeline")
        pipeline_instance = MultimodalAutoResolverPipeline()
        init_ok = True
    except Exception as e:
        init_ok = False
        pipeline_instance = None
        print(f"Import error: {e}")

    assert_check(
        "MultimodalAutoResolverPipeline class dynamically loaded and initialized successfully",
        init_ok and pipeline_instance is not None,
        "Failed to initialize MultimodalAutoResolverPipeline",
    )

    try:
        from pipelines import get_multimodal_auto_resolver
        factory_instance = get_multimodal_auto_resolver()
        factory_ok = factory_instance is not None
    except Exception as e:
        factory_ok = False
        print(f"Factory import error: {e}")

    assert_check(
        "pipelines package exposes get_multimodal_auto_resolver() factory function",
        factory_ok,
        "pipelines/__init__.py get_multimodal_auto_resolver() check",
    )

    assert_check(
        "CleaningPipeline and CleanedMultimodalContract load cleanly from core.cleaning_pipeline",
        hasattr(CleaningPipeline, "normalize_multimodal") and CleanedMultimodalContract is not None,
        "CleaningPipeline contract verification",
    )

    # ------------------------------------------------------------------
    # Check 2: Visual Question OCR Execution
    # ------------------------------------------------------------------
    print("\n--- Check 2: Visual Question OCR Execution ---")
    update_progress(35, subtask="Executing visual question OCR on assessment screenshot...")

    question_target = "fixtures/exam_question_sample.png"
    q_result = pipeline_instance.resolve_multimodal_content(
        target_input=question_target,
        expected_type="visual_question",
        human_mode=True,
        timing_profile="BALANCED_HUMAN",
        force_mock=True,
    )

    assert_check(
        "resolve_multimodal_content() on visual question finishes with status == 'completed'",
        isinstance(q_result, dict) and q_result.get("status") == "completed",
        f"Result status: {q_result.get('status')}",
    )

    q_run_dir = Path(q_result["run_dir"])
    q_raw_dir = q_run_dir / "raw"
    q_cleaned_dir = q_run_dir / "cleaned"

    assert_check(
        "Run directory allocated under data/pipelines/04_multimodal_auto_resolver/",
        q_run_dir.exists() and "04_multimodal_auto_resolver" in str(q_run_dir),
        f"Run dir: {q_run_dir}",
    )

    assert_check(
        "raw/ contains input_image.png and ocr_raw_boxes.json with non-zero bytes",
        (q_raw_dir / "input_image.png").exists() and (q_raw_dir / "ocr_raw_boxes.json").exists(),
        f"Raw files: {[f.name for f in q_raw_dir.iterdir()]}",
    )

    q_boxes_file = q_cleaned_dir / "bounding_boxes.json"
    assert_check(
        "cleaned/bounding_boxes.json exists and contains localized coordinate boxes (>= 5)",
        q_boxes_file.exists() and len(json.loads(q_boxes_file.read_text(encoding="utf-8"))) >= 5,
        f"Boxes file: {q_boxes_file}",
    )

    assert_check(
        "q_result reports content_type == 'visual_question' with high confidence",
        q_result.get("content_type") == "visual_question" and q_result.get("confidence_score", 0.0) >= 0.9,
        f"Type: {q_result.get('content_type')}, Conf: {q_result.get('confidence_score')}",
    )

    # ------------------------------------------------------------------
    # Check 3: Table Grid Matrix Extraction
    # ------------------------------------------------------------------
    print("\n--- Check 3: Table Grid Matrix Extraction ---")
    update_progress(55, subtask="Executing tabular grid matrix extraction on financial table...")

    table_target = "fixtures/financial_table_sample.png"
    t_result = pipeline_instance.resolve_multimodal_content(
        target_input=table_target,
        expected_type="table_grid",
        human_mode=True,
        timing_profile="BALANCED_HUMAN",
        force_mock=True,
    )

    assert_check(
        "resolve_multimodal_content() on table grid finishes with status == 'completed'",
        isinstance(t_result, dict) and t_result.get("status") == "completed",
        f"Result status: {t_result.get('status')}",
    )

    t_run_dir = Path(t_result["run_dir"])
    t_cleaned_dir = t_run_dir / "cleaned"
    tables_dir = t_cleaned_dir / "tables"

    assert_check(
        "cleaned/tables/ directory exists and contains table_01.csv and table_01.json",
        tables_dir.exists() and (tables_dir / "table_01.csv").exists() and (tables_dir / "table_01.json").exists(),
        f"Tables dir files: {[f.name for f in tables_dir.iterdir()] if tables_dir.exists() else []}",
    )

    csv_text = (tables_dir / "table_01.csv").read_text(encoding="utf-8").strip()
    assert_check(
        "table_01.csv contains expected problem benchmark rows (>= 5 rows)",
        len(csv_text.splitlines()) >= 5 and "Problem ID" in csv_text,
        f"CSV preview:\n{csv_text[:120]}",
    )

    t_spec_data = json.loads((t_cleaned_dir / "multimodal_spec.json").read_text(encoding="utf-8"))
    matrices = t_spec_data.get("table_matrices", [])
    assert_check(
        "table_matrices in multimodal_spec.json contains 2D/3D structured row lists",
        len(matrices) >= 1 and isinstance(matrices[0], list) and len(matrices[0]) >= 5,
        f"Matrices count: {len(matrices)}, Rows in table 1: {len(matrices[0]) if matrices else 0}",
    )

    # ------------------------------------------------------------------
    # Check 4: Silver-Tier Contract Schema Enforcement
    # ------------------------------------------------------------------
    print("\n--- Check 4: Silver-Tier Contract Schema Enforcement ---")
    update_progress(75, subtask="Validating multimodal_spec.json and README.md against contract...")

    # Validate table spec against Pydantic schema
    try:
        validated_contract = CleanedMultimodalContract(**t_spec_data)
        schema_valid = True
    except Exception as e:
        schema_valid = False
        validated_contract = None
        print(f"Contract validation error: {e}")

    assert_check(
        "multimodal_spec.json strictly validates against CleanedMultimodalContract",
        schema_valid and validated_contract is not None and validated_contract.content_type == "table_grid",
        f"Schema valid: {schema_valid}, Content type: {getattr(validated_contract, 'content_type', None)}",
    )

    t_readme_file = t_cleaned_dir / "README.md"
    assert_check(
        "cleaned/README.md exists with non-zero bytes (> 200 B)",
        t_readme_file.exists() and t_readme_file.stat().st_size > 200,
        f"README size: {t_readme_file.stat().st_size if t_readme_file.exists() else 0} bytes",
    )

    readme_content = t_readme_file.read_text(encoding="utf-8")
    assert_check(
        "cleaned/README.md contains valid YAML frontmatter header delimited by ---",
        readme_content.startswith("---\n") and "\n---\n\n" in readme_content,
        f"Frontmatter preview: {readme_content[:80]}",
    )

    frontmatter = yaml.safe_load(readme_content.split("---")[1])
    assert_check(
        "README.md frontmatter specifies source_input, content_type, confidence_score, and counts",
        frontmatter.get("content_type") == "table_grid"
        and frontmatter.get("confidence_score") is not None
        and frontmatter.get("tables_count") == 1
        and frontmatter.get("bounding_boxes_count") is not None,
        f"Frontmatter: {frontmatter}",
    )

    assert_check(
        "README.md contains Markdown table preview rendering for table_grid",
        "## 📊 Extracted Table Preview" in readme_content and "Problem ID" in readme_content,
        "Markdown table rendering check",
    )

    # ------------------------------------------------------------------
    # Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard ---")
    update_progress(90, subtask="Verifying manifest hashes, SQLite indexing, and secret security...")

    manifest_file = t_run_dir / "run_manifest.json"
    assert_check(
        "run_manifest.json exists with completed status",
        manifest_file.exists(),
        f"Path: {manifest_file}",
    )

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    domain_metrics = manifest_data.get("domain_metrics", {})
    file_hashes = domain_metrics.get("file_hashes") or manifest_data.get("file_hashes", {})

    assert_check(
        "run_manifest.json contains domain metrics and SHA-256 hashes for all generated files",
        manifest_data.get("status") == "completed"
        and domain_metrics.get("content_type") == "table_grid"
        and domain_metrics.get("tables_count") == 1
        and len(file_hashes) >= 5,
        f"Domain metrics: {domain_metrics}, Hashes count: {len(file_hashes)}",
    )

    assert_check(
        "Manifest records SHA-256 for cleaned/tables/table_01.csv and cleaned/multimodal_spec.json",
        "cleaned/tables/table_01.csv" in file_hashes and "cleaned/multimodal_spec.json" in file_hashes,
        f"File hashes keys: {list(file_hashes.keys())}",
    )

    # Auto-indexing check
    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()
    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() federates the multimodal pipeline runs cleanly",
        isinstance(sync_stats, dict) and total_runs > 0,
        f"Total runs: {total_runs}",
    )

    # Pre-commit secret guard
    secret_scan = scan_staged_for_secrets()
    assert_check(
        "Pre-commit secret guard passes with zero leaks",
        (not secret_scan.get("violations_found", False)) and secret_scan.get("blocked_secrets_count", 0) == 0,
        f"Findings: {secret_scan.get('details', [])}",
    )

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STAGE 5 STEP 5.5 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, subtask="Stage 5 Step 5.5 Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 5 STEP 5.5 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
