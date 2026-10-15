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
| 2026-10-15 17:01:33 | INFO | Stage 1 | 06_playwright | secured_page_origin | 15% | Initialized Playwright run run_170133_56b5dee1 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:01:33 | INFO | Stage 1 | 06_playwright | secured_page_origin | 25% | Launching Playwright Chromium browser |
| 2026-10-15 17:01:35 | INFO | Stage 1 | 06_playwright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ |
| 2026-10-15 17:01:45 | ERROR | Stage 1 | 06_playwright | secured_page_origin | 0% | Playwright action 'secured_page_origin' failed: complete_action_run() got an unexpected keyword argument 'run_id' |
| 2026-10-15 17:03:45 | INFO | Stage 1 | 06_playwright | secured_page_origin | 15% | Initialized Playwright run run_170345_35691fc2 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:03:45 | INFO | Stage 1 | 06_playwright | secured_page_origin | 25% | Launching Playwright Chromium browser |
| 2026-10-15 17:03:45 | INFO | Stage 1 | 06_playwright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ |
| 2026-10-15 17:03:50 | INFO | Stage 1 | 06_playwright | secured_page_origin | 100% | Playwright action 'secured_page_origin' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:03:50 | INFO | Stage 1 | 07_patchright | secured_page_origin | 15% | Initialized Patchright run run_170350_27fe5c74 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:03:50 | INFO | Stage 1 | 07_patchright | secured_page_origin | 25% | Spawning Patchright binary-patched stealth Chromium |
| 2026-10-15 17:03:51 | INFO | Stage 1 | 07_patchright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ under stealth anti-bot profile |
| 2026-10-15 17:03:54 | INFO | Stage 1 | 07_patchright | secured_page_origin | 72% | Executing comprehensive bot fingerprint probe |
| 2026-10-15 17:03:54 | INFO | Stage 1 | 07_patchright | secured_page_origin | 100% | Patchright action 'secured_page_origin' completed (Evasion Score: 45/100) |
| 2026-10-15 17:03:54 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 15% | Initialized Camoufox run run_170354_73a6c4aa for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:03:54 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 25% | Initializing Camoufox C++ stealth Firefox engine |
| 2026-10-15 17:03:55 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 35% | Connecting via AsyncCamoufox context manager |
| 2026-10-15 17:05:27 | INFO | Stage 1 | 06_playwright | secured_page_origin | 15% | Initialized Playwright run run_170527_47645cc2 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:05:27 | INFO | Stage 1 | 06_playwright | secured_page_origin | 25% | Launching Playwright Chromium browser |
| 2026-10-15 17:05:27 | INFO | Stage 1 | 06_playwright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ |
| 2026-10-15 17:05:31 | INFO | Stage 1 | 06_playwright | secured_page_origin | 100% | Playwright action 'secured_page_origin' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:05:31 | INFO | Stage 1 | 07_patchright | secured_page_origin | 15% | Initialized Patchright run run_170531_ae5268e5 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:05:31 | INFO | Stage 1 | 07_patchright | secured_page_origin | 25% | Spawning Patchright binary-patched stealth Chromium |
| 2026-10-15 17:05:31 | INFO | Stage 1 | 07_patchright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ under stealth anti-bot profile |
| 2026-10-15 17:05:34 | INFO | Stage 1 | 07_patchright | secured_page_origin | 72% | Executing comprehensive bot fingerprint probe |
| 2026-10-15 17:05:35 | INFO | Stage 1 | 07_patchright | secured_page_origin | 100% | Patchright action 'secured_page_origin' completed (Evasion Score: 45/100) |
| 2026-10-15 17:05:35 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 15% | Initialized Camoufox run run_170535_9f4b6322 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:05:35 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 25% | Initializing Camoufox C++ stealth Firefox engine |
| 2026-10-15 17:05:35 | WARN | Stage 1 | 08_camoufox | fingerprint_evasion | 40% | Camoufox C++ binary unavailable (Camoufox custom C++ binary not cached locally; falling back to installed Firefox); falling back cleanly to Playwright Firefox |
| 2026-10-15 17:05:42 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 100% | Camoufox action 'fingerprint_evasion' completed using engine 'playwright_firefox_fallback' |
| 2026-10-15 17:05:42 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 15% | Initialized nodriver run run_170542_d97a082e for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:05:42 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 25% | Starting nodriver direct CDP Chrome session (no WebDriver) |
| 2026-10-15 17:05:42 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 35% | Spawning browser instance via nodriver.start() |
| 2026-10-15 17:05:42 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 50% | Navigating to https://quotes.toscrape.com/js/ via raw CDP target commands |
| 2026-10-15 17:05:45 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 100% | Nodriver action 'cdp_intercept' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:05:45 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 15% | Initialized Scrapling run run_170545_bc3035d9 for target https://quotes.toscrape.com/ |
| 2026-10-15 17:05:45 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 25% | Initializing Scrapling Self-Healing DOM Engine |
| 2026-10-15 17:05:45 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 50% | Phase A Complete: Fingerprinted title='Two Sum', diff='Easy' |
| 2026-10-15 17:05:45 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 75% | Phase B Complete: Adaptive Relocation title_healed=False, diff_healed=False |
| 2026-10-15 17:05:46 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 100% | Scrapling action 'adaptive_extract' completed with 66.7% self-healing rate |
| 2026-10-15 17:07:07 | INFO | Stage 1 | 06_playwright | secured_page_origin | 15% | Initialized Playwright run run_170707_c8f73217 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:07:08 | INFO | Stage 1 | 06_playwright | secured_page_origin | 25% | Launching Playwright Chromium browser |
| 2026-10-15 17:07:08 | INFO | Stage 1 | 06_playwright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ |
| 2026-10-15 17:07:11 | INFO | Stage 1 | 06_playwright | secured_page_origin | 100% | Playwright action 'secured_page_origin' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:07:48 | INFO | Stage 1 | 07_patchright | secured_page_origin | 15% | Initialized Patchright run run_170748_78f1c054 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:07:48 | INFO | Stage 1 | 07_patchright | secured_page_origin | 25% | Spawning Patchright binary-patched stealth Chromium |
| 2026-10-15 17:07:49 | INFO | Stage 1 | 07_patchright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ under stealth anti-bot profile |
| 2026-10-15 17:07:52 | INFO | Stage 1 | 07_patchright | secured_page_origin | 72% | Executing comprehensive bot fingerprint probe |
| 2026-10-15 17:07:53 | INFO | Stage 1 | 07_patchright | secured_page_origin | 100% | Patchright action 'secured_page_origin' completed (Evasion Score: 45/100) |
| 2026-10-15 17:08:15 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 15% | Initialized Camoufox run run_170815_48116685 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:08:15 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 25% | Initializing Camoufox C++ stealth Firefox engine |
| 2026-10-15 17:08:16 | WARN | Stage 1 | 08_camoufox | fingerprint_evasion | 40% | Camoufox C++ binary unavailable (Camoufox custom C++ binary not cached locally; falling back to installed Firefox); falling back cleanly to Playwright Firefox |
| 2026-10-15 17:08:25 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 100% | Camoufox action 'fingerprint_evasion' completed using engine 'playwright_firefox_fallback' |
| 2026-10-15 17:08:47 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 15% | Initialized nodriver run run_170847_09abb530 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:08:47 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 25% | Starting nodriver direct CDP Chrome session (no WebDriver) |
| 2026-10-15 17:08:47 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 35% | Spawning browser instance via nodriver.start() |
| 2026-10-15 17:08:48 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 50% | Navigating to https://quotes.toscrape.com/js/ via raw CDP target commands |
| 2026-10-15 17:08:50 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 100% | Nodriver action 'cdp_intercept' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:09:51 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 15% | Initialized nodriver run run_170951_d3eaf7ab for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:09:51 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 25% | Starting nodriver direct CDP Chrome session (no WebDriver) |
| 2026-10-15 17:09:51 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 35% | Spawning browser instance via nodriver.start() |
| 2026-10-15 17:09:52 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 50% | Navigating to https://quotes.toscrape.com/js/ via raw CDP target commands |
| 2026-10-15 17:09:54 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 100% | Nodriver action 'cdp_intercept' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:10:39 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 15% | Initialized Scrapling run run_171039_c489f85d for target https://quotes.toscrape.com/ |
| 2026-10-15 17:10:39 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 25% | Initializing Scrapling Self-Healing DOM Engine |
| 2026-10-15 17:10:39 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 50% | Phase A Complete: Fingerprinted title='Two Sum', diff='Easy' |
| 2026-10-15 17:10:39 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 75% | Phase B Complete: Adaptive Relocation title_healed=False, diff_healed=True |
| 2026-10-15 17:10:40 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 100% | Scrapling action 'adaptive_extract' completed with 66.7% self-healing rate |
| 2026-10-15 17:10:56 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 15% | Initialized Scrapling run run_171056_d55f5335 for target https://quotes.toscrape.com/ |
| 2026-10-15 17:10:56 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 25% | Initializing Scrapling Self-Healing DOM Engine |
| 2026-10-15 17:10:56 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 50% | Phase A Complete: Fingerprinted title='Two Sum', diff='Easy' |
| 2026-10-15 17:10:56 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 75% | Phase B Complete: Adaptive Relocation title_healed=True, diff_healed=True |
| 2026-10-15 17:10:57 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 100% | Scrapling action 'adaptive_extract' completed with 100.0% self-healing rate |
| 2026-10-15 17:11:17 | INFO | Stage 1 | 06_playwright | secured_page_origin | 15% | Initialized Playwright run run_171117_e32d3078 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:11:17 | INFO | Stage 1 | 06_playwright | secured_page_origin | 25% | Launching Playwright Chromium browser |
| 2026-10-15 17:11:17 | INFO | Stage 1 | 06_playwright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ |
| 2026-10-15 17:11:21 | INFO | Stage 1 | 06_playwright | secured_page_origin | 100% | Playwright action 'secured_page_origin' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:11:21 | INFO | Stage 1 | 07_patchright | secured_page_origin | 15% | Initialized Patchright run run_171121_72698e1b for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:11:21 | INFO | Stage 1 | 07_patchright | secured_page_origin | 25% | Spawning Patchright binary-patched stealth Chromium |
| 2026-10-15 17:11:22 | INFO | Stage 1 | 07_patchright | secured_page_origin | 45% | Navigating to https://quotes.toscrape.com/js/ under stealth anti-bot profile |
| 2026-10-15 17:11:25 | INFO | Stage 1 | 07_patchright | secured_page_origin | 72% | Executing comprehensive bot fingerprint probe |
| 2026-10-15 17:11:26 | INFO | Stage 1 | 07_patchright | secured_page_origin | 100% | Patchright action 'secured_page_origin' completed (Evasion Score: 45/100) |
| 2026-10-15 17:11:26 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 15% | Initialized Camoufox run run_171126_35971713 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:11:26 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 25% | Initializing Camoufox C++ stealth Firefox engine |
| 2026-10-15 17:11:27 | WARN | Stage 1 | 08_camoufox | fingerprint_evasion | 40% | Camoufox C++ binary unavailable (Camoufox custom C++ binary not cached locally; falling back to installed Firefox); falling back cleanly to Playwright Firefox |
| 2026-10-15 17:11:33 | INFO | Stage 1 | 08_camoufox | fingerprint_evasion | 100% | Camoufox action 'fingerprint_evasion' completed using engine 'playwright_firefox_fallback' |
| 2026-10-15 17:11:33 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 15% | Initialized nodriver run run_171133_351872c2 for target https://quotes.toscrape.com/js/ |
| 2026-10-15 17:11:33 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 25% | Starting nodriver direct CDP Chrome session (no WebDriver) |
| 2026-10-15 17:11:33 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 35% | Spawning browser instance via nodriver.start() |
| 2026-10-15 17:11:34 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 50% | Navigating to https://quotes.toscrape.com/js/ via raw CDP target commands |
| 2026-10-15 17:11:36 | INFO | Stage 1 | 09_nodriver | cdp_intercept | 100% | Nodriver action 'cdp_intercept' completed successfully (Title: 'Quotes to Scrape') |
| 2026-10-15 17:11:36 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 15% | Initialized Scrapling run run_171136_6f56ec74 for target https://quotes.toscrape.com/ |
| 2026-10-15 17:11:36 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 25% | Initializing Scrapling Self-Healing DOM Engine |
| 2026-10-15 17:11:36 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 50% | Phase A Complete: Fingerprinted title='Two Sum', diff='Easy' |
| 2026-10-15 17:11:36 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 75% | Phase B Complete: Adaptive Relocation title_healed=True, diff_healed=True |
| 2026-10-15 17:11:37 | INFO | Stage 1 | 10_scrapling | adaptive_extract | 100% | Scrapling action 'adaptive_extract' completed with 100.0% self-healing rate |
| 2026-10-15 17:12:51 | INFO | Stage 1 |  | git_commit | 0% | Git commit: 36962c7 — [RUN-LOG] Stage 1 Step 1.2: Verify Batch 2 smoke tests and sync 4-tier logs |
