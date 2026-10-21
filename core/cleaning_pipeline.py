"""
core/cleaning_pipeline.py
=========================
Standardized Cleaned Schema Normalizer & Silver Tier Contract Engine — Rule 8.

Enforces strict data lake Silver Tier schemas for all transformed deliverables saved
into `cleaned/` directories across the workspace.

Contract Schemas (Pydantic V2):
  1. CleanedMarkdownContract     — CommonMark with structured YAML frontmatter
  2. CleanedCodeProblemContract  — Structured problem definitions, snippets, constraints
  3. CleanedSocialMediaContract  — Social posts/reels, metrics, media paths, SRT transcripts
  4. CleanedForensicsContract    — Network security audit, API endpoints, tracker analysis
  5. CleanedMultimodalContract   — OCR layout, bounding boxes, table matrices, document trees

Pipeline Engine:
  - CleaningPipeline: Standardizes, normalizes, validates, and serializes raw artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Union

import yaml
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# 1. STANDARDIZED SILVER-TIER CONTRACT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class CleanedMarkdownContract(BaseModel):
    """
    Standardized Silver Tier schema for article extracts, harvested documentation,
    and LLM-optimized content deliverables.
    """
    title: str = Field(default="Untitled Document", description="Document title extracted or provided")
    url: str = Field(default="", description="Origin URL of the content")
    scraped_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of scraping/cleaning",
    )
    word_count: int = Field(default=0, ge=0, description="Total word count in cleaned Markdown body")
    reading_time_min: float = Field(default=0.0, ge=0.0, description="Estimated reading dwell time in minutes (200 wpm)")
    primary_tool: str = Field(default="generic_cleaner", description="Tool ID responsible for acquisition")
    domain_tags: list[str] = Field(default_factory=list, description="Categorization and topic tags")
    body_markdown: str = Field(default="", description="Sanitized CommonMark text body")

    def to_markdown_file(self, path: Path | str) -> Path:
        """Write valid YAML frontmatter + CommonMark body to target file path."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "title": self.title,
            "url": self.url,
            "scraped_at": self.scraped_at,
            "word_count": self.word_count,
            "reading_time_min": round(self.reading_time_min, 1),
            "primary_tool": self.primary_tool,
            "domain_tags": self.domain_tags,
        }
        yaml_header = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False).strip()
        full_content = f"---\n{yaml_header}\n---\n\n{self.body_markdown.strip()}\n"
        p.write_text(full_content, encoding="utf-8")
        return p

    def to_json_file(self, path: Path | str) -> Path:
        """Write schema JSON export."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return p


class CleanedCodeProblemContract(BaseModel):
    """
    Standardized Silver Tier schema for programming problem catalogs (LeetCode, HackerRank, etc.).
    """
    problem_id: int = Field(..., description="Numerical problem ID")
    title: str = Field(..., description="Problem display title")
    slug: str = Field(..., description="URL slug / problem identifier")
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(..., description="Algorithmic difficulty classification")
    tags: list[str] = Field(default_factory=list, description="Topic and algorithm tags")
    description_markdown: str = Field(default="", description="Full problem specification in clean Markdown")
    starter_snippets: dict[str, str] = Field(
        default_factory=dict,
        description="Language starter templates (e.g. {'python3': '...', 'javascript': '...'})",
    )
    sample_testcases: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parsed sample inputs and outputs",
    )
    constraints: list[str] = Field(default_factory=list, description="Mathematical and algorithmic constraints")
    scraped_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )

    def to_json_file(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return p

    def to_markdown_file(self, path: Path | str) -> Path:
        """Export problem catalog card as clean Markdown."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        snippets_md = "\n\n".join([f"### {lang}\n```{lang}\n{code}\n```" for lang, code in self.starter_snippets.items()])
        constraints_md = "\n".join([f"- `{c}`" for c in self.constraints])
        content = (
            f"# {self.problem_id}. {self.title} ({self.difficulty})\n\n"
            f"**Tags:** {', '.join(self.tags)}\n\n"
            f"## Problem Statement\n\n{self.description_markdown}\n\n"
            f"## Constraints\n\n{constraints_md}\n\n"
            f"## Code Templates\n\n{snippets_md}\n"
        )
        p.write_text(content, encoding="utf-8")
        return p


class CleanedSocialMediaContract(BaseModel):
    """
    Standardized Silver Tier schema for social posts, reels, video streams, and media metadata.
    """
    platform: str = Field(..., description="Origin platform (instagram, facebook, twitter, tiktok)")
    post_id: str = Field(..., description="Unique post ID or shortcode")
    post_url: str = Field(default="", description="Direct URL to the post")
    author_handle: str = Field(default="", description="Creator handle e.g. @username")
    author_name: str = Field(default="", description="Display name of the author")
    caption_text: str = Field(default="", description="Full raw caption text")
    hashtags: list[str] = Field(default_factory=list, description="Extracted hashtags without # symbol")
    published_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Publication timestamp",
    )
    metrics: dict[str, int] = Field(
        default_factory=lambda: {"likes": 0, "comments": 0, "views": 0},
        description="Engagement statistics",
    )
    media_type: Literal["reel", "post", "carousel"] = Field(
        default="post",
        description="Classified media asset type",
    )
    media_files: list[str] = Field(
        default_factory=list,
        description="Associated media file names/paths (video mp4, audio wav, etc.)",
    )
    transcript_srt_path: str | None = Field(default=None, description="Path to accompanying SRT transcript file")
    summary_text: str = Field(default="", description="Concise synopsis of post caption or audio transcript")

    def to_json_file(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return p


class CleanedForensicsContract(BaseModel):
    """
    Standardized Silver Tier schema for deep website security audits, HAR traces, and DOM snapshots.
    """
    target_url: str = Field(..., description="Target URL tested")
    final_url: str = Field(default="", description="Final URL after HTTP redirects")
    status_code: int = Field(default=200, description="Final HTTP status code")
    page_title: str = Field(default="", description="Extracted HTML page title")
    captured_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Capture timestamp",
    )
    singlefile_archive_path: str = Field(default="", description="Relative or absolute path to self-contained HTML archive")
    discovered_api_endpoints: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Discovered backend API endpoints from traffic audit",
    )
    third_party_trackers: list[str] = Field(
        default_factory=list,
        description="Identified tracking and analytics domains",
    )
    security_headers_audit: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit of security headers (CSP, HSTS, X-Frame-Options, etc.)",
    )
    total_assets_inlined: int = Field(default=0, ge=0, description="Total CSS/image/font assets inlined")

    def to_json_file(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return p


class CleanedMultimodalContract(BaseModel):
    """
    Standardized Silver Tier schema for OCR extracts, table grids, bounding boxes, and document trees.
    """
    source_image_or_pdf: str = Field(..., description="Source image or PDF file name")
    content_type: Literal["visual_question", "table_grid", "document_tree"] = Field(
        ...,
        description="Primary nature of the multimodal artifact",
    )
    extracted_text: str = Field(default="", description="Concatenated raw or formatted OCR text")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Average OCR detection confidence")
    table_matrices: list[list[list[str]]] = Field(
        default_factory=list,
        description="Detected table grids as 3D matrices (tables -> rows -> cells)",
    )
    bounding_boxes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Coordinates of detected text lines or cells: [{'box': [x0,y0,x1,y1], 'text': str, 'conf': float}]",
    )
    structured_elements_count: int = Field(default=0, ge=0, description="Total recognized blocks/cells/nodes")

    def to_json_file(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return p


AnyContract = Union[
    CleanedMarkdownContract,
    CleanedCodeProblemContract,
    CleanedSocialMediaContract,
    CleanedForensicsContract,
    CleanedMultimodalContract,
]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CLEANING PIPELINE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CleaningPipeline:
    """
    Universal normalizer and contract enforcement engine for the Silver Tier data lake.
    """

    KNOWN_TRACKER_DOMAINS = [
        "google-analytics.com",
        "googletagmanager.com",
        "doubleclick.net",
        "facebook.net",
        "connect.facebook.net",
        "fbevents.js",
        "hotjar.com",
        "segment.io",
        "mixpanel.com",
        "sentry.io",
        "datadoghq.com",
        "clarity.ms",
        "criteo.com",
        "taboola.com",
        "outbrain.com",
    ]

    SECURITY_HEADERS = [
        "content-security-policy",
        "strict-transport-security",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
    ]

    # ── Markdown & Content Normalization ──────────────────────────────────────

    def normalize_markdown(
        self,
        raw_html_or_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> CleanedMarkdownContract:
        """
        Strips noise, boilerplates, script remnants, and normalizes into CleanedMarkdownContract
        with calculated word count, estimated reading dwell time, and YAML frontmatter.
        """
        metadata = metadata or {}
        text = raw_html_or_text or ""

        # 1. Detect if input contains HTML markup
        if re.search(r"<(?:html|body|div|p|span|script|style|nav|footer)[^>]*>", text, re.IGNORECASE):
            text = self._strip_html_boilerplate(text)

        # 2. Clean CommonMark headers and spacing
        # Ensure single space after header hashes (#Header -> # Header)
        text = re.sub(r"^(#{1,6})([^\s#])", r"\1 \2", text, flags=re.MULTILINE)

        # Remove redundant horizontal rules and excessive blank lines (3+ -> 2)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        # 3. Calculate metrics
        words = re.findall(r"\b[\w'-]+\b", text)
        word_count = len(words)
        reading_time_min = round(max(0.1, word_count / 200.0), 1) if word_count > 0 else 0.0

        # Extract title from metadata or first H1 header
        title = metadata.get("title")
        if not title:
            h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            else:
                title = "Untitled Document"

        # Domain tags
        tags = metadata.get("tags") or metadata.get("domain_tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        return CleanedMarkdownContract(
            title=title,
            url=metadata.get("url", ""),
            scraped_at=metadata.get("scraped_at") or datetime.now(timezone.utc).isoformat(),
            word_count=word_count,
            reading_time_min=reading_time_min,
            primary_tool=metadata.get("primary_tool", metadata.get("tool_id", "generic_cleaner")),
            domain_tags=tags,
            body_markdown=text,
        )

    def _strip_html_boilerplate(self, html: str) -> str:
        """Strip non-content elements and boilerplate navigation from raw HTML."""
        # Strip script, style, noscript, svg, iframe
        cleaned = re.sub(r"<(script|style|noscript|svg|iframe)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Strip nav, footer, header, aside elements
        cleaned = re.sub(r"<(nav|footer|header|aside)[^>]*>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Transform common HTML elements to Markdown
        # Headings
        for i in range(6, 0, -1):
            cleaned = re.sub(
                rf"<h{i}[^>]*>(.*?)</h{i}>",
                rf"\n\n{'#' * i} \1\n\n",
                cleaned,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # Paragraphs & linebreaks
        cleaned = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\n\1\n\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<br\s*/?>", r"\n", cleaned, flags=re.IGNORECASE)

        # Bold & Italic
        cleaned = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Links
        cleaned = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r"[\2](\1)", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Code blocks and inline code
        cleaned = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"\n\n```\n\1\n```\n\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # List items
        cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Strip all remaining tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # Unescape HTML entities
        cleaned = (
            cleaned.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )

        return cleaned

    # ── Code Problem Normalization ───────────────────────────────────────────

    def normalize_code_problem(self, raw_graphql_json: dict[str, Any]) -> CleanedCodeProblemContract:
        """
        Normalizes raw LeetCode or algorithmic problem GraphQL payloads into CleanedCodeProblemContract.
        """
        # Unwrap question node if nested
        data = raw_graphql_json.get("data", raw_graphql_json)
        q = data.get("question", data)

        # 1. ID & Names
        problem_id_raw = q.get("questionFrontendId") or q.get("questionId") or q.get("problem_id", 0)
        try:
            problem_id = int(problem_id_raw)
        except (ValueError, TypeError):
            problem_id = 0

        title = q.get("title") or q.get("questionTitle") or "Unknown Problem"
        slug = q.get("titleSlug") or q.get("slug") or re.sub(r"[^\w\s-]", "", title).strip().lower().replace(" ", "-")

        # 2. Difficulty
        diff_raw = str(q.get("difficulty", "Medium")).strip().capitalize()
        difficulty: Literal["Easy", "Medium", "Hard"]
        if diff_raw in ["Easy", "Medium", "Hard"]:
            difficulty = diff_raw  # type: ignore
        else:
            difficulty = "Medium"

        # 3. Tags
        raw_tags = q.get("topicTags") or q.get("tags") or []
        tags: list[str] = []
        for t in raw_tags:
            if isinstance(t, dict):
                name = t.get("name") or t.get("slug", "")
                if name:
                    tags.append(name)
            elif isinstance(t, str):
                tags.append(t)

        # 4. Description & Constraints
        raw_content = q.get("content") or q.get("description_markdown") or ""
        desc_md = self._strip_html_boilerplate(raw_content).strip()

        # Extract constraints if present
        constraints: list[str] = []
        if "Constraints:" in desc_md or "constraints:" in desc_md.lower():
            parts = re.split(r"(?:Constraints:|\*\*Constraints:\*\*)", desc_md, flags=re.IGNORECASE)
            if len(parts) > 1:
                const_block = parts[1]
                for line in const_block.splitlines():
                    line_s = line.strip().lstrip("-*•").strip()
                    if line_s and len(line_s) > 2:
                        constraints.append(line_s)

        if not constraints and q.get("constraints"):
            raw_c = q["constraints"]
            constraints = raw_c if isinstance(raw_c, list) else [str(raw_c)]

        # 5. Starter Snippets
        snippets: dict[str, str] = {}
        raw_snippets = q.get("codeSnippets") or q.get("starter_snippets") or []
        if isinstance(raw_snippets, list):
            for snip in raw_snippets:
                if isinstance(snip, dict):
                    lang = snip.get("langSlug") or snip.get("lang", "")
                    code = snip.get("code", "")
                    if lang and code:
                        snippets[lang] = code
        elif isinstance(raw_snippets, dict):
            snippets = {str(k): str(v) for k, v in raw_snippets.items()}

        # 6. Sample Testcases
        testcases: list[dict[str, Any]] = []
        raw_examples = q.get("exampleTestcases") or q.get("sampleTestCase") or q.get("sample_testcases")
        if isinstance(raw_examples, list):
            for ex in raw_examples:
                if isinstance(ex, dict):
                    testcases.append(ex)
                elif isinstance(ex, str):
                    testcases.append({"input": ex})
        elif isinstance(raw_examples, str) and raw_examples.strip():
            # Lines separated by newlines
            lines = [l.strip() for l in raw_examples.strip().splitlines() if l.strip()]
            for idx, line in enumerate(lines):
                testcases.append({"case_index": idx + 1, "input": line})

        return CleanedCodeProblemContract(
            problem_id=problem_id,
            title=title,
            slug=slug,
            difficulty=difficulty,
            tags=tags,
            description_markdown=desc_md,
            starter_snippets=snippets,
            sample_testcases=testcases,
            constraints=constraints,
            scraped_at=q.get("scraped_at") or datetime.now(timezone.utc).isoformat(),
        )

    # ── Social Media & Stream Normalization ──────────────────────────────────

    def normalize_social_post(
        self,
        metadata_dict: dict[str, Any],
        transcript_text: str = "",
    ) -> CleanedSocialMediaContract:
        """
        Normalizes Instagram/Facebook/media metadata and optional audio transcript
        into CleanedSocialMediaContract.
        """
        m = metadata_dict or {}

        platform = str(m.get("platform", "instagram")).lower()
        post_id = str(m.get("post_id") or m.get("shortcode") or m.get("id", "post_001"))
        post_url = m.get("post_url") or m.get("url") or f"https://{platform}.com/p/{post_id}"

        # Author handle & name
        handle = m.get("author_handle") or m.get("owner_username") or m.get("uploader", "")
        if handle and not handle.startswith("@"):
            handle = f"@{handle}"
        name = m.get("author_name") or m.get("owner_fullname") or handle.lstrip("@")

        # Caption & hashtags
        caption = m.get("caption_text") or m.get("caption") or m.get("description", "")
        hashtags: list[str] = m.get("hashtags") or []
        if not hashtags and caption:
            # Extract hashtags via regex
            raw_tags = re.findall(r"#(\w+)", caption)
            hashtags = list(dict.fromkeys(raw_tags))

        # Metrics
        raw_metrics = m.get("metrics") or {}
        likes = raw_metrics.get("likes") or m.get("likes_count") or m.get("edge_media_preview_like", {}).get("count", 0)
        comments = raw_metrics.get("comments") or m.get("comments_count") or m.get("edge_media_to_comment", {}).get("count", 0)
        views = raw_metrics.get("views") or m.get("video_view_count") or m.get("view_count", 0)

        # Media Type
        m_type_raw = str(m.get("media_type") or ("reel" if m.get("is_video") else "post")).lower()
        media_type: Literal["reel", "post", "carousel"]
        if m_type_raw in ["reel", "post", "carousel"]:
            media_type = m_type_raw  # type: ignore
        else:
            media_type = "post"

        # Media Files
        files = m.get("media_files") or []
        if isinstance(files, str):
            files = [files]

        # Transcript & Summary
        srt_path = m.get("transcript_srt_path") or m.get("srt_path")
        summary = m.get("summary_text") or ""
        if not summary:
            if transcript_text:
                summary = transcript_text.strip()[:240] + ("..." if len(transcript_text) > 240 else "")
            elif caption:
                summary = caption.strip()[:200] + ("..." if len(caption) > 200 else "")

        return CleanedSocialMediaContract(
            platform=platform,
            post_id=post_id,
            post_url=post_url,
            author_handle=handle,
            author_name=name,
            caption_text=caption,
            hashtags=hashtags,
            published_at=m.get("published_at") or datetime.now(timezone.utc).isoformat(),
            metrics={"likes": int(likes), "comments": int(comments), "views": int(views)},
            media_type=media_type,
            media_files=files,
            transcript_srt_path=srt_path,
            summary_text=summary,
        )

    # ── Forensics & Network Snapshot Normalization ───────────────────────────

    def normalize_forensics(
        self,
        network_har_or_requests: list[dict[str, Any]] | dict[str, Any],
        singlefile_path: str = "",
    ) -> CleanedForensicsContract:
        """
        Parses network traces, extracts API endpoints, identifies trackers, and builds
        a security header audit into CleanedForensicsContract.
        """
        # Normalize into list of entries
        entries: list[dict[str, Any]] = []
        meta_info: dict[str, Any] = {}

        if isinstance(network_har_or_requests, dict):
            # Check for HAR structure: {"log": {"entries": [...]}}
            if "log" in network_har_or_requests and "entries" in network_har_or_requests["log"]:
                entries = network_har_or_requests["log"]["entries"]
            elif "entries" in network_har_or_requests:
                entries = network_har_or_requests["entries"]
            else:
                meta_info = network_har_or_requests
                entries = network_har_or_requests.get("requests", [])
        elif isinstance(network_har_or_requests, list):
            entries = network_har_or_requests

        target_url = meta_info.get("target_url", "")
        final_url = meta_info.get("final_url", target_url)
        status_code = meta_info.get("status_code", 200)
        page_title = meta_info.get("page_title", "")

        api_endpoints: list[dict[str, Any]] = []
        trackers_detected: set[str] = set()
        collected_headers: dict[str, str] = {}
        assets_inlined = meta_info.get("total_assets_inlined", 0)

        for entry in entries:
            req = entry.get("request", entry)
            resp = entry.get("response", {})
            url = req.get("url", "")
            method = req.get("method", "GET")
            status = resp.get("status") or entry.get("status", 200)

            if not target_url and url:
                target_url = url
                final_url = url

            # Detect content-type
            content_type = ""
            for h in resp.get("headers", []):
                h_name = h.get("name", "").lower()
                h_val = h.get("value", "")
                if h_name == "content-type":
                    content_type = h_val.lower()
                if h_name in self.SECURITY_HEADERS:
                    collected_headers[h_name] = h_val

            # Detect Trackers
            for tracker_domain in self.KNOWN_TRACKER_DOMAINS:
                if tracker_domain in url:
                    trackers_detected.add(tracker_domain)

            # Detect API endpoints (REST/JSON/GraphQL)
            is_api = (
                "application/json" in content_type
                or "api/" in url
                or "/v1/" in url
                or "/v2/" in url
                or "graphql" in url
            )
            if is_api and not any(t in url for t in trackers_detected):
                api_endpoints.append({
                    "url": url,
                    "method": method,
                    "status": status,
                    "content_type": content_type or "application/json",
                })

        # Build Security Header Audit
        header_audit: dict[str, Any] = {
            "audited_headers_count": len(self.SECURITY_HEADERS),
            "present_headers_count": len(collected_headers),
            "headers_present": collected_headers,
            "missing_headers": [h for h in self.SECURITY_HEADERS if h not in collected_headers],
            "security_grade": "A" if len(collected_headers) >= 5 else "B" if len(collected_headers) >= 3 else "C" if len(collected_headers) >= 1 else "F",
        }

        return CleanedForensicsContract(
            target_url=target_url or "https://example.com",
            final_url=final_url or target_url or "https://example.com",
            status_code=int(status_code),
            page_title=page_title or "Security Forensics Audit Snapshot",
            captured_at=datetime.now(timezone.utc).isoformat(),
            singlefile_archive_path=singlefile_path,
            discovered_api_endpoints=api_endpoints[:50],  # Bound to top 50
            third_party_trackers=sorted(list(trackers_detected)),
            security_headers_audit=header_audit,
            total_assets_inlined=assets_inlined,
        )

    # ── Multimodal, OCR & Layout Normalization ───────────────────────────────

    def normalize_multimodal(
        self,
        ocr_result_or_boxes: dict[str, Any],
    ) -> CleanedMultimodalContract:
        """
        Normalizes Surya OCR, PaddleOCR, table grids, or document trees into CleanedMultimodalContract.
        """
        raw = ocr_result_or_boxes or {}

        source = raw.get("source_image_or_pdf") or raw.get("filename") or "sample_document.png"

        # Determine content_type
        if raw.get("content_type") in ("visual_question", "table_grid", "document_tree"):
            content_type: Literal["visual_question", "table_grid", "document_tree"] = raw["content_type"]
        elif raw.get("table_matrices") or raw.get("tables"):
            content_type = "table_grid"
        elif raw.get("document_tree") or raw.get("hierarchy"):
            content_type = "document_tree"
        else:
            content_type = "visual_question"

        # Bounding boxes & lines
        boxes: list[dict[str, Any]] = []
        raw_boxes = raw.get("bounding_boxes") or raw.get("lines") or raw.get("elements") or []
        total_conf = 0.0
        extracted_lines: list[str] = []

        for b in raw_boxes:
            if isinstance(b, dict):
                text_val = b.get("text") or b.get("line_text") or ""
                conf_val = float(b.get("conf") or b.get("confidence") or 1.0)
                box_coords = b.get("box") or b.get("bbox") or []
                boxes.append({"text": text_val, "conf": conf_val, "box": box_coords})
                total_conf += conf_val
                if text_val:
                    extracted_lines.append(text_val)
            elif isinstance(b, str):
                extracted_lines.append(b)
                boxes.append({"text": b, "conf": 1.0, "box": []})
                total_conf += 1.0

        avg_conf = round(total_conf / len(boxes), 4) if boxes else 1.0

        # Full text
        extracted_text = raw.get("extracted_text") or "\n".join(extracted_lines)

        # Table Matrices
        table_matrices: list[list[list[str]]] = []
        raw_tables = raw.get("table_matrices") or raw.get("tables") or []
        if isinstance(raw_tables, list):
            for t in raw_tables:
                if isinstance(t, list):
                    # Table is list of rows
                    norm_table: list[list[str]] = []
                    for row in t:
                        if isinstance(row, list):
                            norm_table.append([str(c) for c in row])
                    if norm_table:
                        table_matrices.append(norm_table)

        elements_count = len(boxes) + sum(len(row) for t in table_matrices for row in t)

        return CleanedMultimodalContract(
            source_image_or_pdf=source,
            content_type=content_type,
            extracted_text=extracted_text,
            confidence_score=avg_conf,
            table_matrices=table_matrices,
            bounding_boxes=boxes,
            structured_elements_count=elements_count,
        )

    # ── Universal Validation & Disk Persistence ──────────────────────────────

    def validate_and_save(
        self,
        contract_instance: AnyContract,
        destination_dir: Path | str,
        filename_prefix: str = "",
    ) -> list[Path]:
        """
        Validates contract schema, writes clean output files to destination_dir,
        computes SHA-256 hashes, and returns list of created Paths.
        """
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)
        created_files: list[Path] = []

        prefix = filename_prefix.strip("_") if filename_prefix else "cleaned"

        if isinstance(contract_instance, CleanedMarkdownContract):
            md_path = dest / f"{prefix}.md"
            contract_instance.to_markdown_file(md_path)
            created_files.append(md_path)

        elif isinstance(contract_instance, CleanedCodeProblemContract):
            json_path = dest / f"{prefix}_{contract_instance.slug}.json"
            contract_instance.to_json_file(json_path)
            created_files.append(json_path)

            # Also generate human-readable Markdown specification
            md_path = dest / f"{prefix}_{contract_instance.slug}.md"
            contract_instance.to_markdown_file(md_path)
            created_files.append(md_path)

        elif isinstance(contract_instance, CleanedSocialMediaContract):
            json_path = dest / f"{prefix}_{contract_instance.post_id}.json"
            contract_instance.to_json_file(json_path)
            created_files.append(json_path)

        elif isinstance(contract_instance, CleanedForensicsContract):
            json_path = dest / f"{prefix}_forensics_audit.json"
            contract_instance.to_json_file(json_path)
            created_files.append(json_path)

        elif isinstance(contract_instance, CleanedMultimodalContract):
            json_path = dest / f"{prefix}_multimodal_{contract_instance.content_type}.json"
            contract_instance.to_json_file(json_path)
            created_files.append(json_path)

        else:
            raise TypeError(f"Unsupported contract schema instance type: {type(contract_instance)}")

        return created_files

    @staticmethod
    def compute_sha256(file_path: Path | str) -> str:
        """Compute hex SHA-256 hash of a file."""
        p = Path(file_path)
        sha = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()
