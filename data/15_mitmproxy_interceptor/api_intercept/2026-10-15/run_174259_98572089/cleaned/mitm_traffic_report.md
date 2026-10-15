# 🕵️ mitmproxy Wire Interception & Hidden API Discovery Report

**Tool:** `15_mitmproxy_interceptor`  
**Action:** `api_intercept`  
**Proxy Port:** `127.0.0.1:57240`  
**Intercepted Packets:** **3**  
**Discovered APIs:** **1**  
**Timestamp:** 2026-10-15 17:43:03 UTC

---

## 🔍 Discovered REST & GraphQL APIs
| Method | Endpoint URL | Status | Content-Type | Auth Headers Intercepted |
|--------|--------------|--------|--------------|--------------------------|
| `GET` | `http://httpbin.org/get?category=algorithms&limit=25&origin=crawlers_test` | 200 | `application/json` | Authorization |


---

## 📡 Media Stream Manifests On Wire
| Manifest URL | Status | Content-Type |
|--------------|--------|--------------|
| - | No media stream manifests captured | - |


---

## 🛡️ Observed Origin Security Policies
| Security Header | Observed Value(s) |
|-----------------|-------------------|
| `server` | `gunicorn/19.9.0` |
| `access-control-allow-origin` | `*` |

---

## 📁 Output Artifacts
- **Raw Wire Flows (JSONL):** `raw/intercepted_flows.jsonl` (6.18 KB)
- **Discovered APIs Catalog:** `cleaned/discovered_apis.json`
