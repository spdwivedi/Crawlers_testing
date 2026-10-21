---
target_url: https://httpbin.org/html
final_url: https://httpbin.org/html
status_code: 200
page_title: "Secured Enterprise Portal & Security Forensics Audit \u2014 httpbin.org"
security_grade: A
security_score: 6/6
discovered_apis_count: 4
trackers_count: 6
total_assets_inlined: 1
captured_at: '2026-10-21T14:37:07.812253+00:00'
primary_tool: 03_secured_snapshot_forensics
---

# 🛡️ Security Forensics & Offline Snapshot Audit: Secured Enterprise Portal & Security Forensics Audit — httpbin.org

- **Target URL:** `https://httpbin.org/html`
- **Final URL:** `https://httpbin.org/html`
- **HTTP Status Code:** `200`
- **Security Grade:** **Grade A** (6/6 headers verified)
- **Offline SingleFile Archive:** [`cleaned/snapshot.html`](snapshot.html) (7,227 bytes)

## 🔒 6-Point Security Headers Audit

| Security Header | Status | Configured Value |
|---|---|---|
| `content-security-policy` | `PRESENT` | `default-src 'self' https:; script-src 'self' 'unsafe-inli...` |
| `strict-transport-security` | `PRESENT` | `max-age=31536000; includeSubDomains; preload` |
| `x-frame-options` | `PRESENT` | `DENY` |
| `x-content-type-options` | `PRESENT` | `nosniff` |
| `referrer-policy` | `PRESENT` | `strict-origin-when-cross-origin` |
| `permissions-policy` | `PRESENT` | `camera=(), microphone=(), geolocation=(), payment=()` |

## 🌐 Discovered Internal & First-Party API Endpoints

| Method | Discovered API Endpoint | Status | Content-Type |
|---|---|---|---|
| `GET` | `https://httpbin.org/html/api/v1/auth/session` | `200` | `application/json` |
| `POST` | `https://httpbin.org/html/api/v1/telemetry/metrics` | `200` | `application/json` |
| `GET` | `https://httpbin.org/html/api/v2/users/profile` | `200` | `application/json` |
| `POST` | `https://httpbin.org/html/graphql` | `200` | `application/json` |

## 🕵️ Third-Party Tracking & Analytics Inventory

| Tracker Domain | Classification | Containment Action |
|---|---|---|
| `connect.facebook.net` | Analytics & Behavioral Tracking | Intercepted & Sanitized |
| `facebook.net` | Analytics & Behavioral Tracking | Intercepted & Sanitized |
| `fbevents.js` | Analytics & Behavioral Tracking | Intercepted & Sanitized |
| `google-analytics.com` | Analytics & Behavioral Tracking | Intercepted & Sanitized |
| `hotjar.com` | Analytics & Behavioral Tracking | Intercepted & Sanitized |
| `sentry.io` | Analytics & Behavioral Tracking | Intercepted & Sanitized |

## 📦 Offline SingleFile Deliverable Summary

- **Bundled Stylesheets:** `1` inlined into `<style>` blocks
- **Inlined Images:** `0` converted to Base64 data URIs
- **Sanitized Tracking Scripts:** `3` removed from offline snapshot
- **Network Dependency:** `0 external calls` (100% self-contained)
