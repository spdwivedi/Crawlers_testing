# Patchright Anti-Bot & Stealth Evasion Report

- **Tool ID:** `07_patchright`
- **Target URL:** `https://quotes.toscrape.com/js/`
- **Page Title:** Quotes to Scrape
- **Stealth Evasion Score:** **45 / 100**
- **Execution Latency:** 8184.97 ms

## Bot Detection Vector Audit

| Vector | Observed Value | Status |
|---|---|---|
| `navigator.webdriver` | `False` | **PASS** |
| `window.chrome` Object | `Absent` | **WARN** |
| `navigator.plugins` Count | `0` | **WARN** |
| WebGL Renderer | `ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)` | **FAIL** |
| CDP Runtime Leak | `Undetected` | **PASS** |

## Environment Fingerprint
- **User Agent:** `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36`
- **Languages:** `en-US`
- **Hardware Concurrency:** 28 cores
- **Device Memory:** 32 GB
- **Raw Probe Evidence:** `stealth_probe.json` (684 bytes)
- **Visual Capture:** `stealth_check.png` (102680 bytes)
