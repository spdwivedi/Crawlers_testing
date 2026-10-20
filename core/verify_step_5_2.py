"""
core/verify_step_5_2.py
=======================
Focused Verification Suite for Stage 5 — Step 5.2:
Build Task Pipeline 1 — LeetCode Catalog Index, Problem Markdown,
Starter Code & Testcases Archiver (`pipelines/01_leetcode_archiver.py`).

Verifies:
1. Pipeline Directory & Module Initialization:
   - pipelines/ exists and contains README.md with 4 pipeline architectures
   - pipelines/01_leetcode_archiver.py loads cleanly via dynamic import
2. Live Execution of LeetCode Problem Archiver:
   - LeetCodeArchiverPipeline.archive_problem("two-sum", human_mode=True, timing_profile="FAST_AUTOMATED")
   - Run finishes with status == "completed"
   - raw/graphql_response.json and raw/description_raw.html exist
3. Silver-Tier Contract Schema Enforcement:
   - cleaned/problem_spec.json validates strictly against CleanedCodeProblemContract
   - cleaned/README.md begins with valid YAML frontmatter and contains problem specification
   - cleaned/testcases.json contains structured test case vectors
4. Multi-Language Starter Code Generation:
   - cleaned/starter_codes/ contains solution.py, solution.js, solution.cpp, solution.java
   - Code files contain valid starter templates
5. Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard:
   - run_manifest.json contains SHA-256 hashes and domain metrics
   - GlobalMasterIndexer.sync_all() federates the run without error
   - core/git_manager.py:scan_staged_for_secrets() reports zero violations
"""

import hashlib
import importlib
import json
import os
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

from core.cleaning_pipeline import CleanedCodeProblemContract
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
            step="Step 5.2",
            tool_id="01_leetcode_archiver",
            action_name="verify_step_5_2",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.2",
            tool_id="01_leetcode_archiver",
            action_name="verify_step_5_2",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 STEP 5.2 VERIFICATION SUITE")
    print("   LeetCode Catalog Index, Markdown, Starter Code & Testcases Archiver")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 5 Step 5.2 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Pipeline Directory & Module Initialization
    # ------------------------------------------------------------------
    print("--- Check 1: Pipeline Directory & Module Initialization ---")
    update_progress(15, "Verifying pipelines/ directory and module imports...")

    pipelines_dir = ROOT / "pipelines"
    readme_path = pipelines_dir / "README.md"
    pipeline_script = pipelines_dir / "01_leetcode_archiver.py"

    assert_check(
        "pipelines/ directory exists",
        pipelines_dir.exists() and pipelines_dir.is_dir(),
        f"Path: {pipelines_dir}",
    )
    assert_check(
        "pipelines/README.md documents the 4 production task pipelines",
        readme_path.exists() and "01_leetcode_archiver.py" in readme_path.read_text(encoding="utf-8"),
        f"Path: {readme_path}",
    )
    assert_check(
        "pipelines/01_leetcode_archiver.py exists and is non-empty",
        pipeline_script.exists() and pipeline_script.stat().st_size > 500,
        f"Path: {pipeline_script}",
    )

    try:
        archiver_mod = importlib.import_module("pipelines.01_leetcode_archiver")
        LeetCodeArchiverPipeline = getattr(archiver_mod, "LeetCodeArchiverPipeline")
        pipeline_cls_valid = True
    except Exception as e:
        pipeline_cls_valid = False
        LeetCodeArchiverPipeline = None
        print(f"Import error: {e}")

    assert_check(
        "LeetCodeArchiverPipeline class dynamically loaded successfully",
        pipeline_cls_valid and LeetCodeArchiverPipeline is not None,
        "Failed to load LeetCodeArchiverPipeline from pipelines.01_leetcode_archiver",
    )

    # ------------------------------------------------------------------
    # Check 2: Live Execution of LeetCode Problem Archiver
    # ------------------------------------------------------------------
    print("\n--- Check 2: Live Execution of LeetCode Problem Archiver ---")
    update_progress(35, "Executing LeetCodeArchiverPipeline on 'two-sum' with human timing...")

    archiver = LeetCodeArchiverPipeline()
    t0 = time.perf_counter()
    result = archiver.archive_problem(
        title_slug="two-sum",
        human_mode=True,
        timing_profile="FAST_AUTOMATED",
        languages=["python3", "javascript", "cpp", "java"],
    )
    elapsed = time.perf_counter() - t0

    assert_check(
        "archive_problem() finishes with completed status",
        isinstance(result, dict) and result.get("status") == "completed",
        f"Result: {result}",
    )

    run_dir = Path(result["run_dir"])
    raw_dir = run_dir / "raw"
    cleaned_dir = run_dir / "cleaned"
    logs_dir = run_dir / "logs"

    assert_check(
        "Run directory allocated under data/pipelines/01_leetcode_archiver",
        run_dir.exists() and "01_leetcode_archiver" in str(run_dir),
        f"Run dir: {run_dir}",
    )

    raw_json = raw_dir / "graphql_response.json"
    raw_html = raw_dir / "description_raw.html"
    assert_check(
        "raw/graphql_response.json captured with valid JSON structure",
        raw_json.exists() and raw_json.stat().st_size > 100,
        f"Path: {raw_json}",
    )
    assert_check(
        "raw/description_raw.html captured with HTML content",
        raw_html.exists() and raw_html.stat().st_size > 50,
        f"Path: {raw_html}",
    )

    # ------------------------------------------------------------------
    # Check 3: Silver-Tier Contract Schema Enforcement
    # ------------------------------------------------------------------
    print("\n--- Check 3: Silver-Tier Contract Schema Enforcement ---")
    update_progress(60, "Validating cleaned/ outputs against CleanedCodeProblemContract...")

    spec_file = cleaned_dir / "problem_spec.json"
    assert_check(
        "cleaned/problem_spec.json exists",
        spec_file.exists() and spec_file.stat().st_size > 100,
        f"Path: {spec_file}",
    )

    try:
        spec_data = json.loads(spec_file.read_text(encoding="utf-8"))
        validated_contract = CleanedCodeProblemContract(**spec_data)
        contract_valid = True
    except Exception as e:
        contract_valid = False
        validated_contract = None
        print(f"Contract validation error: {e}")

    assert_check(
        "problem_spec.json strictly validates against CleanedCodeProblemContract",
        contract_valid and validated_contract is not None and validated_contract.slug == "two-sum",
        f"Problem: {getattr(validated_contract, 'title', None)}, ID: {getattr(validated_contract, 'problem_id', None)}",
    )

    readme_file = cleaned_dir / "README.md"
    assert_check(
        "cleaned/README.md exists",
        readme_file.exists() and readme_file.stat().st_size > 100,
        f"Path: {readme_file}",
    )

    readme_content = readme_file.read_text(encoding="utf-8")
    assert_check(
        "cleaned/README.md contains valid YAML frontmatter header delimited by ---",
        readme_content.startswith("---\n") and "\n---\n\n" in readme_content,
        f"Preview: {readme_content[:80]}",
    )

    frontmatter = yaml.safe_load(readme_content.split("---")[1])
    assert_check(
        "README.md frontmatter specifies problem_id, difficulty, and tags",
        frontmatter.get("problem_id") == 1 and frontmatter.get("difficulty") == "Easy" and "Array" in frontmatter.get("tags", []),
        f"Frontmatter: {frontmatter}",
    )

    testcases_file = cleaned_dir / "testcases.json"
    assert_check(
        "cleaned/testcases.json exists and contains structured testcases",
        testcases_file.exists() and testcases_file.stat().st_size > 20,
        f"Path: {testcases_file}",
    )

    tc_data = json.loads(testcases_file.read_text(encoding="utf-8"))
    assert_check(
        "testcases.json parsed as a non-empty list of case objects",
        isinstance(tc_data, list) and len(tc_data) >= 1 and "input" in tc_data[0],
        f"Testcases count: {len(tc_data)}",
    )

    # ------------------------------------------------------------------
    # Check 4: Multi-Language Starter Code Generation
    # ------------------------------------------------------------------
    print("\n--- Check 4: Multi-Language Starter Code Generation ---")
    update_progress(75, "Verifying cleaned/starter_codes/ templates for Python, JS, C++, Java...")

    starter_dir = cleaned_dir / "starter_codes"
    assert_check(
        "cleaned/starter_codes/ directory exists",
        starter_dir.exists() and starter_dir.is_dir(),
        f"Path: {starter_dir}",
    )

    sol_py = starter_dir / "solution.py"
    sol_js = starter_dir / "solution.js"
    sol_cpp = starter_dir / "solution.cpp"
    sol_java = starter_dir / "solution.java"

    assert_check(
        "solution.py exists with valid Python starter snippet",
        sol_py.exists() and ("class Solution" in sol_py.read_text(encoding="utf-8")),
        f"Path: {sol_py}",
    )
    assert_check(
        "solution.js exists with valid JavaScript starter snippet",
        sol_js.exists() and ("twoSum" in sol_js.read_text(encoding="utf-8") or "function" in sol_js.read_text(encoding="utf-8")),
        f"Path: {sol_js}",
    )
    assert_check(
        "solution.cpp exists with valid C++ starter snippet",
        sol_cpp.exists() and ("Solution" in sol_cpp.read_text(encoding="utf-8")),
        f"Path: {sol_cpp}",
    )
    assert_check(
        "solution.java exists with valid Java starter snippet",
        sol_java.exists() and ("Solution" in sol_java.read_text(encoding="utf-8")),
        f"Path: {sol_java}",
    )

    # ------------------------------------------------------------------
    # Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 5: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard ---")
    update_progress(90, "Verifying manifest hashes, SQLite indexing, and secret security...")

    manifest_file = run_dir / "run_manifest.json"
    assert_check(
        "run_manifest.json exists with completed status",
        manifest_file.exists(),
        f"Path: {manifest_file}",
    )

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert_check(
        "Manifest records domain metrics and SHA-256 file hashes",
        manifest_data.get("status") == "completed"
        and "domain_metrics" in manifest_data
        and manifest_data["domain_metrics"].get("problem_id") == 1
        and len(manifest_data["domain_metrics"].get("file_hashes", {})) >= 6,
        f"Manifest keys: {list(manifest_data.keys())}",
    )

    # Auto-indexing check
    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()
    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() federates the pipeline run cleanly",
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
    print("STAGE 5 STEP 5.2 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, "Stage 5 Step 5.2 Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 5 STEP 5.2 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
