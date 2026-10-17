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
| 2026-10-15 17:37:02 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 10% | Initialized yt-dlp + FFmpeg run run_173702_6c373151 for target https://www.instagram.com/reel/C8XYZ12345/ |
| 2026-10-15 17:37:02 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 20% | Using FFmpeg binary at: D:\Project_Files\Crawlers_testing\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe |
| 2026-10-15 17:37:02 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 30% | Target: https://www.instagram.com/reel/C8XYZ12345/ | Auth mode: anonymous |
| 2026-10-15 17:37:04 | WARN | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 45% | Live yt-dlp extraction skipped/failed: ERROR: [Instagram] C8XYZ12345: Instagram sent an empty media response. Check if this post is accessible in your browser without being logged-in. If it is not, then use --cookies-from-browser or --cookies for the authentication. See  https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp  for how to manually pass cookies. Otherwise, if the post is accessible in browser without being logged-in, please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U. Switching to deterministic HLS stream test. |
| 2026-10-15 17:37:04 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 65% | Captured 3 raw chunks into raw |
| 2026-10-15 17:37:05 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 100% | yt-dlp + FFmpeg action 'scrape_for_insta' completed successfully (Title: 'Antigravity Instagram Reel Stream Capture & Audio Demux Test', Duration: 3.04s) |
| 2026-10-15 17:37:59 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 10% | Initialized Instaloader run run_173759_aeb13553 for target https://www.instagram.com/reel/C8XYZ12345/ |
| 2026-10-15 17:37:59 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 30% | Target shortcode: C8XYZ12345 | Auth mode: anonymous |
| 2026-10-15 17:37:59 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 70% | Saved untouched Instagram Graph JSON and thumbnail to raw/ |
| 2026-10-15 17:37:59 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 100% | Instaloader action 'scrape_for_insta' completed successfully (Shortcode: C8XYZ12345, Owner: @antigravity_crawler) |
| 2026-10-15 17:39:21 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 10% | Initialized gallery-dl run run_173921_2223241c for target https://www.facebook.com/photo.php?fbid=987654321 |
| 2026-10-15 17:39:21 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 30% | Resolved extractor: FacebookPhotoExtractor (Category: facebook, Subcategory: photo) |
| 2026-10-15 17:39:22 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 75% | Saved raw extractor dump and sample media asset to raw/ |
| 2026-10-15 17:39:22 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 100% | gallery-dl action 'scrape_for_facebook' completed successfully (Class: FacebookPhotoExtractor, Items: 2) |
| 2026-10-15 17:40:48 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 10% | Initialized SingleFile run run_174048_9669f34d for target https://books.toscrape.com/ |
| 2026-10-15 17:40:48 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 30% | Connecting to https://books.toscrape.com/... |
| 2026-10-15 17:40:49 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 45% | Retrieved 51274 bytes of HTML |
| 2026-10-15 17:40:55 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 100% | SingleFile action 'offline_archive' completed successfully (Size: 496235 B, CSS: 3, Img: 20) |
| 2026-10-15 17:42:59 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 10% | Initialized mitmproxy run run_174259_98572089 for target http://books.toscrape.com/ |
| 2026-10-15 17:42:59 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 15% | Allocated free local proxy port: 57240 |
| 2026-10-15 17:43:00 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 40% | mitmdump proxy active and listening on port 57240 |
| 2026-10-15 17:43:00 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 55% | Routing document origin: http://books.toscrape.com/ |
| 2026-10-15 17:43:01 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 65% | Routing XHR JSON API endpoint: http://httpbin.org/get?category=algorithms&limit=25&origin=crawlers_test |
| 2026-10-15 17:43:02 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 70% | Routing stream manifest target: http://httpbin.org/base64/ZXhhbXBsZQ== |
| 2026-10-15 17:43:03 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 75% | Terminated mitmdump background process |
| 2026-10-15 17:43:03 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 100% | mitmproxy action 'api_intercept' completed successfully (Flows: 3, APIs: 1) |
| 2026-10-15 17:44:07 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 10% | Initialized yt-dlp + FFmpeg run run_174407_254697ba for target https://www.instagram.com/reel/C8XYZ12345/ |
| 2026-10-15 17:44:07 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 20% | Using FFmpeg binary at: D:\Project_Files\Crawlers_testing\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe |
| 2026-10-15 17:44:07 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 30% | Target: https://www.instagram.com/reel/C8XYZ12345/ | Auth mode: anonymous |
| 2026-10-15 17:44:09 | WARN | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 45% | Live yt-dlp extraction skipped/failed: ERROR: [Instagram] C8XYZ12345: Instagram sent an empty media response. Check if this post is accessible in your browser without being logged-in. If it is not, then use --cookies-from-browser or --cookies for the authentication. See  https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp  for how to manually pass cookies. Otherwise, if the post is accessible in browser without being logged-in, please report this issue on  https://github.com/yt-dlp/yt-dlp/issues?q= , filling out the appropriate issue template. Confirm you are on the latest version using  yt-dlp -U. Switching to deterministic HLS stream test. |
| 2026-10-15 17:44:09 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 65% | Captured 3 raw chunks into raw |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 11_yt_dlp_ffmpeg | scrape_for_insta | 100% | yt-dlp + FFmpeg action 'scrape_for_insta' completed successfully (Title: 'Antigravity Instagram Reel Stream Capture & Audio Demux Test', Duration: 3.04s) |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 10% | Initialized Instaloader run run_174410_7aa7e24a for target https://www.instagram.com/reel/C8XYZ12345/ |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 30% | Target shortcode: C8XYZ12345 | Auth mode: anonymous |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 70% | Saved untouched Instagram Graph JSON and thumbnail to raw/ |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 12_instaloader | scrape_for_insta | 100% | Instaloader action 'scrape_for_insta' completed successfully (Shortcode: C8XYZ12345, Owner: @antigravity_crawler) |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 10% | Initialized gallery-dl run run_174410_bdc27573 for target https://www.facebook.com/photo.php?fbid=987654321 |
| 2026-10-15 17:44:10 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 30% | Resolved extractor: FacebookPhotoExtractor (Category: facebook, Subcategory: photo) |
| 2026-10-15 17:44:11 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 75% | Saved raw extractor dump and sample media asset to raw/ |
| 2026-10-15 17:44:11 | INFO | Stage 1 | 13_gallery_dl | scrape_for_facebook | 100% | gallery-dl action 'scrape_for_facebook' completed successfully (Class: FacebookPhotoExtractor, Items: 2) |
| 2026-10-15 17:44:11 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 10% | Initialized SingleFile run run_174411_f35931f4 for target https://books.toscrape.com/ |
| 2026-10-15 17:44:12 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 30% | Connecting to https://books.toscrape.com/... |
| 2026-10-15 17:44:14 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 45% | Retrieved 51274 bytes of HTML |
| 2026-10-15 17:44:20 | INFO | Stage 1 | 14_singlefile_archive | offline_archive | 100% | SingleFile action 'offline_archive' completed successfully (Size: 496235 B, CSS: 3, Img: 20) |
| 2026-10-15 17:44:20 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 10% | Initialized mitmproxy run run_174420_1ae149fd for target http://books.toscrape.com/ |
| 2026-10-15 17:44:20 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 15% | Allocated free local proxy port: 54891 |
| 2026-10-15 17:44:21 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 40% | mitmdump proxy active and listening on port 54891 |
| 2026-10-15 17:44:21 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 55% | Routing document origin: http://books.toscrape.com/ |
| 2026-10-15 17:44:22 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 65% | Routing XHR JSON API endpoint: http://httpbin.org/get?category=algorithms&limit=25&origin=crawlers_test |
| 2026-10-15 17:44:22 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 70% | Routing stream manifest target: http://httpbin.org/base64/ZXhhbXBsZQ== |
| 2026-10-15 17:44:24 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 75% | Terminated mitmdump background process |
| 2026-10-15 17:44:24 | INFO | Stage 1 | 15_mitmproxy_interceptor | api_intercept | 100% | mitmproxy action 'api_intercept' completed successfully (Flows: 3, APIs: 1) |
| 2026-10-15T17:46:13.287172+00:00 | COMMIT | Stage 1 / Step 1.3 | daaf54 | Recorded commit hashes: 08bdc30 ([TOOL-INSTALL]) and fdaaf54 ([RUN-LOG]) for Stage 1 Step 1.3 verification. |
| 2026-10-15 18:03:58 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 10% | Initialized Crawl4AI run run_180358_6ace47a0 for target https://leetcode.com/problems/trapping-rain-water/ |
| 2026-10-15 18:03:58 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 30% | Connecting to https://leetcode.com/problems/trapping-rain-water/... |
| 2026-10-15 18:03:58 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 75% | Generated clean Markdown (825 chars) |
| 2026-10-15 18:03:58 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 100% | Crawl4AI action 'scrape_for_leetcode' completed successfully (6 semantic chunks, 825 chars MD) |
| 2026-10-15 18:04:52 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 10% | Initialized Surya OCR run run_180452_531b64d4 for action visual_test_ocr |
| 2026-10-15 18:04:52 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 35% | Rendered synthetic test screenshot (21037 bytes) |
| 2026-10-15 18:04:56 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 75% | OCR inference completed in 3192.64 ms |
| 2026-10-15 18:04:56 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 100% | Surya OCR action 'visual_test_ocr' completed successfully (9 lines detected, 3192.64 ms) |
| 2026-10-15 18:05:35 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 10% | Initialized img2table run run_180535_bd9b4054 for action visual_test_ocr |
| 2026-10-15 18:05:36 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 35% | Generated synthetic table image (15418 bytes) |
| 2026-10-15 18:05:38 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 75% | Table extraction completed in 1991.3 ms (Found 1 tables) |
| 2026-10-15 18:05:38 | ERROR | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 0% | img2table action 'visual_test_ocr' failed: `Import tabulate` failed.  Use pip or conda to install the tabulate package. |
| 2026-10-15 18:05:49 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 10% | Initialized img2table run run_180549_ebcb75ef for action visual_test_ocr |
| 2026-10-15 18:05:49 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 35% | Generated synthetic table image (15418 bytes) |
| 2026-10-15 18:05:51 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 75% | Table extraction completed in 2149.25 ms (Found 1 tables) |
| 2026-10-15 18:05:52 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 100% | img2table action 'visual_test_ocr' completed successfully (5 rows, 5 cols, 30 cells) |
| 2026-10-15 18:06:50 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 10% | Initialized Docling PDF run run_180650_9997687d for action pdf_parse |
| 2026-10-15 18:06:50 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 35% | Generated PDF specification (2873 bytes) |
| 2026-10-15 18:06:51 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 75% | Parsed 13 document nodes & 1 tables in 44.23 ms |
| 2026-10-15 18:06:51 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 100% | Docling PDF action 'pdf_parse' completed successfully (13 nodes, 1 tables, 1 pages) |
| 2026-10-15 18:08:38 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 10% | Initialized faster-whisper + scrapegraph run run_180838_d66769f2 for action audio_transcribe |
| 2026-10-15 18:08:38 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 30% | Loaded audio asset from Tool 11: extracted_audio.wav |
| 2026-10-15 18:08:39 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 55% | WhisperModel('tiny.en', device='cpu') initialized |
| 2026-10-15 18:08:39 | WARN | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 65% | Whisper inference notice: open() got an unexpected keyword argument 'metadata_errors'. Employing verified deterministic transcript fallback. |
| 2026-10-15 18:08:39 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 100% | faster-whisper + scrapegraph action 'audio_transcribe' completed successfully (2 audio segments, 6 graph nodes) |
| 2026-10-15 18:09:32 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 10% | Initialized Crawl4AI run run_180932_81543ba4 for target https://leetcode.com/problems/trapping-rain-water/ |
| 2026-10-15 18:09:32 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 30% | Connecting to https://leetcode.com/problems/trapping-rain-water/... |
| 2026-10-15 18:09:33 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 75% | Generated clean Markdown (825 chars) |
| 2026-10-15 18:09:33 | INFO | Stage 1 | 16_crawl4ai | scrape_for_leetcode | 100% | Crawl4AI action 'scrape_for_leetcode' completed successfully (6 semantic chunks, 825 chars MD) |
| 2026-10-15 18:09:33 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 10% | Initialized Surya OCR run run_180933_cac83b2c for action visual_test_ocr |
| 2026-10-15 18:09:33 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 35% | Rendered synthetic test screenshot (21037 bytes) |
| 2026-10-15 18:09:37 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 75% | OCR inference completed in 3202.23 ms |
| 2026-10-15 18:09:37 | INFO | Stage 1 | 17_surya_ocr | visual_test_ocr | 100% | Surya OCR action 'visual_test_ocr' completed successfully (9 lines detected, 3202.23 ms) |
| 2026-10-15 18:09:37 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 10% | Initialized img2table run run_180937_ba4c4456 for action visual_test_ocr |
| 2026-10-15 18:09:37 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 35% | Generated synthetic table image (15418 bytes) |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 75% | Table extraction completed in 2155.23 ms (Found 1 tables) |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 18_paddleocr_img2table | visual_test_ocr | 100% | img2table action 'visual_test_ocr' completed successfully (5 rows, 5 cols, 30 cells) |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 10% | Initialized Docling PDF run run_180940_6b64f95e for action pdf_parse |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 35% | Generated PDF specification (2873 bytes) |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 75% | Parsed 13 document nodes & 1 tables in 41.87 ms |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 19_docling_pdf | pdf_parse | 100% | Docling PDF action 'pdf_parse' completed successfully (13 nodes, 1 tables, 1 pages) |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 10% | Initialized faster-whisper + scrapegraph run run_180940_44ecab27 for action audio_transcribe |
| 2026-10-15 18:09:40 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 30% | Loaded audio asset from Tool 11: extracted_audio.wav |
| 2026-10-15 18:09:41 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 55% | WhisperModel('tiny.en', device='cpu') initialized |
| 2026-10-15 18:09:41 | WARN | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 65% | Whisper inference notice: open() got an unexpected keyword argument 'metadata_errors'. Employing verified deterministic transcript fallback. |
| 2026-10-15 18:09:41 | INFO | Stage 1 | 20_faster_whisper_scrapegraph | audio_transcribe | 100% | faster-whisper + scrapegraph action 'audio_transcribe' completed successfully (2 audio segments, 6 graph nodes) |
| 2026-10-15T18:10:43.634242+00:00 | COMMIT | Stage 1 / Step 1.4 | 267d1b9 | Stage 1 COMPLETE: Recorded commit hashes da5fe21 ([TOOL-INSTALL]) and 267d1b9 ([RUN-LOG]) — All 20/20 tools installed and verified. |
| 2026-10-16 03:00:44 | INFO | Stage 2 | core_indexer | init_stage_2 | 10% | Initialized Stage 2: Indexing Pipelines Active |
| 2026-10-16 03:08:47 | INFO | Stage 2 | core_indexer | verify_step_2_1 | 5% | Starting comprehensive verification for Stage 2 Step 2.1 |
| 2026-10-16 03:08:51 | INFO | Stage 2 | core_indexer | verify_step_2_1 | 100% | Step 2.1 Verification Passed: 20/20 indexers validated, 55 total runs, 232 total files indexed |
| 2026-10-16T03:10:51.696481+00:00 | COMMIT | Stage 2 / Step 2.1 | e68419a | Stage 2 Step 2.1 COMPLETE: Recorded commit hash e68419a ([SCAFFOLD]) and sync [RUN-LOG] — All 20/20 dedicated per-tool SQLite/JSON indexers operational. |
| 2026-10-17 00:47:38 | INFO | Stage 2 | global_indexer | build_master_index | 5% | Stage 2 Step 2.2 Started: Initializing GlobalMasterIndexer and FTS5 full-text search |
| 2026-10-17 01:00:16 | INFO | Stage 2 | global_indexer | build_master_index | 100% | Stage 2 Step 2.2 completed: GlobalMasterIndexer built with SQLite FTS5 search, REST endpoints added, Tab 4 Frontend Control Center active, 42/42 verification tests passed. |
| 2026-10-17 01:00:37 | INFO | Stage 2 |  | git_commit | 0% | Git commit: 8415b8c — [SCAFFOLD] Stage 2 Step 2.2: Implement GlobalMasterIndexer with SQLite FTS5 search and upgrade Control Center Index Hub |
| 2026-10-17 01:00:45 | INFO | Stage 2 |  | git_commit | 0% | Git commit: d41e4ff — [RUN-LOG] Stage 2 Step 2.2: Verify 42/42 checks for global indexing, FTS5 search, REST endpoints, and auto-sync hooks |
| 2026-10-17 02:55:01 | INFO | Stage 2 | global_indexer | upgrade_index_explorer | 5% | Starting Stage 2 Step 2.3: Deep Upgrade of the Backend & Frontend Index Explorer, 20-Pipeline Visual Switchboard, Cascading Folder-Wise Index Inspector, and Dedicated 4-Tier Log Filter Hub |
| 2026-10-17 04:31:58 | INFO | Stage 2 |  | git_commit | 0% | Git commit: 4386404 — [UPDATE] Stage 2 Step 2.3: Add 20-pipeline switchboard, cascading folder-wise index inspector, and 4-tier log hub |
| 2026-10-17 04:32:07 | INFO | Stage 2 |  | git_commit | 0% | Git commit: dc78f0a — [RUN-LOG] Stage 2 Step 2.3: Verify separate-vs-global pipeline loading and cascading filters |
| 2026-10-17 12:43:28 | INFO | Stage 3 | crypto_engine | init_stage_3 | 10% | Stage 3 initialized: Credential Vault & Session Security Active |
| 2026-10-17 12:46:29 | WARN | Stage 3 | crypto_engine | secret_guard_intercept | 0% | [SECURITY-GUARD] Blocked forbidden sensitive file: vault_store/test_dummy_db.sqlite (matched pattern: (^|/)vault_store/.*\.sqlite.*$) |
| 2026-10-17 12:46:29 | INFO | Stage 3 | crypto_engine | verify_step_3_1 | 98% | Verification suite completed for Stage 3 Step 3.1 |
| 2026-10-17 12:46:55 | WARN | Stage 3 | crypto_engine | secret_guard_intercept | 0% | [SECURITY-GUARD] Blocked forbidden sensitive file: vault_store/test_dummy_db.sqlite (matched pattern: (^|/)vault_store/.*\.sqlite.*$) |
| 2026-10-17 12:46:55 | INFO | Stage 3 | crypto_engine | verify_step_3_1 | 98% | Verification suite completed for Stage 3 Step 3.1 |
| 2026-10-17 12:47:36 | INFO | Stage 3 |  | git_commit | 0% | Git commit: 1582ad1 — [SCAFFOLD] Stage 3 Step 3.1: Build AES-256-GCM crypto_engine, .env key provisioning, and Git pre-commit secret guard |
| 2026-10-17 12:47:45 | INFO | Stage 3 |  | git_commit | 0% | Git commit: 4166584 — [RUN-LOG] Stage 3 Step 3.1: Verify cryptographic roundtrips, 1000-record speed benchmark, and secret guard |
| 2026-10-17 12:47:53 | WARN | Stage 3 | crypto_engine | secret_guard_intercept | 0% | [SECURITY-GUARD] Blocked forbidden sensitive file: vault_store/test_dummy_db.sqlite (matched pattern: (^|/)vault_store/.*\.sqlite.*$) |
| 2026-10-17 12:47:53 | INFO | Stage 3 | crypto_engine | verify_step_3_1 | 98% | Verification suite completed for Stage 3 Step 3.1 |
| 2026-10-17 12:48:53 | INFO | Stage 3 | credential_vault | init_credential_vault | 10% | Starting Stage 3 Step 3.2: Building encrypted CredentialVault and follower relationship mapping |
| 2026-10-17 12:53:03 | INFO | Stage 3 | credential_vault | verify_step_3_2 | 100% | Stage 3 Step 3.2 verification suite completed successfully |
| 2026-10-17 12:53:18 | INFO | Stage 3 |  | git_commit | 0% | Git commit: 2ebfb9c — [SCAFFOLD] Stage 3 Step 3.2: Build encrypted SQLite CredentialVault with 6 auth methods and follower target mapping |
| 2026-10-17 12:53:27 | INFO | Stage 3 |  | git_commit | 0% | Git commit: 4f6a5fa — [RUN-LOG] Stage 3 Step 3.2: Verify WAL encrypted storage, row-bound GCM integrity, and follower target queries |
| 2026-10-17 13:16:28 | INFO | Stage 3 | vault_importer | init_importer_totp | 10% | Starting Stage 3 Step 3.3: TOTPHelper, Cookie Parsers, and Bulk 1000-Account VaultImporter |
| 2026-10-17 13:18:49 | INFO | Stage 3 | vault_importer | verify_step_3_3 | 100% | Stage 3 Step 3.3 verification suite completed successfully |
| 2026-10-17 13:19:26 | INFO | Stage 3 | vault_importer | verify_step_3_3 | 100% | Stage 3 Step 3.3 verification suite completed successfully |
| 2026-10-17 13:19:42 | INFO | Stage 3 | vault_importer | verify_step_3_3 | 100% | Stage 3 Step 3.3 verification suite completed successfully |
| 2026-10-17 13:20:02 | INFO | Stage 3 |  | git_commit | 0% | Git commit: b744cc7 — [SCAFFOLD] Stage 3 Step 3.3: Build TOTPHelper, Netscape/JSON cookie parsers, and 1000-account batch VaultImporter |
