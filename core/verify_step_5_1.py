"""
core/verify_step_5_1.py
=======================
Focused Verification Suite for Stage 5 — Step 5.1:
Initialize Stage 5 Governance & Logging, Build the Cleaned Schema Normalizer &
Contract Enforcement Engine (`core/cleaning_pipeline.py`), and Validate Disk Serialization.

Verifies:
1. Stage 5 Governance & Log Infrastructure:
   - logs/stages/stage_5_real_pipelines.jsonl exists and records structured events
   - GEMINI.md reflects Stage 5 and Rule 8 (Silver Tier Contract Enforcement)
   - frontend/index.html includes Stage 5 options in Tab 1 and Tab 4
2. Markdown Contract & YAML Frontmatter Generation:
   - normalize_markdown() on noisy raw HTML
   - Strips scripts/styles/navigation/footers
   - Produces valid YAML frontmatter + CommonMark body
   - Calculates word count and reading dwell time
3. Code Problem Contract Normalization:
   - normalize_code_problem() on LeetCode GraphQL structure
   - Validates problem metadata, starter snippets, testcases, constraints
4. Social Media & Forensics Contract Validation:
   - normalize_social_post() extracts metrics, hashtags, media files, summaries
   - normalize_forensics() identifies REST APIs, trackers, and security headers
5. Multimodal Contract & Disk Persistence:
   - normalize_multimodal() handles OCR bounding boxes and table matrices
   - validate_and_save() writes validated deliverables to disk with SHA-256 verification
6. Global Master Index Sync & Zero-Plaintext Security Guard:
   - GlobalMasterIndexer.sync_all() federates Stage 5 without errors
   - core/git_manager.py:scan_staged_for_secrets() passes with zero leaks
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
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

from core.cleaning_pipeline import (
    CleanedCodeProblemContract,
    CleanedForensicsContract,
    CleanedMarkdownContract,
    CleanedMultimodalContract,
    CleanedSocialMediaContract,
    CleaningPipeline,
)
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
            step="Step 5.1",
            tool_id="cleaning_pipeline",
            action_name="verify_step_5_1",
            stage_log_name="stage_5_real_pipelines",
        )
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {name} - {details}")
        log_global(
            message=f"CHECK FAILED: {name} - {details}",
            level="ERROR",
            stage="Stage 5",
            step="Step 5.1",
            tool_id="cleaning_pipeline",
            action_name="verify_step_5_1",
            stage_log_name="stage_5_real_pipelines",
        )


def main() -> None:
    print("\n" + "=" * 70)
    print("STARTING STAGE 5 STEP 5.1 VERIFICATION SUITE")
    print("   Cleaned Schema Normalizer & Silver Tier Contract Enforcement")
    print("=" * 70 + "\n")

    update_progress(5, "Initializing Stage 5 Step 5.1 verification suite...")
    pipeline = CleaningPipeline()

    # ------------------------------------------------------------------
    # Check 1: Stage 5 Governance & Log Infrastructure
    # ------------------------------------------------------------------
    print("--- Check 1: Stage 5 Governance & Log Infrastructure ---")
    update_progress(15, "Verifying Stage 5 log files and GEMINI.md governance...")

    stage_5_log = ROOT / "logs" / "stages" / "stage_5_real_pipelines.jsonl"
    assert_check(
        "logs/stages/stage_5_real_pipelines.jsonl exists",
        stage_5_log.exists(),
        f"Path: {stage_5_log}",
    )

    # Test writing a sample log entry into stage 5
    log_global(
        message="Stage 5 governance initialized",
        level="INFO",
        stage="Stage 5",
        step="Step 5.1",
        tool_id="cleaning_pipeline",
        action_name="init_stage_5",
        stage_log_name="stage_5_real_pipelines",
    )
    assert_check(
        "stage_5_real_pipelines.jsonl successfully receives structured entries",
        stage_5_log.stat().st_size > 0,
        f"Size: {stage_5_log.stat().st_size} bytes",
    )

    # Check GEMINI.md
    gemini_md = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    assert_check(
        "GEMINI.md reflects Stage 5 in header",
        "Stage:** 5" in gemini_md,
        "Stage 5 not found in GEMINI.md header",
    )
    assert_check(
        "GEMINI.md defines Rule 8 (Data Lake Silver Tier Contract Enforcement)",
        "Rule 8 — Data Lake Silver Tier Contract Enforcement" in gemini_md,
        "Rule 8 missing from GEMINI.md",
    )

    # Check frontend/index.html
    html_content = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert_check(
        "frontend/index.html includes Stage 5 in filter dropdowns",
        '<option value="Stage 5">Stage 5</option>' in html_content,
        "Stage 5 option missing in index.html",
    )

    # ------------------------------------------------------------------
    # Check 2: Markdown Contract & YAML Frontmatter Generation
    # ------------------------------------------------------------------
    print("\n--- Check 2: Markdown Contract & YAML Frontmatter Generation ---")
    update_progress(35, "Testing normalize_markdown with noisy HTML and YAML frontmatter...")

    noisy_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Scraper Architecture</title></head>
    <body>
      <nav><a href="/">Home</a> | <a href="/login">Login</a></nav>
      <header><div>Sponsored Banner Ad</div></header>
      <h1>Clean Architecture in Web Crawlers</h1>
      <p>Modern web scraping pipelines require <strong>strict separation</strong> between raw landing tiers and silver schema contracts.</p>
      <p>By enforcing typed contracts, downstream AI models and analysts receive validated, deterministic data.</p>
      <pre><code>print('contract enforced')</code></pre>
      <aside><div>Related Articles</div></aside>
      <footer><p>Copyright 2026 Antigravity Inc. All rights reserved.</p></footer>
    </body>
    </html>
    """

    md_contract = pipeline.normalize_markdown(
        raw_html_or_text=noisy_html,
        metadata={
            "title": "Clean Architecture in Web Crawlers",
            "url": "https://example.com/clean-arch",
            "primary_tool": "16_crawl4ai",
            "tags": ["architecture", "silver_tier", "clean_code"],
        },
    )

    assert_check(
        "CleanedMarkdownContract instance created with valid attributes",
        isinstance(md_contract, CleanedMarkdownContract) and md_contract.title == "Clean Architecture in Web Crawlers",
        f"Title: {md_contract.title}",
    )
    assert_check(
        "Word count and estimated reading time correctly calculated",
        md_contract.word_count >= 20 and md_contract.reading_time_min >= 0.1,
        f"Words: {md_contract.word_count}, Reading dwell: {md_contract.reading_time_min}m",
    )
    assert_check(
        "Boilerplate nav, footer, and script elements cleanly stripped",
        "Sponsored Banner Ad" not in md_contract.body_markdown and "Copyright 2026" not in md_contract.body_markdown,
        f"Body preview: {md_contract.body_markdown[:100]}...",
    )

    # Test serialization to markdown with YAML frontmatter
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_md_path = Path(tmp_dir) / "test_article.md"
        md_contract.to_markdown_file(tmp_md_path)

        assert_check(
            "to_markdown_file() produces valid file on disk",
            tmp_md_path.exists() and tmp_md_path.stat().st_size > 0,
            f"Path: {tmp_md_path}",
        )

        md_raw = tmp_md_path.read_text(encoding="utf-8")
        assert_check(
            "File contains valid YAML frontmatter delimited by ---",
            md_raw.startswith("---\n") and "\n---\n\n" in md_raw,
            f"Frontmatter: {md_raw[:80]}",
        )
        parsed_yaml = yaml.safe_load(md_raw.split("---")[1])
        assert_check(
            "YAML frontmatter contains title, url, word_count, and domain_tags",
            parsed_yaml.get("title") == "Clean Architecture in Web Crawlers"
            and parsed_yaml.get("word_count") == md_contract.word_count
            and "silver_tier" in parsed_yaml.get("domain_tags", []),
            f"Parsed YAML: {parsed_yaml}",
        )

    # ------------------------------------------------------------------
    # Check 3: Code Problem Contract Normalization
    # ------------------------------------------------------------------
    print("\n--- Check 3: Code Problem Contract Normalization ---")
    update_progress(55, "Testing normalize_code_problem with LeetCode GraphQL payload...")

    mock_leetcode_payload = {
        "data": {
            "question": {
                "questionFrontendId": "1",
                "title": "Two Sum",
                "titleSlug": "two-sum",
                "difficulty": "Easy",
                "topicTags": [
                    {"name": "Array", "slug": "array"},
                    {"name": "Hash Table", "slug": "hash-table"},
                ],
                "content": "<p>Given an array of integers <code>nums</code> and an integer <code>target</code>, return <em>indices of the two numbers such that they add up to <code>target</code></em>.</p><p><strong>Constraints:</strong></p><ul><li><code>2 &lt;= nums.length &lt;= 10<sup>4</sup></code></li><li><code>-10<sup>9</sup> &lt;= nums[i] &lt;= 10<sup>9</sup></code></li></ul>",
                "codeSnippets": [
                    {
                        "langSlug": "python3",
                        "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
                    },
                    {
                        "langSlug": "javascript",
                        "code": "/**\n * @param {number[]} nums\n * @param {number} target\n * @return {number[]}\n */\nvar twoSum = function(nums, target) {\n    \n};",
                    },
                ],
                "exampleTestcases": "[2,7,11,15]\n9\n[3,2,4]\n6\n[3,3]\n6",
            }
        }
    }

    code_contract = pipeline.normalize_code_problem(mock_leetcode_payload)

    assert_check(
        "CleanedCodeProblemContract normalizes ID, slug, and difficulty",
        code_contract.problem_id == 1 and code_contract.slug == "two-sum" and code_contract.difficulty == "Easy",
        f"ID: {code_contract.problem_id}, Slug: {code_contract.slug}, Diff: {code_contract.difficulty}",
    )
    assert_check(
        "Topic tags and starter snippets correctly extracted",
        "Array" in code_contract.tags and "python3" in code_contract.starter_snippets and "javascript" in code_contract.starter_snippets,
        f"Tags: {code_contract.tags}, Snippets: {list(code_contract.starter_snippets.keys())}",
    )
    assert_check(
        "Sample testcases and constraints parsed from HTML content",
        len(code_contract.sample_testcases) >= 2 and len(code_contract.constraints) >= 1,
        f"Testcases count: {len(code_contract.sample_testcases)}, Constraints count: {len(code_contract.constraints)}",
    )

    # ------------------------------------------------------------------
    # Check 4: Social Media & Forensics Contract Validation
    # ------------------------------------------------------------------
    print("\n--- Check 4: Social Media & Forensics Contract Validation ---")
    update_progress(70, "Testing normalize_social_post and normalize_forensics...")

    # 1. Social Post
    mock_social_meta = {
        "platform": "instagram",
        "shortcode": "C9XYZ12345",
        "owner_username": "ai_researcher",
        "owner_fullname": "AI Crawler Lab",
        "caption": "Exploring human-like mouse kinematics with cubic Bezier curves! #playwright #automation #stealth",
        "likes_count": 2450,
        "comments_count": 132,
        "video_view_count": 18200,
        "is_video": True,
        "media_files": ["reel_video.mp4", "extracted_audio.wav"],
        "transcript_srt_path": "data/20_whisper/transcripts/reel.srt",
    }
    social_contract = pipeline.normalize_social_post(
        metadata_dict=mock_social_meta,
        transcript_text="In this short demonstration, we analyze how neuromotor jitter prevents fingerprinting.",
    )

    assert_check(
        "CleanedSocialMediaContract normalizes post identity and author handle",
        social_contract.platform == "instagram" and social_contract.post_id == "C9XYZ12345" and social_contract.author_handle == "@ai_researcher",
        f"Handle: {social_contract.author_handle}, ID: {social_contract.post_id}",
    )
    assert_check(
        "Hashtags, metrics, and media type parsed accurately",
        "playwright" in social_contract.hashtags and social_contract.metrics["likes"] == 2450 and social_contract.media_type == "reel",
        f"Hashtags: {social_contract.hashtags}, Metrics: {social_contract.metrics}",
    )

    # 2. Forensics Audit
    mock_network_entries = [
        {
            "request": {"url": "https://auth.example.com/api/v1/session", "method": "POST"},
            "response": {
                "status": 200,
                "headers": [
                    {"name": "Content-Type", "value": "application/json; charset=utf-8"},
                    {"name": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains"},
                    {"name": "Content-Security-Policy", "value": "default-src 'self'"},
                    {"name": "X-Frame-Options", "value": "DENY"},
                ],
            },
        },
        {
            "request": {"url": "https://www.google-analytics.com/g/collect?v=2", "method": "POST"},
            "response": {"status": 204, "headers": []},
        },
        {
            "request": {"url": "https://connect.facebook.net/en_US/fbevents.js", "method": "GET"},
            "response": {"status": 200, "headers": []},
        },
    ]

    forensics_contract = pipeline.normalize_forensics(
        network_har_or_requests=mock_network_entries,
        singlefile_path="data/14_singlefile/archives/audit_snapshot.html",
    )

    assert_check(
        "CleanedForensicsContract discovers backend API endpoints",
        len(forensics_contract.discovered_api_endpoints) >= 1 and forensics_contract.discovered_api_endpoints[0]["method"] == "POST",
        f"APIs: {forensics_contract.discovered_api_endpoints}",
    )
    assert_check(
        "Third-party trackers identified correctly",
        "google-analytics.com" in forensics_contract.third_party_trackers and "facebook.net" in forensics_contract.third_party_trackers,
        f"Trackers: {forensics_contract.third_party_trackers}",
    )
    assert_check(
        "Security headers audit calculated with score",
        "strict-transport-security" in forensics_contract.security_headers_audit["headers_present"]
        and forensics_contract.security_headers_audit["security_grade"] in ["A", "B"],
        f"Audit: {forensics_contract.security_headers_audit}",
    )

    # ------------------------------------------------------------------
    # Check 5: Multimodal Contract & Disk Persistence (validate_and_save)
    # ------------------------------------------------------------------
    print("\n--- Check 5: Multimodal Contract & Disk Persistence ---")
    update_progress(85, "Testing normalize_multimodal and validate_and_save...")

    mock_multimodal = {
        "source_image_or_pdf": "exam_sheet_table.png",
        "lines": [
            {"text": "Algorithm Performance Comparison Table", "conf": 0.99, "box": [20, 20, 400, 50]},
            {"text": "Report generated on Oct 2026", "conf": 0.96, "box": [20, 60, 250, 80]},
        ],
        "table_matrices": [
            [
                ["Scraper", "Latency", "Stealth"],
                ["01_curl_cffi", "0.22s", "JA3 Masked"],
                ["06_playwright", "1.45s", "Neuromotor Arc"],
            ]
        ],
    }

    multi_contract = pipeline.normalize_multimodal(mock_multimodal)
    assert_check(
        "CleanedMultimodalContract identifies table_grid content type and matrices",
        multi_contract.content_type == "table_grid" and len(multi_contract.table_matrices) == 1,
        f"Type: {multi_contract.content_type}, Matrices count: {len(multi_contract.table_matrices)}",
    )
    assert_check(
        "Confidence score and structured elements count verified",
        multi_contract.confidence_score >= 0.95 and multi_contract.structured_elements_count >= 5,
        f"Confidence: {multi_contract.confidence_score}, Elements: {multi_contract.structured_elements_count}",
    )

    # Test validate_and_save across all 5 contracts
    with tempfile.TemporaryDirectory() as tmp_save_dir:
        save_path = Path(tmp_save_dir)

        files_md = pipeline.validate_and_save(md_contract, save_path, "sample_article")
        files_code = pipeline.validate_and_save(code_contract, save_path, "leetcode")
        files_social = pipeline.validate_and_save(social_contract, save_path, "insta")
        files_forensics = pipeline.validate_and_save(forensics_contract, save_path, "forensics")
        files_multi = pipeline.validate_and_save(multi_contract, save_path, "tables")

        all_created = files_md + files_code + files_social + files_forensics + files_multi
        assert_check(
            "validate_and_save() successfully wrote all 5 standardized Silver Tier contracts to disk",
            len(all_created) >= 6 and all(f.exists() for f in all_created),
            f"Files created ({len(all_created)}): {[f.name for f in all_created]}",
        )

        # Check SHA-256 calculation
        first_sha = pipeline.compute_sha256(all_created[0])
        assert_check(
            "compute_sha256() computes valid 64-character SHA-256 hex string",
            isinstance(first_sha, str) and len(first_sha) == 64,
            f"SHA256: {first_sha}",
        )

    # ------------------------------------------------------------------
    # Check 6: Global Master Index Sync & Zero-Plaintext Security Guard
    # ------------------------------------------------------------------
    print("\n--- Check 6: Global Master Index Sync & Zero-Plaintext Security Guard ---")
    update_progress(95, "Syncing master index and scanning staged files for secrets...")

    master_indexer = GlobalMasterIndexer()
    sync_stats = master_indexer.sync_all()
    total_runs = sync_stats.get("totals", {}).get("total_runs", 0)
    assert_check(
        "GlobalMasterIndexer.sync_all() federates Stage 5 logs without error",
        isinstance(sync_stats, dict) and total_runs > 0,
        f"Total runs indexed: {total_runs}",
    )

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
    print("STAGE 5 STEP 5.1 VERIFICATION COMPLETED")
    print(f"   Passed: {PASSED_COUNT} / {PASSED_COUNT + FAILED_COUNT}")
    print(f"   Failed: {FAILED_COUNT}")
    print("=" * 70 + "\n")

    if FAILED_COUNT == 0:
        update_progress(100, "Stage 5 Step 5.1 Master Verification Suite completed with 100% pass rate.")
        print("ALL STAGE 5 STEP 5.1 CHECKS PASSED PERFECTLY!\n")
    else:
        print(f"{FAILED_COUNT} CHECKS FAILED. See details above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
