# Antigravity Control Center Frontend (`frontend/`)

The `frontend/` directory contains the responsive, dark-mode single-page dashboard serving as the real-time operational interface for `Crawlers_testing`.

---

## 🎨 Interface Structure & Tabs

- **Live Sticky HUD Bar:** Fixed top bar displaying active Stage, Step, Tool, Elapsed Seconds, circular progress percentage, and dual 60 FPS HTML5 Canvas graphs tracking worker CPU usage % and RAM consumption in MB.
- **Tab 1: Telemetry Dashboard & Worker Monitor:** Real-time visual timeline of system milestones, task parameters, and active worker process PIDs (`psutil`).
- **Tab 2: 20-Tool Execution Hub:** Execution cards for all 20 crawling engines, supporting custom target URLs, scraping actions, and live JSON response inspection.
- **Tab 3: Dual-Index Search Engine:** Full-text keyword and phrase search across all Bronze/Silver artifacts and 4-tier logs, featuring Okapi BM25 ranking, yellow keyword highlighting (`mark.fts-hl`), and snippet previews.
- **Tab 4: Real-Time 4-Tier Log Streamer:** High-performance virtual-scrolling log grid connected via WebSocket (`/ws/logs`) with real-time log-level and stage filtering.
- **Tab 5: 🔐 Credential Vault & Session Manager:**
  - 6-card KPI ribbon (Total Accounts, Active Ready, Cooldown Quarantine, High Risk, Private Target Coverage, Protected 2FA Seeds).
  - Masked accounts table with health score indicators and action triggers (Copy TOTP, Quarantine/Release, Delete).
  - Followed private targets list showing access coverage.
  - 20-Tool Auth Router Sandbox testing ephemeral cookie injection.
  - Modals: **Add Encrypted Account**, **Bulk Import** (with 50-account sample seed generator), and **Browser Session Capture** (interactive or headless).
  - Floating, animated **Live 2FA TOTP Toast** with second-by-second countdown bars.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|:---:|:---|
| `Alt + 1` | Switch to Tab 1: Telemetry Dashboard |
| `Alt + 2` | Switch to Tab 2: 20-Tool Execution Hub |
| `Alt + 3` | Switch to Tab 3: Dual-Index Search Engine |
| `Alt + 4` | Switch to Tab 4: 4-Tier Log Streamer |
| `Alt + 5` | Switch to Tab 5: 🔐 Credential Vault & Sessions |
| `Escape` | Close any open modal dialog |

---

## 🛠️ File Reference

- `index.html`: Semantic HTML5 layout and modal definitions.
- `styles.css`: Dark-mode CSS styling using CSS Grid, Flexbox, custom scrollbars, and badge typography.
- `app.js`: Pure vanilla JavaScript controller establishing WebSocket reconnect loops, handling tab switches, and executing asynchronous REST requests.
