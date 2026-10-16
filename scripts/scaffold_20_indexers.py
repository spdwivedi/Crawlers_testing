"""
scripts/scaffold_20_indexers.py
===============================
Generates tools/<tool_id>/indexer.py for all 20 tools.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDEXERS = {
    "01_curl_cffi": '''"""
tools/01_curl_cffi/indexer.py
=============================
Dedicated Indexer for 01_curl_cffi.
Extracts TLS impersonation profile, GraphQL problem slug, catalog problem count, and HTTP status.
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
    def __init__(self, tool_id: str = "01_curl_cffi"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "tls_impersonation_profile": "chrome124",
            "graphql_problem_slug": None,
            "catalog_problems_count": 0,
            "http_status": 200,
        }
        headers_file = raw_dir / "response_headers.json"
        if headers_file.exists():
            try:
                hd = json.loads(headers_file.read_text(encoding="utf-8"))
                metrics["http_status"] = hd.get("status_code", hd.get("status", 200))
            except Exception:
                pass

        cat_file = cleaned_dir / "catalog_index.json"
        if cat_file.exists():
            try:
                items = json.loads(cat_file.read_text(encoding="utf-8"))
                if isinstance(items, list):
                    metrics["catalog_problems_count"] = len(items)
                    if items and isinstance(items[0], dict):
                        metrics["graphql_problem_slug"] = items[0].get("slug")
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "02_selectolax_lxml": '''"""
tools/02_selectolax_lxml/indexer.py
===================================
Dedicated Indexer for 02_selectolax_lxml.
Extracts items parsed, selectolax parse us, lxml parse us, and speedup factor.
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
    def __init__(self, tool_id: str = "02_selectolax_lxml"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "items_parsed": 0,
            "selectolax_parse_us": None,
            "lxml_parse_us": None,
            "speedup_factor": None,
        }
        cat_file = cleaned_dir / "parsed_catalog.json"
        if cat_file.exists():
            try:
                data = json.loads(cat_file.read_text(encoding="utf-8"))
                items = data.get("items", [])
                metrics["items_parsed"] = len(items)
                bench = data.get("benchmark", {})
                metrics["selectolax_parse_us"] = bench.get("selectolax_us")
                metrics["lxml_parse_us"] = bench.get("lxml_us")
                metrics["speedup_factor"] = bench.get("speedup_factor")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "03_scrapy": '''"""
tools/03_scrapy/indexer.py
==========================
Dedicated Indexer for 03_scrapy.
Extracts spider items scraped, spider elapsed sec, and pipeline status.
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
    def __init__(self, tool_id: str = "03_scrapy"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "spider_items_scraped": 0,
            "spider_elapsed_sec": 0.0,
            "pipeline_status": "unknown",
        }
        stats_file = cleaned_dir / "spider_stats.json"
        if stats_file.exists():
            try:
                data = json.loads(stats_file.read_text(encoding="utf-8"))
                metrics["spider_items_scraped"] = data.get("items_scraped", 0)
                metrics["spider_elapsed_sec"] = data.get("elapsed_seconds", 0.0)
                metrics["pipeline_status"] = data.get("close_reason", "finished")
            except Exception:
                pass
        
        items_file = cleaned_dir / "scrapy_items.jsonl"
        if items_file.exists() and metrics["spider_items_scraped"] == 0:
            try:
                lines = [l for l in items_file.read_text(encoding="utf-8").splitlines() if l.strip()]
                metrics["spider_items_scraped"] = len(lines)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "04_httpx_parsel": '''"""
tools/04_httpx_parsel/indexer.py
================================
Dedicated Indexer for 04_httpx_parsel.
Extracts http2 enabled, concurrent requests count, jmespath fields extracted, and xpath nodes extracted.
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
    def __init__(self, tool_id: str = "04_httpx_parsel"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "http2_enabled": True,
            "concurrent_requests_count": 1,
            "jmespath_fields_extracted": 0,
            "xpath_nodes_extracted": 0,
        }
        extracted_file = cleaned_dir / "async_extracted.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                meta = data.get("fetch_metadata", {})
                metrics["http2_enabled"] = meta.get("http2", True)
                metrics["concurrent_requests_count"] = meta.get("concurrent_requests", 1)
                
                jmes = data.get("json_jmespath_extracted", {})
                metrics["jmespath_fields_extracted"] = len(jmes) if isinstance(jmes, dict) else len(jmes) if isinstance(jmes, list) else 0

                html_nodes = data.get("html_parsel_extracted", {})
                metrics["xpath_nodes_extracted"] = len(html_nodes) if isinstance(html_nodes, dict) else len(html_nodes) if isinstance(html_nodes, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "05_trafilatura": '''"""
tools/05_trafilatura/indexer.py
===============================
Dedicated Indexer for 05_trafilatura.
Extracts raw html bytes, clean md bytes, boilerplate reduction pct, and extracted title.
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
    def __init__(self, tool_id: str = "05_trafilatura"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "raw_html_bytes": 0,
            "clean_md_bytes": 0,
            "boilerplate_reduction_pct": 0.0,
            "extracted_title": "",
        }
        raw_html = raw_dir / "raw_page.html"
        if raw_html.exists():
            metrics["raw_html_bytes"] = raw_html.stat().st_size

        clean_md = cleaned_dir / "extracted_content.md"
        if clean_md.exists():
            metrics["clean_md_bytes"] = clean_md.stat().st_size

        if metrics["raw_html_bytes"] > 0:
            reduction = (1.0 - (metrics["clean_md_bytes"] / metrics["raw_html_bytes"])) * 100.0
            metrics["boilerplate_reduction_pct"] = round(max(0.0, reduction), 2)

        meta_file = cleaned_dir / "metadata.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                metrics["extracted_title"] = data.get("title", "")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "06_playwright": '''"""
tools/06_playwright/indexer.py
==============================
Dedicated Indexer for 06_playwright.
Extracts har total requests, unique origins discovered, screenshot bytes, and rendered dom bytes.
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
    def __init__(self, tool_id: str = "06_playwright"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "har_total_requests": 0,
            "unique_origins_discovered": 0,
            "screenshot_bytes": 0,
            "rendered_dom_bytes": 0,
        }
        origin_file = cleaned_dir / "origin_map.json"
        if origin_file.exists():
            try:
                data = json.loads(origin_file.read_text(encoding="utf-8"))
                metrics["har_total_requests"] = data.get("total_requests_recorded", 0)
                origins = data.get("unique_origins", [])
                metrics["unique_origins_discovered"] = len(origins) if isinstance(origins, list) else 0
            except Exception:
                pass

        screenshot = raw_dir / "page_visual.png"
        if screenshot.exists():
            metrics["screenshot_bytes"] = screenshot.stat().st_size

        dom_file = raw_dir / "rendered_dom.html"
        if dom_file.exists():
            metrics["rendered_dom_bytes"] = dom_file.stat().st_size

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "07_patchright": '''"""
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
''',

    "08_camoufox": '''"""
tools/08_camoufox/indexer.py
============================
Dedicated Indexer for 08_camoufox.
Extracts engine used, spoofed oscpu, canvas hash, and webgl renderer.
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
    def __init__(self, tool_id: str = "08_camoufox"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "engine_used": "Camoufox Firefox",
            "spoofed_oscpu": "Windows NT 10.0; Win64; x64",
            "canvas_hash": None,
            "webgl_renderer": None,
        }
        extracted_file = cleaned_dir / "extracted_data.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                metrics["engine_used"] = data.get("engine_used", "Camoufox Firefox")
                fp = data.get("spoofed_fingerprint", {})
                metrics["spoofed_oscpu"] = fp.get("oscpu", metrics["spoofed_oscpu"])
                metrics["canvas_hash"] = fp.get("canvas_hash")
                metrics["webgl_renderer"] = fp.get("webgl_renderer")
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "09_nodriver": '''"""
tools/09_nodriver/indexer.py
============================
Dedicated Indexer for 09_nodriver.
Extracts cdp direct mode, links extracted count, and dom size bytes.
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
    def __init__(self, tool_id: str = "09_nodriver"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "cdp_direct_mode": True,
            "links_extracted_count": 0,
            "dom_size_bytes": 0,
        }
        extracted_file = cleaned_dir / "cdp_extracted.json"
        if extracted_file.exists():
            try:
                data = json.loads(extracted_file.read_text(encoding="utf-8"))
                links = data.get("extracted_links", [])
                metrics["links_extracted_count"] = len(links) if isinstance(links, list) else 0
            except Exception:
                pass

        dom_file = raw_dir / "cdp_dom.html"
        if dom_file.exists():
            metrics["dom_size_bytes"] = dom_file.stat().st_size
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "10_scrapling": '''"""
tools/10_scrapling/indexer.py
=============================
Dedicated Indexer for 10_scrapling.
Extracts baseline elements count, mutated elements recovered, healing rate pct, and avg similarity score.
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
    def __init__(self, tool_id: str = "10_scrapling"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "baseline_elements_count": 0,
            "mutated_elements_recovered": 0,
            "healing_rate_pct": 100.0,
            "avg_similarity_score": 0.95,
        }
        bench_file = cleaned_dir / "self_healing_benchmark.json"
        if bench_file.exists():
            try:
                data = json.loads(bench_file.read_text(encoding="utf-8"))
                base = data.get("phase_a_baseline", {})
                metrics["baseline_elements_count"] = base.get("elements_found_count", 0)
                mut = data.get("phase_b_mutated_redesign", {})
                metrics["mutated_elements_recovered"] = mut.get("elements_recovered_count", 0)
                metrics["healing_rate_pct"] = float(mut.get("healing_rate_pct", 100.0))
                metrics["avg_similarity_score"] = float(mut.get("average_similarity_score", 0.95))
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "11_yt_dlp_ffmpeg": '''"""
tools/11_yt_dlp_ffmpeg/indexer.py
=================================
Dedicated Indexer for 11_yt_dlp_ffmpeg.
Extracts raw hls chunks count, combined video bytes, extracted audio wav bytes, video codec, and duration sec.
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
    def __init__(self, tool_id: str = "11_yt_dlp_ffmpeg"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "raw_hls_chunks_count": 0,
            "combined_video_bytes": 0,
            "extracted_audio_wav_bytes": 0,
            "video_codec": "h264",
            "duration_sec": 3.0,
        }
        if raw_dir.exists():
            chunks = list(raw_dir.glob("*.ts"))
            metrics["raw_hls_chunks_count"] = len(chunks)

        analysis_file = cleaned_dir / "media_analysis.json"
        if analysis_file.exists():
            try:
                data = json.loads(analysis_file.read_text(encoding="utf-8"))
                meta = data.get("metadata", {})
                metrics["duration_sec"] = float(meta.get("duration_seconds", 3.0))
                stream_pipe = data.get("stream_pipeline", {})
                if "raw_hls_chunks_count" in stream_pipe:
                    metrics["raw_hls_chunks_count"] = stream_pipe.get("raw_hls_chunks_count")
                vid = data.get("combined_video", {})
                metrics["combined_video_bytes"] = vid.get("size_bytes", 0)
                metrics["video_codec"] = vid.get("codec", "h264")
                wav = data.get("extracted_audio_wav", {})
                metrics["extracted_audio_wav_bytes"] = wav.get("size_bytes", 0)
            except Exception:
                pass
        
        vid_file = cleaned_dir / "combined_video.mp4"
        if vid_file.exists() and metrics["combined_video_bytes"] == 0:
            metrics["combined_video_bytes"] = vid_file.stat().st_size
        wav_file = cleaned_dir / "extracted_audio.wav"
        if wav_file.exists() and metrics["extracted_audio_wav_bytes"] == 0:
            metrics["extracted_audio_wav_bytes"] = wav_file.stat().st_size

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "12_instaloader": '''"""
tools/12_instaloader/indexer.py
===============================
Dedicated Indexer for 12_instaloader.
Extracts insta shortcode, auth mode, likes count, comments count, and hashtags count.
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
    def __init__(self, tool_id: str = "12_instaloader"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "insta_shortcode": "test_shortcode",
            "auth_mode": "anonymous_guest",
            "likes_count": 0,
            "comments_count": 0,
            "hashtags_count": 0,
        }
        post_file = cleaned_dir / "insta_post_structured.json"
        if post_file.exists():
            try:
                data = json.loads(post_file.read_text(encoding="utf-8"))
                metrics["insta_shortcode"] = data.get("shortcode", "test_shortcode")
                prov = data.get("provenance", {})
                metrics["auth_mode"] = prov.get("auth_mode", "anonymous_guest")
                eng = data.get("engagement", {})
                metrics["likes_count"] = eng.get("likes", 0)
                metrics["comments_count"] = eng.get("comments", 0)
                content = data.get("content", {})
                tags = content.get("hashtags", [])
                metrics["hashtags_count"] = len(tags) if isinstance(tags, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "13_gallery_dl": '''"""
tools/13_gallery_dl/indexer.py
==============================
Dedicated Indexer for 13_gallery_dl.
Extracts extractor used, platform, gallery items count, and media files downloaded.
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
    def __init__(self, tool_id: str = "13_gallery_dl"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "extractor_used": "gallery-dl",
            "platform": "generic",
            "gallery_items_count": 0,
            "media_files_downloaded": 0,
        }
        cat_file = cleaned_dir / "gallery_catalog.json"
        if cat_file.exists():
            try:
                data = json.loads(cat_file.read_text(encoding="utf-8"))
                metrics["extractor_used"] = data.get("resolved_extractor", "gallery-dl")
                items = data.get("items", [])
                metrics["gallery_items_count"] = len(items) if isinstance(items, list) else data.get("item_count", 0)
                if items and isinstance(items[0], dict):
                    metrics["platform"] = items[0].get("platform", "gallery")
                saved = data.get("raw_media_saved", [])
                metrics["media_files_downloaded"] = len(saved) if isinstance(saved, list) else 0
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "14_singlefile_archive": '''"""
tools/14_singlefile_archive/indexer.py
======================================
Dedicated Indexer for 14_singlefile_archive.
Extracts singlefile size kb, inlined css count, inlined images base64 count, and scripts stripped count.
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
    def __init__(self, tool_id: str = "14_singlefile_archive"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "singlefile_size_kb": 0.0,
            "inlined_css_count": 0,
            "inlined_images_base64_count": 0,
            "scripts_stripped_count": 0,
        }
        manifest_file = cleaned_dir / "inlined_assets_manifest.json"
        if manifest_file.exists():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                size_bytes = data.get("final_html_size_bytes", 0)
                metrics["singlefile_size_kb"] = round(size_bytes / 1024.0, 2)
                metrics["inlined_css_count"] = data.get("stylesheets_count", 0)
                metrics["inlined_images_base64_count"] = data.get("images_count", 0)
                metrics["scripts_stripped_count"] = data.get("scripts_sanitized_count", 0)
            except Exception:
                pass

        snapshot = raw_dir / "snapshot.singlefile.html"
        if snapshot.exists() and metrics["singlefile_size_kb"] == 0.0:
            metrics["singlefile_size_kb"] = round(snapshot.stat().st_size / 1024.0, 2)

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "15_mitmproxy_interceptor": '''"""
tools/15_mitmproxy_interceptor/indexer.py
=========================================
Dedicated Indexer for 15_mitmproxy_interceptor.
Extracts intercepted flows count, discovered api endpoints count, and proxy port used.
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
    def __init__(self, tool_id: str = "15_mitmproxy_interceptor"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "intercepted_flows_count": 0,
            "discovered_api_endpoints_count": 0,
            "proxy_port_used": 8080,
        }
        apis_file = cleaned_dir / "discovered_apis.json"
        if apis_file.exists():
            try:
                data = json.loads(apis_file.read_text(encoding="utf-8"))
                metrics["intercepted_flows_count"] = data.get("total_flows_intercepted", 0)
                metrics["discovered_api_endpoints_count"] = data.get("discovered_apis_count", 0)
                metrics["proxy_port_used"] = data.get("proxy_port_used", 8080)
            except Exception:
                pass

        flows_file = raw_dir / "intercepted_flows.jsonl"
        if flows_file.exists() and metrics["intercepted_flows_count"] == 0:
            try:
                lines = [l for l in flows_file.read_text(encoding="utf-8").splitlines() if l.strip()]
                metrics["intercepted_flows_count"] = len(lines)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "16_crawl4ai": '''"""
tools/16_crawl4ai/indexer.py
============================
Dedicated Indexer for 16_crawl4ai.
Extracts semantic chunks count, markdown length chars, links discovered count, and media discovered count.
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
    def __init__(self, tool_id: str = "16_crawl4ai"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "semantic_chunks_count": 0,
            "markdown_length_chars": 0,
            "links_discovered_count": 0,
            "media_discovered_count": 0,
        }
        chunks_file = cleaned_dir / "semantic_chunks.json"
        if chunks_file.exists():
            try:
                data = json.loads(chunks_file.read_text(encoding="utf-8"))
                metrics["semantic_chunks_count"] = data.get("total_chunks", 0)
            except Exception:
                pass

        md_file = cleaned_dir / "llm_ready.md"
        if md_file.exists():
            metrics["markdown_length_chars"] = len(md_file.read_text(encoding="utf-8", errors="replace"))

        media_links = cleaned_dir / "media_and_links.json"
        if media_links.exists():
            try:
                data = json.loads(media_links.read_text(encoding="utf-8"))
                metrics["links_discovered_count"] = data.get("total_links", 0)
                metrics["media_discovered_count"] = data.get("total_media", 0)
            except Exception:
                pass

        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "17_surya_ocr": '''"""
tools/17_surya_ocr/indexer.py
=============================
Dedicated Indexer for 17_surya_ocr.
Extracts ocr lines recognized, avg ocr confidence, and test image dimensions.
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
    def __init__(self, tool_id: str = "17_surya_ocr"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "ocr_lines_recognized": 0,
            "avg_ocr_confidence": 0.98,
            "test_image_dimensions": "1280x720",
        }
        ocr_file = cleaned_dir / "ocr_structured.json"
        if ocr_file.exists():
            try:
                data = json.loads(ocr_file.read_text(encoding="utf-8"))
                metrics["ocr_lines_recognized"] = data.get("total_lines_detected", 0)
                metrics["avg_ocr_confidence"] = float(data.get("average_confidence", 0.98))
                dims = data.get("image_dimensions")
                if dims:
                    metrics["test_image_dimensions"] = f"{dims[0]}x{dims[1]}" if isinstance(dims, (list, tuple)) else str(dims)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "18_paddleocr_img2table": '''"""
tools/18_paddleocr_img2table/indexer.py
=======================================
Dedicated Indexer for 18_paddleocr_img2table.
Extracts tables detected count, table rows, table cols, and cells extracted count.
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
    def __init__(self, tool_id: str = "18_paddleocr_img2table"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "tables_detected_count": 0,
            "table_rows": 0,
            "table_cols": 0,
            "cells_extracted_count": 0,
        }
        table_file = cleaned_dir / "extracted_table.json"
        if table_file.exists():
            try:
                data = json.loads(table_file.read_text(encoding="utf-8"))
                rows = data.get("row_count", 0)
                cols = data.get("column_count", 0)
                metrics["tables_detected_count"] = 1 if rows > 0 else 0
                metrics["table_rows"] = rows
                metrics["table_cols"] = cols
                metrics["cells_extracted_count"] = rows * cols
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "19_docling_pdf": '''"""
tools/19_docling_pdf/indexer.py
===============================
Dedicated Indexer for 19_docling_pdf.
Extracts pdf pages count, hierarchy nodes count, and pdf tables parsed.
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
    def __init__(self, tool_id: str = "19_docling_pdf"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "pdf_pages_count": 1,
            "hierarchy_nodes_count": 0,
            "pdf_tables_parsed": 0,
        }
        doc_file = cleaned_dir / "document_hierarchy.json"
        if doc_file.exists():
            try:
                data = json.loads(doc_file.read_text(encoding="utf-8"))
                metrics["pdf_pages_count"] = data.get("page_count", 1)
                metrics["hierarchy_nodes_count"] = data.get("total_nodes", 0)
                metrics["pdf_tables_parsed"] = data.get("tables_count", 0)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',

    "20_faster_whisper_scrapegraph": '''"""
tools/20_faster_whisper_scrapegraph/indexer.py
==============================================
Dedicated Indexer for 20_faster_whisper_scrapegraph.
Extracts audio duration sec, srt segments count, knowledge graph nodes, and knowledge graph edges.
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
    def __init__(self, tool_id: str = "20_faster_whisper_scrapegraph"):
        super().__init__(tool_id=tool_id)

    def extract_domain_metrics(self, run_dir: Path, raw_dir: Path, cleaned_dir: Path) -> dict[str, Any]:
        metrics = {
            "audio_duration_sec": 0.0,
            "srt_segments_count": 0,
            "knowledge_graph_nodes": 0,
            "knowledge_graph_edges": 0,
        }
        seg_file = cleaned_dir / "transcript_segments.json"
        if seg_file.exists():
            try:
                data = json.loads(seg_file.read_text(encoding="utf-8"))
                metrics["audio_duration_sec"] = float(data.get("duration_seconds", 0.0))
                metrics["srt_segments_count"] = data.get("segments_count", 0)
            except Exception:
                pass

        kg_file = cleaned_dir / "knowledge_graph.json"
        if kg_file.exists():
            try:
                data = json.loads(kg_file.read_text(encoding="utf-8"))
                metrics["knowledge_graph_nodes"] = data.get("nodes_count", 0)
                metrics["knowledge_graph_edges"] = data.get("edges_count", 0)
            except Exception:
                pass
        return metrics

if __name__ == "__main__":
    indexer = ToolIndexer()
    res = indexer.index_all_runs()
    print(f"Indexed {res['runs_indexed']} runs for {res['tool_id']}")
''',
}

def main():
    count = 0
    for tool_id, code in INDEXERS.items():
        tool_dir = ROOT / "tools" / tool_id
        tool_dir.mkdir(parents=True, exist_ok=True)
        indexer_path = tool_dir / "indexer.py"
        indexer_path.write_text(code, encoding="utf-8")
        count += 1
        print(f"Generated {indexer_path}")
    print(f"Successfully generated {count}/20 dedicated indexers.")

if __name__ == "__main__":
    main()
