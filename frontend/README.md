# Antigravity Control Center Frontend (`frontend/`)

The `frontend/` directory hosts the responsive, dark-mode single-page dashboard serving as the real-time operational interface, command center, and diagnostic workstation for `Crawlers_testing`.

---

## 🎨 Architectural Overview

The frontend is architected as a lightweight, zero-build vanilla JavaScript and HTML5 application engineered for maximum rendering performance, low memory footprint, and high-frequency WebSocket streaming:
- **No External Bundler Required:** Runs directly from static files served by FastAPI at `/` (`frontend/index.html`).
- **Real-Time State Synchronization:** Subscribes to `/ws/telemetry` at 1 Hz for global execution state (`logs/global/live_state.json`) and `/ws/logs` for real-time log tailing.
- **Dual HTML5 Canvas 60 FPS HUD Monitors:** Renders hardware-accelerated time-series sparklines for worker CPU load % and RAM RSS consumption (MB) without DOM reflow penalties.
- **Fast Tab Switching & Deep Linking:** Pure DOM tab navigation preserving active form inputs, filter selections, and scroll positions across tabs.

---

## 🖥️ Detailed Guide to All 8 Dashboard Tabs

```
+===================================================================================================================+
|  HUD BAR: [Stage: Master Verification]  [Step: Final Audit]  [Elapsed: 14.2s]  [Prog: 100%]  [Workers: 4]         |
|  Canvas CPU Monitor: [||||||||||  12%]      Canvas RAM Monitor: [||||||||||||||||  196 MB]                        |
+===================================================================================================================+
| [Tab 1: Live Execution] [Tab 2: Tool Roster] [Tab 3: Data Explorer] [Tab 4: Index & Search Hub]                   |
| [Tab 5: 🔐 Credential Vault] [Tab 6: ⚙ Working Ways & Arena] [Tab 7: 🧪 Real Pipelines] [Tab 8: 📊 Benchmarks]    |
+===================================================================================================================+
```

### Tab 1: Live Execution (`id="tab-live"`, Shortcut: `Alt + 1`)
- **Primary Role:** Operational cockpit displaying the live execution stream and milestone timeline.
- **Components:**
  - *Milestone Step Progress Bar:* Circular and linear percentage indicators tracking sub-step progression ($0\% \to 100\%$).
  - *Worker Process Inspector:* Dynamic table listing active worker PIDs, process start times, and CPU/RAM consumption via `psutil`.
  - *Real-Time Log Terminal:* Virtual-scrolling console streaming live diagnostic lines with level badges (`INFO`, `WARNING`, `ERROR`, `SUCCESS`).

### Tab 2: Tool Roster (`id="tab-tools"`, Shortcut: `Alt + 2`)
- **Primary Role:** Interactive testbed and configuration hub for all 20 specialized crawling engines.
- **Components:**
  - *20 Engine Execution Cards:* Grouped across Batches 1 to 4 with mechanism badges (`JA4 TLS`, `C-DOM`, `Stealth CDP`, `Document AI`).
  - *Parameter Configuration Modal:* Custom target URL input, action selector (`scrape_for_leetcode`, `secured_page_origin`, etc.), and Human Mode toggle.
  - *Live JSON Response Inspector:* Syntax-highlighted response pane displaying status, elapsed time, raw bytes, and domain metrics.

### Tab 3: Data Explorer (`id="tab-explorer"`, Shortcut: `Alt + 3`)
- **Primary Role:** Medallion Data Lake file browser inspecting Bronze, Silver, and Provenance artifacts.
- **Components:**
  - *Hierarchical Directory Tree:* Visual drill-down through `data/<tool_id>/<action>/<date>/<run_id>/`.
  - *Artifact Splitter:* Dedicated subviews for Bronze `raw/` payloads, Silver `cleaned/` normalized outputs, and `logs/action_run.jsonl`.
  - *Provenance Inspector:* Side-by-side display of `run_manifest.json` showing Git commit hash, SHA-256 file digests, and execution metadata.

### Tab 4: Index & Search Hub (`id="tab-index"`, Shortcut: `Alt + 4`)
- **Primary Role:** Unified full-text search engine querying both artifacts and multi-tier logs.
- **Components:**
  - *Okapi BM25 Search Bar:* Full-text search querying `global_master_index.sqlite` (`fts_artifacts` and `fts_logs`).
  - *Keyword Highlighter:* Yellow keyword highlighting (`mark.fts-hl`) across search snippets and previews.
  - *Tool Database Selector:* Direct inspection of any of the 20 isolated SQLite databases in `index_store/tool_indexes/`.

### Tab 5: Credential Vault (`id="tab-vault"`, Shortcut: `Alt + 5`)
- **Primary Role:** Zero-plaintext cryptographic credential manager, session store, and 2FA controller.
- **Components:**
  - *6-Card KPI Ribbon:* Total Accounts, Active Ready, Cooldown Quarantine, High Risk, Target Coverage, Protected 2FA Seeds.
  - *Masked Accounts Table:* Health score meters, target domain pills, and action buttons (`Copy TOTP`, `Quarantine`, `Delete`).
  - *Live 2FA TOTP Toast:* Floating toast emitting live 6-digit numeric codes with second-by-second countdown progress bars.
  - *Modals:* **Add Account**, **Bulk Importer** (with 50-account sample generator), and **Browser Session Capture**.

### Tab 6: Working Ways & Safe Arena (`id="tab-working-ways"`, Shortcut: `Alt + 6`)
- **Primary Role:** Execution studio for the 3 Working Ways (Human Mode, Safe Arena, Task Router).
- **Components:**
  - *Human Simulation Studio:* Interactive sliders for Gaussian typing speed, reaction pauses, reading delays, and Bezier trajectories.
  - *Safe Arena Tournament Studio:* Multi-tool tournament launcher, staggered concurrency offset sliders, auto-kill watchdog timer, and leaderboard view.
  - *Precision Task Router Studio:* Chaining studio configuring primary scraper, fallback engines, and enrichment handoffs.

### Tab 7: Real Pipelines (`id="tab-real-pipelines"`, Shortcut: `Alt + 7`)
- **Primary Role:** Production task pipeline control plane and Silver-Tier deliverable inspector.
- **Components:**
  - *4 Pipeline Launchers:* LeetCode Archiver, Social Media & Whisper, Secured Snapshot Forensics, Multimodal Auto-Resolver.
  - *Multi-Format Deliverable Viewer:* Renderers for CommonMark Markdown, Audio waveforms (`.wav`/`.mp3`), self-contained HTML snapshots, and code templates.
  - *Silver Contract Compliance Matrix:* Pydantic schema validation status and SHA-256 integrity confirmation.

### Tab 8: Benchmarks & Lab (`id="tab-benchmarks-exporter"`, Shortcut: `Alt + 8`)
- **Primary Role:** Performance matrix lab, chaos resilience testbed, and standalone project packager.
- **Components:**
  - *Master Benchmark Lab:* 20-tool tournament battery launcher, radar spider chart (Speed, Richness, Stealth, Memory, Reliability), and leaderboard.
  - *Chaos & Resilience Stress Lab:* Interactive trigger cards for HTTP 429 backoff, DOM mutation fuzzing, socket chaos, and schema fuzzing.
  - *Standalone Project Exporter:* Scraper packaging controls, signed Data Lake ZIP bundler, and Dockerized microservice generator.

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Target Destination |
|:---:|:---|
| `Alt + 1` | Tab 1: Live Execution & Real-Time Stream |
| `Alt + 2` | Tab 2: Tool Roster (20 Engine Hub) |
| `Alt + 3` | Tab 3: Data Explorer (Data Lake Browser) |
| `Alt + 4` | Tab 4: Index & Search Hub (FTS5 BM25) |
| `Alt + 5` | Tab 5: 🔐 Credential Vault & Auth Router |
| `Alt + 6` | Tab 6: ⚙ Working Ways & Safe Arena Studio |
| `Alt + 7` | Tab 7: 🧪 Real Pipelines & Cleaned Inspector |
| `Alt + 8` | Tab 8: 📊 Benchmarks, Chaos Lab & Exporter |
| `Escape` | Close any active modal dialog or preview panel |

---

## 📁 Source File Breakdown

- [`index.html`](file:///d:/Project_Files/Crawlers_testing/frontend/index.html): Semantic HTML5 markup, SVG iconography, modal dialogues, and tab container elements.
- [`styles.css`](file:///d:/Project_Files/Crawlers_testing/frontend/styles.css): High-performance dark-mode stylesheet utilizing CSS Grid, Flexbox, custom scrollbars, and variable color palettes.
- [`app.js`](file:///d:/Project_Files/Crawlers_testing/frontend/app.js): Vanilla JavaScript controller handling WebSocket reconnection loops, Canvas HUD drawing, REST calls, and DOM updates.
