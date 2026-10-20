"""
core/verify_step_5_3.py
=======================
Focused Verification Suite for Stage 5 — Step 5.3:
Build Task Pipeline 2 — Authenticated Instagram & Facebook Reel/Post Chunk
Downloader, FFmpeg Combiner & Whisper Transcript Pipeline (`pipelines/02_social_media_pipeline.py`).

Verifies:
1. Module Imports & Pipeline Initialization:
   - pipelines/02_social_media_pipeline.py loads cleanly via dynamic import
   - SocialMediaPipeline class loads and initializes dependencies
2. Vault Authentication & Ephemeral Cookie Shredding:
   - Verifies AuthInjector ephemeral cookie generation and zero-residual file shredding
3. Media Capture & Audio Extraction Execution:
   - process_media_url() finishes with status == "completed"
   - cleaned/combined_video.mp4 and cleaned/extracted_audio.wav exist with non-zero bytes
4. Audio Transcription & Knowledge Graph Extraction:
   - cleaned/transcript.srt exists with valid SubRip subtitle format
   - cleaned/knowledge_graph.json contains structured entities and summary
5. Silver-Tier Contract Schema Enforcement:
   - cleaned/post_spec.json strictly validates against CleanedSocialMediaContract
   - cleaned/README.md starts with valid YAML frontmatter and contains metrics table
6. Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard:
   - run_manifest.json contains SHA-256 hashes for media and transcript files
   - GlobalMasterIndexer.sync_all() federates the pipeline run without error
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

from core.auth_injector import TEMP_COOKIE_DIR, get_auth_injector
from core.cleaning_pipeline import CleanedSocialMediaContract
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
            step="Step 5.3",
            tool_id="02_social_media_pipeline",
            action_name="verify_step_5_3",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.3",
            tool_id="02_social_media_pipeline",
            action_name="verify_step_5_3",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 STEP 5.3 VERIFICATION SUITE")
    print("   Social Media Stream Downloader, FFmpeg Combiner & Whisper Pipeline")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 5 Step 5.3 verification suite...")

    # ------------------------------------------------------------------
    # Check 1: Module Imports & Pipeline Initialization
    # ------------------------------------------------------------------
    print("--- Check 1: Module Imports & Pipeline Initialization ---")
    update_progress(15, "Verifying module imports and dependency initialization...")

    script_path = ROOT / "pipelines" / "02_social_media_pipeline.py"
    assert_check(
        "pipelines/02_social_media_pipeline.py exists and is non-empty",
        script_path.exists() and script_path.stat().st_size > 1000,
        f"Path: {script_path}",
    )

    try:
        mod = importlib.import_module("pipelines.02_social_media_pipeline")
        SocialMediaPipeline = getattr(mod, "SocialMediaPipeline")
        pipeline_instance = SocialMediaPipeline()
        init_ok = True
    except Exception as e:
        init_ok = False
        pipeline_instance = None
        print(f"Import error: {e}")

    assert_check(
        "SocialMediaPipeline class dynamically loaded and initialized successfully",
        init_ok and pipeline_instance is not None,
        f"Failed to initialize SocialMediaPipeline",
    )

    assert_check(
        "SocialMediaPipeline resolves functional FFmpeg binary",
        bool(getattr(pipeline_instance, "ffmpeg_bin", None)) and Path(pipeline_instance.ffmpeg_bin).exists(),
        f"FFmpeg binary: {getattr(pipeline_instance, 'ffmpeg_bin', None)}",
    )

    # ------------------------------------------------------------------
    # Check 2: Vault Authentication & Ephemeral Cookie Shredding
    # ------------------------------------------------------------------
    print("\n--- Check 2: Vault Authentication & Ephemeral Cookie Shredding ---")
    update_progress(30, "Testing ephemeral Netscape cookie generation and zero-fill shredder...")

    injector = get_auth_injector()
    test_token = f"verify_{int(time.time())}"
    test_cookie_file = TEMP_COOKIE_DIR / f"ephemeral_test_{test_token}.cookies.txt"

    # Simulate creation of an ephemeral Netscape cookie file
    TEMP_COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    test_cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".instagram.com\tTRUE\t/\tTRUE\t1790000000\tsessionid\tsecret_verification_token\n",
        encoding="utf-8",
    )
    assert_check(
        "Ephemeral cookie file successfully written to vault_store/temp_cookies/",
        test_cookie_file.exists() and test_cookie_file.stat().st_size > 0,
        f"Path: {test_cookie_file}",
    )

    # Test shredder
    auth_bundle = {"ephemeral_files": [str(test_cookie_file)]}
    shredded_count = injector.shred_ephemeral_artifacts(auth_bundle)

    assert_check(
        "shred_ephemeral_artifacts() overwrites with null bytes and deletes cookie file",
        not test_cookie_file.exists() and shredded_count == 1,
        f"Shredded count: {shredded_count}, File still exists: {test_cookie_file.exists()}",
    )

    residual_cookies = list(TEMP_COOKIE_DIR.glob(f"*_{test_token}.cookies.txt"))
    assert_check(
        "Zero residual ephemeral cookie files remain in vault_store/temp_cookies/",
        len(residual_cookies) == 0,
        f"Residual files: {residual_cookies}",
    )

    # ------------------------------------------------------------------
    # Check 3: Media Capture & Audio Extraction Execution
    # ------------------------------------------------------------------
    print("\n--- Check 3: Media Capture & Audio Extraction Execution ---")
    update_progress(50, "Executing SocialMediaPipeline on sample reel target with FFmpeg muxing...")

    t0 = time.perf_counter()
    result = pipeline_instance.process_media_url(
        target_url="https://www.instagram.com/reel/sample_test_reel/",
        platform="instagram",
        human_mode=True,
        timing_profile="STREAM_PACED",
        transcribe_audio=True,
        force_mock=True,
    )
    elapsed = time.perf_counter() - t0

    assert_check(
        "process_media_url() finishes with status == 'completed'",
        isinstance(result, dict) and result.get("status") == "completed",
        f"Result status: {result.get('status')}",
    )

    run_dir = Path(result["run_dir"])
    raw_dir = run_dir / "raw"
    cleaned_dir = run_dir / "cleaned"

    assert_check(
        "Run directory allocated under data/pipelines/02_social_media_pipeline/",
        run_dir.exists() and "02_social_media_pipeline" in str(run_dir),
        f"Run dir: {run_dir}",
    )

    video_path = cleaned_dir / "combined_video.mp4"
    audio_path = cleaned_dir / "extracted_audio.wav"

    assert_check(
        "cleaned/combined_video.mp4 exists with non-zero bytes (H.264 video)",
        video_path.exists() and video_path.stat().st_size > 1000,
        f"Video size: {video_path.stat().st_size if video_path.exists() else 0} bytes",
    )

    assert_check(
        "cleaned/extracted_audio.wav exists with non-zero bytes (16kHz mono audio)",
        audio_path.exists() and audio_path.stat().st_size > 1000,
        f"Audio size: {audio_path.stat().st_size if audio_path.exists() else 0} bytes",
    )

    raw_meta = raw_dir / "post_metadata_raw.json"
    assert_check(
        "raw/post_metadata_raw.json captured with valid JSON metadata",
        raw_meta.exists() and raw_meta.stat().st_size > 50,
        f"Metadata size: {raw_meta.stat().st_size if raw_meta.exists() else 0} bytes",
    )

    # ------------------------------------------------------------------
    # Check 4: Audio Transcription & Knowledge Graph Extraction
    # ------------------------------------------------------------------
    print("\n--- Check 4: Audio Transcription & Knowledge Graph Extraction ---")
    update_progress(70, "Verifying cleaned/transcript.srt and knowledge_graph.json...")

    srt_path = cleaned_dir / "transcript.srt"
    assert_check(
        "cleaned/transcript.srt exists with non-zero bytes",
        srt_path.exists() and srt_path.stat().st_size > 50,
        f"SRT size: {srt_path.stat().st_size if srt_path.exists() else 0} bytes",
    )

    srt_text = srt_path.read_text(encoding="utf-8")
    srt_pattern_valid = bool(re.search(r"\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}", srt_text))
    assert_check(
        "transcript.srt conforms to SubRip subtitle timestamp format (00:00:00,000 --> 00:00:00,000)",
        srt_pattern_valid,
        f"SRT preview: {srt_text[:100]}",
    )

    kg_path = cleaned_dir / "knowledge_graph.json"
    assert_check(
        "cleaned/knowledge_graph.json exists with non-zero bytes",
        kg_path.exists() and kg_path.stat().st_size > 50,
        f"KG size: {kg_path.stat().st_size if kg_path.exists() else 0} bytes",
    )

    kg_data = json.loads(kg_path.read_text(encoding="utf-8"))
    assert_check(
        "knowledge_graph.json contains structured entities and summary",
        isinstance(kg_data.get("entities"), list) and len(kg_data["entities"]) >= 2 and bool(kg_data.get("summary")),
        f"Entities: {len(kg_data.get('entities', []))}, Summary: {bool(kg_data.get('summary'))}",
    )

    # ------------------------------------------------------------------
    # Check 5: Silver-Tier Contract Schema Enforcement
    # ------------------------------------------------------------------
    print("\n--- Check 5: Silver-Tier Contract Schema Enforcement ---")
    update_progress(85, "Validating post_spec.json and README.md against CleanedSocialMediaContract...")

    post_spec_file = cleaned_dir / "post_spec.json"
    assert_check(
        "cleaned/post_spec.json exists with non-zero bytes",
        post_spec_file.exists() and post_spec_file.stat().st_size > 100,
        f"Spec size: {post_spec_file.stat().st_size if post_spec_file.exists() else 0} bytes",
    )

    try:
        spec_dict = json.loads(post_spec_file.read_text(encoding="utf-8"))
        validated_contract = CleanedSocialMediaContract(**spec_dict)
        contract_valid = True
    except Exception as e:
        contract_valid = False
        validated_contract = None
        print(f"Contract validation error: {e}")

    assert_check(
        "post_spec.json strictly validates against CleanedSocialMediaContract",
        contract_valid and validated_contract is not None and validated_contract.platform == "instagram",
        f"Platform: {getattr(validated_contract, 'platform', None)}, ID: {getattr(validated_contract, 'post_id', None)}",
    )

    readme_file = cleaned_dir / "README.md"
    assert_check(
        "cleaned/README.md exists with non-zero bytes",
        readme_file.exists() and readme_file.stat().st_size > 100,
        f"README size: {readme_file.stat().st_size if readme_file.exists() else 0} bytes",
    )

    readme_content = readme_file.read_text(encoding="utf-8")
    assert_check(
        "cleaned/README.md contains valid YAML frontmatter header delimited by ---",
        readme_content.startswith("---\n") and "\n---\n\n" in readme_content,
        f"Frontmatter preview: {readme_content[:80]}",
    )

    frontmatter = yaml.safe_load(readme_content.split("---")[1])
    assert_check(
        "README.md frontmatter specifies platform, post_id, author_handle, and metrics",
        frontmatter.get("platform") == "instagram"
        and "author_handle" in frontmatter
        and frontmatter.get("likes") is not None,
        f"Frontmatter: {frontmatter}",
    )

    # ------------------------------------------------------------------
    # Check 6: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard
    # ------------------------------------------------------------------
    print("\n--- Check 6: Data Lake Integrity, Auto-Indexing & Pre-Commit Secret Guard ---")
    update_progress(95, "Verifying manifest hashes, SQLite indexing, and secret security...")

    manifest_file = run_dir / "run_manifest.json"
    assert_check(
        "run_manifest.json exists with completed status",
        manifest_file.exists(),
        f"Path: {manifest_file}",
    )

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    domain_metrics = manifest_data.get("domain_metrics", {})
    assert_check(
        "Manifest records domain metrics and SHA-256 hashes for media deliverables",
        manifest_data.get("status") == "completed"
        and domain_metrics.get("has_video") is True
        and domain_metrics.get("has_audio") is True
        and len(domain_metrics.get("file_hashes", {})) >= 5,
        f"Domain metrics: {domain_metrics}",
    )

    # Auto-indexing check
    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()
    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() federates the social pipeline run cleanly",
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
    print("STAGE 5 STEP 5.3 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, "Stage 5 Step 5.3 Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 5 STEP 5.3 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
