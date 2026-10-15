# Antigravity Prompt Execution Log

| Timestamp (UTC) | Level | Stage | Tool | Action | Progress | Message |
|-----------------|-------|-------|------|--------|----------|---------|
| 2026-10-15 14:16:03 | INFO | Stage 1 | 01_curl_cffi | system_scaffold_check | 95% | Verification dry-run: 4-tier logger test |
| 2026-10-15 14:16:03 | WARN | Stage 1 | 01_curl_cffi | system_scaffold_check | 0% | This is a test WARN entry |
| 2026-10-15 14:28:36 | INFO | Stage 1 | 01_curl_cffi | system_scaffold_check | 95% | Verification dry-run: 4-tier logger test |
| 2026-10-15 14:28:36 | WARN | Stage 1 | 01_curl_cffi | system_scaffold_check | 0% | This is a test WARN entry |
| 2026-10-15 14:31:02 | INFO | Stage 1 |  | git_commit | 0% | Git commit: 36b205f — [SCAFFOLD] Stage 1 Step 1.0: Init Git governance, 4-tier logger, 20-tool spine, and live telemetry UI |
| 2026-10-15 14:32:05 | INFO | Stage 1 |  | git_commit | 0% | Git commit: e2055c1 — [UPDATE] Stage 1 Step 1.0: Fix logger_engine tool_ops write condition and finalize initial logs |
| 2026-10-15 14:53:56 | INFO | Stage 1 |  | git_commit | 0% | Git commit: 759acfe — [FIX] Stage 1 Step 1.1: Fix idle timer drift, add tools watchdog, action/date log filters, and run log/file viewer |
| 2026-10-15 14:55:52 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 10% | Initialized curl_cffi run run_145552_c1f3b819 impersonating chrome124 |
| 2026-10-15 14:55:52 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 35% | Executing GraphQL question detail query for 'two-sum' |
| 2026-10-15 14:55:53 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 60% | Successfully fetched live LeetCode GraphQL problem data |
| 2026-10-15 14:55:53 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 85% | Raw outputs saved to D:\Project_Files\Crawlers_testing\data\01_curl_cffi\scrape_for_leetcode\2026-10-15\run_145552_c1f3b819\raw (mode: live) |
| 2026-10-15 14:55:53 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 100% | Run manifest finalized, all 4 log tiers synchronized |
| 2026-10-15 14:56:42 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 10% | Initialized dual-parser run run_145642_b246e1e3 |
| 2026-10-15 14:56:43 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 35% | Fetched live HTML from https://books.toscrape.com/ (51274 bytes) |
| 2026-10-15 14:56:43 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 65% | Selectolax parsed 20 items in 890.5 us (0.89 ms) |
| 2026-10-15 14:56:43 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 85% | lxml XPath parsed 20 items in 2637.9 us (2.638 ms) |
| 2026-10-15 14:56:43 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 14:57:34 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 15% | Initialized Scrapy run run_145734_19397e0e for https://quotes.toscrape.com/ |
| 2026-10-15 14:57:36 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 75% | Scrapy process finished (exit code 0) in 2.14s |
| 2026-10-15 14:57:36 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 100% | Completed Scrapy run: 10 items collected |
| 2026-10-15 14:58:09 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 15% | Initialized httpx_parsel run run_145809_447daaf5 (HTTP/2 enabled) |
| 2026-10-15 14:58:10 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 60% | Saved raw responses (mode: live) |
| 2026-10-15 14:58:10 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 14:58:45 | INFO | Stage 1 | 05_trafilatura | article_extract | 15% | Initialized Trafilatura run run_145845_ebc2b46b for https://en.wikipedia.org/wiki/Web_crawler |
| 2026-10-15 14:58:45 | INFO | Stage 1 | 05_trafilatura | article_extract | 45% | Fetched live article (346739 bytes) in 0.612s |
| 2026-10-15 14:58:46 | INFO | Stage 1 | 05_trafilatura | article_extract | 95% | Boilerplate stripping: 346739 bytes -> 70718 bytes (79.6% reduction) |
| 2026-10-15 14:58:46 | INFO | Stage 1 | 05_trafilatura | article_extract | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 15:00:43 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 10% | Initialized curl_cffi run run_150043_a0ca0ded impersonating chrome124 |
| 2026-10-15 15:00:43 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 35% | Executing GraphQL question detail query for 'two-sum' |
| 2026-10-15 15:00:44 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 60% | Successfully fetched live LeetCode GraphQL problem data |
| 2026-10-15 15:00:44 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 85% | Raw outputs saved to D:\Project_Files\Crawlers_testing\data\01_curl_cffi\scrape_for_leetcode\2026-10-15\run_150043_a0ca0ded\raw (mode: live) |
| 2026-10-15 15:00:44 | INFO | Stage 1 | 01_curl_cffi | scrape_for_leetcode | 100% | Run manifest finalized, all 4 log tiers synchronized |
| 2026-10-15 15:00:44 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 10% | Initialized dual-parser run run_150044_a32d4083 |
| 2026-10-15 15:00:46 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 35% | Fetched live HTML from https://books.toscrape.com/ (51274 bytes) |
| 2026-10-15 15:00:46 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 65% | Selectolax parsed 20 items in 4928.6 us (4.929 ms) |
| 2026-10-15 15:00:46 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 85% | lxml XPath parsed 20 items in 4017.8 us (4.018 ms) |
| 2026-10-15 15:00:46 | INFO | Stage 1 | 02_selectolax_lxml | scrape_for_leetcode | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 15:00:46 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 15% | Initialized Scrapy run run_150046_c306193b for https://quotes.toscrape.com/ |
| 2026-10-15 15:00:48 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 75% | Scrapy process finished (exit code 0) in 2.13s |
| 2026-10-15 15:00:48 | INFO | Stage 1 | 03_scrapy | catalog_crawl | 100% | Completed Scrapy run: 10 items collected |
| 2026-10-15 15:00:48 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 15% | Initialized httpx_parsel run run_150048_b3157488 (HTTP/2 enabled) |
| 2026-10-15 15:00:49 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 60% | Saved raw responses (mode: live) |
| 2026-10-15 15:00:49 | INFO | Stage 1 | 04_httpx_parsel | scrape_for_leetcode | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 15:00:49 | INFO | Stage 1 | 05_trafilatura | article_extract | 15% | Initialized Trafilatura run run_150049_05609c83 for https://en.wikipedia.org/wiki/Web_crawler |
| 2026-10-15 15:00:50 | INFO | Stage 1 | 05_trafilatura | article_extract | 45% | Fetched live article (346739 bytes) in 0.571s |
| 2026-10-15 15:00:50 | INFO | Stage 1 | 05_trafilatura | article_extract | 95% | Boilerplate stripping: 346739 bytes -> 70718 bytes (79.6% reduction) |
| 2026-10-15 15:00:50 | INFO | Stage 1 | 05_trafilatura | article_extract | 100% | Run manifest finalized, 4-tier logs synchronized |
| 2026-10-15 15:01:25 | INFO | Stage 1 |  |  | 100% | Stage 1 Step 1.1 Batch 1 (01 to 05) verified and smoke-tested |
