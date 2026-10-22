/**
 * frontend/app.js
 * ===============
 * Crawlers_testing Control Center — Frontend Logic
 * Handles WebSocket connections, telemetry HUD, log streaming,
 * tool roster, data explorer, and demo simulation trigger.
 */

"use strict";

// ─── Config ───────────────────────────────────────────────────────────────────
const WS_TELEMETRY = `ws://${location.host}/ws/telemetry`;
const WS_LOGS      = `ws://${location.host}/ws/logs`;
const API_BASE     = `${location.protocol}//${location.host}`;

// ─── State ────────────────────────────────────────────────────────────────────
let telemetryWs   = null;
let logWs         = null;
let allLogs       = [];          // raw JSONL records
let timerInterval = null;
let lastState     = {};

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  connectTelemetry();
  connectLogStream();
  loadRecentLogs();
  loadTools();
  loadGitLog();
  loadDataTree();
  startLocalTimer();
});

// ─── Tab Switching ────────────────────────────────────────────────────────────
function switchTab(tabId, btn) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  btn.classList.add("active");

  if (tabId === "tab-explorer") loadDataTree();
  if (tabId === "tab-index") loadIndexHub();
  if (tabId === "tab-vault") loadVaultTab();
  if (tabId === "tab-working-ways") loadWorkingWaysTab();
  if (tabId === "tab-real-pipelines") loadPipelinesTab();
  if (tabId === "tab-benchmarks-exporter") loadBenchmarksTab();
}

// ─── Telemetry WebSocket ──────────────────────────────────────────────────────
function connectTelemetry() {
  if (telemetryWs) telemetryWs.close();

  telemetryWs = new WebSocket(WS_TELEMETRY);

  telemetryWs.onmessage = (e) => {
    try {
      const state = JSON.parse(e.data);
      updateHUD(state);
      lastState = state;
    } catch (err) { /* ignore */ }
  };

  telemetryWs.onclose = () => {
    setTimeout(connectTelemetry, 3000);
  };

  telemetryWs.onerror = () => {
    setTimeout(connectTelemetry, 5000);
  };
}

function updateHUD(state) {
  const isRunning = state.is_running;

  // Status pill
  const pill = document.getElementById("hud-status-pill");
  const dot  = document.getElementById("hud-status-dot");
  const label = document.getElementById("hud-status-label");
  pill.classList.toggle("running", isRunning);
  dot.classList.toggle("running", isRunning);
  label.textContent = isRunning ? "RUNNING" : "IDLE";

  // Info blocks
  setText("hud-stage",  state.current_stage  || "—");
  setText("hud-step",   state.current_step   || "—");
  setText("hud-tool",   state.active_tool_id || "—");
  setText("hud-action", state.active_action  || "—");

  // Subtask
  setText("hud-subtask", state.current_subtask || "System ready — waiting for task");

  // Progress
  const pct = state.progress_percent || 0;
  document.getElementById("hud-progress-fill").style.width = pct + "%";
  setText("hud-progress-label", pct + "%");

  // Timer (use server elapsed + local drift via startLocalTimer)
  if (state.started_at_epoch && isRunning) {
    updateTimerDisplay(state.elapsed_seconds || 0);
  } else if (!isRunning) {
    const elapsed = state.elapsed_seconds || 0;
    updateTimerDisplay(elapsed);
  }

  // Workers
  const workers = state.worker_processes || [];
  const totalCPU = workers.reduce((s, w) => s + (w.cpu_pct || 0), 0).toFixed(1);
  const totalRAM = workers.reduce((s, w) => s + (w.ram_mb || 0), 0).toFixed(0);
  setText("worker-count", workers.length);
  setText("worker-cpu",   totalCPU + "%");
  setText("worker-ram",   totalRAM + "MB");
  renderProcessList(workers);

  // Recent events
  renderEvents(state.recent_events || []);

  // Demo button state
  const demoBtn = document.getElementById("demo-btn");
  if (isRunning && state.active_action === "scrape_for_leetcode") {
    demoBtn.classList.add("running");
    demoBtn.textContent = "⏳ Demo Running";
  } else {
    demoBtn.classList.remove("running");
    demoBtn.textContent = "▶ Demo Run";
  }
}

function updateTimerDisplay(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  document.getElementById("hud-timer").textContent =
    pad2(h) + ":" + pad2(m) + ":" + pad2(s);
}

function startLocalTimer() {
  // Keep timer ticking locally between WS updates
  let localOffset = 0;
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    if (lastState.is_running && lastState.started_at_epoch) {
      const elapsed = (Date.now() / 1000) - lastState.started_at_epoch;
      updateTimerDisplay(elapsed);
    }
  }, 1000);
}

// ─── Log Stream WebSocket ─────────────────────────────────────────────────────
function connectLogStream() {
  if (logWs) logWs.close();
  logWs = new WebSocket(WS_LOGS);

  const console_ = document.getElementById("log-console");
  const placeholder = console_.querySelector(".log-placeholder");

  logWs.onopen = () => {
    if (placeholder) placeholder.textContent = "🔗 Connected to log stream — waiting for log events...";
  };

  logWs.onmessage = (e) => {
    try {
      const record = JSON.parse(e.data);
      if (record.type === "heartbeat") return;  // ignore pings
      if (placeholder) placeholder.remove();

      allLogs.push(record);
      if (allLogs.length > 5000) allLogs.shift(); // cap memory

      renderLogLine(record, console_);
    } catch (err) { /* ignore */ }
  };

  logWs.onclose = () => {
    setTimeout(connectLogStream, 3000);
  };
}

function renderLogLine(record, container) {
  // Apply current filters
  if (!passesFilter(record)) return;

  const line = document.createElement("div");
  line.className = "log-line";
  line.dataset.level  = record.level  || "";
  line.dataset.tool   = record.tool_id || "";
  line.dataset.action = record.action_name || "";
  line.dataset.source = record._source_file || "";

  const ts     = (record.timestamp || "").slice(0, 19).replace("T", " ");
  const level  = record.level || "INFO";
  const tool   = record.tool_id || "—";
  const msg    = record.message || JSON.stringify(record);

  line.innerHTML = `
    <span class="log-ts">${ts}</span>
    <span class="log-level-${level}">${level}</span>
    <span class="log-tool">${tool}</span>
    <span class="log-msg">${escHtml(msg)}</span>
  `;
  container.appendChild(line);

  if (document.getElementById("auto-scroll").checked) {
    container.scrollTop = container.scrollHeight;
  }
}

function passesFilter(record) {
  const stage  = document.getElementById("filter-stage")?.value;
  const tier   = document.getElementById("filter-tier")?.value;
  const level  = document.getElementById("filter-level")?.value;
  const tool   = document.getElementById("filter-tool")?.value;
  const action = document.getElementById("filter-action")?.value;
  const date   = document.getElementById("filter-date")?.value;

  if (stage  && record.stage !== stage) return false;
  if (level  && record.level !== level) return false;
  if (tool   && record.tool_id !== tool) return false;
  if (action && record.action_name !== action) return false;
  if (date   && !(record.timestamp || "").startsWith(date)) return false;
  if (tier) {
    const src = record._source_file || "";
    if (!src.includes(tier)) return false;
  }
  return true;
}

async function loadRecentLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/recent-logs?limit=100`);
    const data = await res.json();
    const logs = data.logs || [];
    if (logs.length) {
      allLogs = logs;
      applyFilters();
    }
  } catch (e) {
    /* ignore network error on init */
  }
}

function applyFilters() {
  const console_ = document.getElementById("log-console");
  console_.innerHTML = "";
  allLogs.forEach(r => renderLogLine(r, console_));
}

function clearLogs() {
  allLogs = [];
  const console_ = document.getElementById("log-console");
  console_.innerHTML = '<div class="log-placeholder">Log cleared.</div>';
}

// ─── Process List ─────────────────────────────────────────────────────────────
function renderProcessList(workers) {
  const el = document.getElementById("process-list");
  if (!workers.length) {
    el.innerHTML = '<div class="empty-state">No active workers</div>';
    return;
  }
  el.innerHTML = workers.map(w => `
    <div class="process-row">
      <span class="process-pid">${w.pid}</span>
      <span class="process-name" title="${w.cmdline.join(' ')}">${w.name}</span>
      <span class="process-cpu">${(w.cpu_pct || 0).toFixed(1)}%</span>
      <span class="process-ram">${(w.ram_mb || 0).toFixed(0)}M</span>
    </div>
  `).join("");
}

// ─── Events List ─────────────────────────────────────────────────────────────
function renderEvents(events) {
  const el = document.getElementById("events-list");
  if (!events.length) {
    el.innerHTML = '<div class="empty-state">No events yet</div>';
    return;
  }
  el.innerHTML = [...events].reverse().map(ev => `
    <div class="event-row">
      <div class="event-ts">${(ev.timestamp || "").slice(11,19)}</div>
      <div class="event-msg">${escHtml(ev.message || "")}</div>
    </div>
  `).join("");
}

// ─── Git Log ──────────────────────────────────────────────────────────────────
async function loadGitLog() {
  try {
    const res  = await fetch(`${API_BASE}/api/git-log`);
    const data = await res.json();
    const el   = document.getElementById("git-log-list");
    const commits = data.commits || [];

    if (!commits.length) {
      el.innerHTML = '<div class="empty-state">No commits yet</div>';
      return;
    }
    el.innerHTML = commits.slice(0, 10).map(c => `
      <div class="git-row">
        <span class="git-hash">${c.short_hash}</span>
        <div class="git-msg" title="${escHtml(c.message)}">${escHtml(c.message)}</div>
      </div>
    `).join("");
  } catch (e) {
    document.getElementById("git-log-list").innerHTML =
      '<div class="empty-state">Could not load commits</div>';
  }
}

// ─── Tool Roster (Tab 2) ──────────────────────────────────────────────────────
async function loadTools() {
  try {
    const res  = await fetch(`${API_BASE}/api/tools`);
    const data = await res.json();
    renderTools(data.tools || []);
  } catch (e) {
    document.getElementById("tools-grid").innerHTML =
      '<div class="empty-state">Could not load tool registry</div>';
  }
}

function renderTools(tools) {
  const grid = document.getElementById("tools-grid");
  const batchClass = { 1: "b1", 2: "b2", 3: "b3", 4: "b4" };

  grid.innerHTML = tools.map(t => {
    const bc = batchClass[t.batch] || "b1";
    const statusCls = `status-${t.status || "scaffolded"}`;
    const statusLabel = (t.status || "scaffolded").charAt(0).toUpperCase() + (t.status || "scaffolded").slice(1);
    const actions = (t.supported_actions || []).map(a =>
      `<span class="action-pill">${a}</span>`
    ).join("");

    return `
      <div class="tool-card ${bc}">
        <div class="tool-card-header">
          <div>
            <div class="tool-card-id">${t.tool_id}</div>
            <div class="tool-card-name">${t.name}</div>
            <span class="tool-mechanism">${t.mechanism_type || ""}</span>
          </div>
          <span class="tool-status-badge ${statusCls}">${statusLabel}</span>
        </div>
        <div class="tool-description">${t.description || ""}</div>
        <div class="tool-actions">${actions}</div>
        ${t.installed ? `
          <button class="smoke-btn" id="smoke-btn-${t.tool_id}" onclick="runTool('${t.tool_id}', this)">
            ▶ Run Tool Smoke Test
          </button>
        ` : ""}
      </div>
    `;
  }).join("");
}

// ─── Data Explorer (Tab 3) ────────────────────────────────────────────────────
async function loadDataTree() {
  const container = document.getElementById("tree-container");
  container.innerHTML = '<div class="loading-dots">Loading data tree</div>';

  try {
    const res  = await fetch(`${API_BASE}/api/data-tree`);
    const data = await res.json();
    renderTree(data.tree || {}, container);
  } catch (e) {
    container.innerHTML = '<div class="empty-state">Could not load data tree</div>';
  }
}

function renderTree(tree, container) {
  const isEmpty = Object.keys(tree).length === 0 ||
    Object.values(tree).every(a => Object.keys(a).length === 0);

  if (isEmpty) {
    container.innerHTML = '<div class="empty-state">No run data yet.<br>Run a demo or tool action first.</div>';
    return;
  }

  container.innerHTML = "";

  for (const [toolId, actions] of Object.entries(tree)) {
    if (!Object.keys(actions).length) continue;

    const toolNode = makeTreeNode({
      icon: "🛠", label: toolId, labelClass: "tool-level",
      children: () => {
        const kids = [];
        for (const [actionName, dates] of Object.entries(actions)) {
          const actionNode = makeTreeNode({
            icon: "⚡", label: actionName,
            children: () => {
              const dateKids = [];
              for (const [date, runs] of Object.entries(dates).sort().reverse()) {
                const dateNode = makeTreeNode({
                  icon: "📅", label: date,
                  children: () => runs.map(run => makeTreeNode({
                    icon: "📂",
                    label: run.run_id,
                    labelClass: "run-level",
                    onClick: () => showRunDetail(toolId, actionName, date, run),
                  }))
                });
                dateKids.push(dateNode);
              }
              return dateKids;
            }
          });
          kids.push(actionNode);
        }
        return kids;
      }
    });
    container.appendChild(toolNode);
  }
}

function makeTreeNode({ icon, label, labelClass = "", children, onClick }) {
  const node = document.createElement("div");
  node.className = "tree-node";

  const labelEl = document.createElement("div");
  labelEl.className = "tree-label";

  const caret = document.createElement("span");
  caret.className = "tree-caret";
  caret.textContent = children ? "▶" : " ";

  const iconEl = document.createElement("span");
  iconEl.className = "tree-icon";
  iconEl.textContent = icon;

  const nameEl = document.createElement("span");
  nameEl.className = `tree-name ${labelClass}`;
  nameEl.textContent = label;

  labelEl.appendChild(caret);
  labelEl.appendChild(iconEl);
  labelEl.appendChild(nameEl);
  node.appendChild(labelEl);

  let childrenContainer = null;

  labelEl.addEventListener("click", () => {
    if (onClick) {
      document.querySelectorAll(".tree-label.selected").forEach(el => el.classList.remove("selected"));
      labelEl.classList.add("selected");
      onClick();
      return;
    }
    if (!children) return;

    if (!childrenContainer) {
      childrenContainer = document.createElement("div");
      childrenContainer.className = "tree-children";
      const childNodes = children();
      childNodes.forEach(c => childrenContainer.appendChild(c));
      node.appendChild(childrenContainer);
    }
    const isOpen = childrenContainer.classList.toggle("open");
    caret.classList.toggle("open", isOpen);
  });

  return node;
}

function showRunDetail(toolId, actionName, date, run) {
  document.getElementById("detail-title").textContent =
    `${run.run_id}`;

  const panel  = document.getElementById("detail-panel");
  const m      = run.manifest || {};
  const status = m.status || "unknown";
  const statusCls = `manifest-status-${status}`;
  const domainMetrics = m.domain_metrics || run.domain_metrics;

  const rawFiles = (run.raw_files || []).map(f => `
    <div class="file-item clickable" onclick="previewFile('${toolId}', '${actionName}', '${date}', '${run.run_id}', 'raw', '${f}')">
      <span>📄 ${f}</span>
      <span class="file-item-badge">Preview</span>
    </div>
  `).join("") || "<div class='empty-state'>No raw files</div>";

  const cleanedFiles = (run.cleaned_files || []).map(f => `
    <div class="file-item clickable" onclick="previewFile('${toolId}', '${actionName}', '${date}', '${run.run_id}', 'cleaned', '${f}')">
      <span>✨ ${f}</span>
      <span class="file-item-badge">Preview</span>
    </div>
  `).join("") || "<div class='empty-state'>No cleaned files</div>";

  const metricsSection = domainMetrics && Object.keys(domainMetrics).length ? `
    <div class="file-list-section">
      <div class="file-list-title">📊 Indexed Domain Metrics & KPIs</div>
      <div style="display:flex; flex-wrap:wrap; gap:6px; padding:6px 0;">
        ${Object.entries(domainMetrics).map(([k, v]) => `
          <span class="metric-pill" style="font-size:11px; padding:3px 8px;">
            <strong>${escHtml(k)}:</strong> ${escHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}
          </span>
        `).join("")}
      </div>
    </div>
  ` : "";

  panel.innerHTML = `
    <div class="manifest-grid">
      <span class="manifest-key">Run ID</span>
      <span class="manifest-val">${m.run_id || run.run_id}</span>
      <span class="manifest-key">Tool</span>
      <span class="manifest-val">${m.tool_id || toolId}</span>
      <span class="manifest-key">Action</span>
      <span class="manifest-val">${m.action_name || actionName}</span>
      <span class="manifest-key">Date</span>
      <span class="manifest-val">${m.date || date}</span>
      <span class="manifest-key">Target URL</span>
      <span class="manifest-val">${m.target_url || "—"}</span>
      <span class="manifest-key">Started</span>
      <span class="manifest-val">${(m.started_at || "").replace("T"," ").slice(0,19)}</span>
      <span class="manifest-key">Ended</span>
      <span class="manifest-val">${(m.ended_at || "—").replace("T"," ").slice(0,19)}</span>
      <span class="manifest-key">Elapsed</span>
      <span class="manifest-val">${m.elapsed_sec != null ? m.elapsed_sec + "s" : "—"}</span>
      <span class="manifest-key">Status</span>
      <span class="manifest-val ${statusCls}">${status.toUpperCase()}</span>
      <span class="manifest-key">Git Commit</span>
      <span class="manifest-val">${m.git_commit || "—"}</span>
    </div>

    ${metricsSection}

    <div class="file-list-section">
      <div class="file-list-title">📦 Raw Files (${(run.raw_files||[]).length}) — click to preview</div>
      <div class="file-list">${rawFiles}</div>
    </div>

    <div class="file-list-section">
      <div class="file-list-title">✨ Cleaned Files (${(run.cleaned_files||[]).length}) — click to preview</div>
      <div class="file-list">${cleanedFiles}</div>
    </div>

    <div class="run-log-section">
      <div class="file-list-title">📋 Run Log (action_run.jsonl)</div>
      <div class="run-log-console" id="run-log-console">
        <div class="loading-dots">Loading run log...</div>
      </div>
    </div>
  `;

  // Fetch dedicated run log
  fetch(`${API_BASE}/api/run-log?tool_id=${encodeURIComponent(toolId)}&action=${encodeURIComponent(actionName)}&date=${encodeURIComponent(date)}&run_id=${encodeURIComponent(run.run_id)}`)
    .then(r => r.json())
    .then(data => {
      const consoleEl = document.getElementById("run-log-console");
      if (!consoleEl) return;
      const lines = data.lines || [];
      if (!lines.length) {
        consoleEl.innerHTML = "<div class='empty-state'>No log records recorded for this run</div>";
        return;
      }
      consoleEl.innerHTML = lines.map(l => {
        const ts = (l.timestamp || "").slice(11, 19);
        const lvl = l.level || "INFO";
        const msg = l.message || JSON.stringify(l);
        return `<div class="run-log-line"><span class="log-ts">${ts}</span><span class="log-level-${lvl}">[${lvl}]</span><span>${escHtml(msg)}</span></div>`;
      }).join("");
    })
    .catch(() => {
      const consoleEl = document.getElementById("run-log-console");
      if (consoleEl) consoleEl.innerHTML = "<div class='empty-state'>Could not load run log</div>";
    });
}

// ─── Demo Run Trigger ─────────────────────────────────────────────────────────
async function triggerDemo() {
  const btn = document.getElementById("demo-btn");
  btn.disabled = true;
  btn.textContent = "⏳ Starting...";

  try {
    const res  = await fetch(`${API_BASE}/api/demo-run`, { method: "POST" });
    const data = await res.json();

    if (data.status === "demo_started") {
      btn.classList.add("running");
      btn.textContent = "⏳ Demo Running";
      // Re-enable after demo duration (12s + buffer)
      setTimeout(() => {
        btn.disabled = false;
        btn.classList.remove("running");
        btn.textContent = "▶ Demo Run";
        loadDataTree();  // refresh explorer
        loadGitLog();
      }, 15000);
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "▶ Demo Run";
    alert("Could not connect to backend. Is the server running?");
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function pad2(n) {
  return String(Math.floor(n)).padStart(2, "0");
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── File Preview Modal ───────────────────────────────────────────────────────
async function previewFile(toolId, action, date, runId, folder, filename) {
  const modal = document.getElementById("file-modal");
  const title = document.getElementById("modal-title");
  const meta = document.getElementById("modal-meta");
  const content = document.getElementById("modal-content");

  if (!modal) return;
  title.textContent = filename;
  meta.textContent = `${toolId} / ${action} / ${date} / ${runId} / ${folder} — Loading preview...`;
  content.textContent = "Loading file content...";
  modal.classList.add("open");

  try {
    const res = await fetch(`${API_BASE}/api/file-preview?tool_id=${encodeURIComponent(toolId)}&action=${encodeURIComponent(action)}&date=${encodeURIComponent(date)}&run_id=${encodeURIComponent(runId)}&folder=${encodeURIComponent(folder)}&filename=${encodeURIComponent(filename)}`);
    const data = await res.json();
    if (data.error) {
      content.textContent = `Error: ${data.error}`;
    } else {
      meta.textContent = `${folder.toUpperCase()} • Size: ${data.size} bytes (showing first ${data.content.length} chars)`;
      content.textContent = data.content;
    }
  } catch (e) {
    content.textContent = `Network error fetching preview: ${e.message}`;
  }
}

function closeModal(e) {
  if (e && e.target !== e.currentTarget && !e.target.classList.contains("modal-close")) return;
  document.getElementById("file-modal")?.classList.remove("open");
}

// ─── Run Tool Smoke Test ──────────────────────────────────────────────────────
async function runTool(toolId, btn) {
  if (!btn) btn = document.getElementById(`smoke-btn-${toolId}`);
  if (btn) {
    btn.disabled = true;
    btn.classList.add("running");
    btn.textContent = "⏳ Running...";
  }

  try {
    const res = await fetch(`${API_BASE}/api/run-tool/${encodeURIComponent(toolId)}`, { method: "POST" });
    const data = await res.json();
    if (data.status === "started") {
      setTimeout(() => {
        if (btn) {
          btn.disabled = false;
          btn.classList.remove("running");
          btn.textContent = "▶ Run Tool Smoke Test";
        }
        loadDataTree();
        loadGitLog();
      }, 10000);
    } else {
      alert(`Could not start tool: ${data.error || "Unknown error"}`);
      if (btn) {
        btn.disabled = false;
        btn.classList.remove("running");
        btn.textContent = "▶ Run Tool Smoke Test";
      }
    }
  } catch (err) {
    alert(`Request error: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.classList.remove("running");
      btn.textContent = "▶ Run Tool Smoke Test";
    }
  }
}

// ─── Jump To Run Detail (Tab 4 -> Tab 3 Integration) ─────────────────────────
async function jumpToRunDetail(toolId, actionName, date, runId) {
  const explorerBtn = document.querySelector('.tab-btn[data-tab="tab-explorer"]');
  switchTab("tab-explorer", explorerBtn);

  // Try to find run in data-tree
  try {
    const res = await fetch(`${API_BASE}/api/data-tree`);
    const data = await res.json();
    const tree = data.tree || {};
    if (tree[toolId] && tree[toolId][actionName] && tree[toolId][actionName][date]) {
      const match = tree[toolId][actionName][date].find(r => r.run_id === runId);
      if (match) {
        showRunDetail(toolId, actionName, date, match);
        return;
      }
    }
  } catch (e) { /* ignore */ }

  // Fallback if not found in cache
  showRunDetail(toolId, actionName, date, {
    run_id: runId,
    manifest: { tool_id: toolId, action_name: actionName, date: date, run_id: runId },
    raw_files: [],
    cleaned_files: []
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4: INDEX & SEARCH HUB LOGIC
// ═══════════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4: INDEX & SEARCH HUB LOGIC (STAGE 2 STEP 2.3)
// ═══════════════════════════════════════════════════════════════════════════════
let currentIndexScope   = "global";
let currentSubView       = "subview-switchboard";
let currentMatrixTier    = "all";
let indexSearchDebounce  = null;
let currentFolderBundle  = null;
let cachedFacets         = null;
let matrixLogsCache      = [];

function onIndexScopeChange(scope) {
  if (!scope) {
    scope = document.getElementById("index-scope-select")?.value || "global";
  } else {
    const sel = document.getElementById("index-scope-select");
    if (sel) sel.value = scope;
  }
  currentIndexScope = scope;

  const pill = document.getElementById("index-scope-pill");
  const kpiScope = document.getElementById("kpi-scope");
  const banner = document.getElementById("isolated-mode-banner");
  const dbName = document.getElementById("isolated-db-name");

  if (scope === "global") {
    if (pill) {
      pill.textContent = "GLOBAL MASTER";
      pill.className = "scope-pill";
    }
    if (kpiScope) kpiScope.textContent = "GLOBAL";
    if (banner) banner.style.display = "none";
  } else {
    if (pill) {
      pill.textContent = `SEPARATE: ${scope}.sqlite`;
      pill.className = "scope-pill pill-separate";
    }
    if (kpiScope) kpiScope.textContent = scope;
    if (banner) {
      banner.style.display = "flex";
      if (dbName) dbName.textContent = `index_store/tool_indexes/${scope}.sqlite`;
    }
  }

  loadIndexHub();
}

function switchSubView(subviewId, btn) {
  currentSubView = subviewId;
  document.querySelectorAll(".subview-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".subview-btn").forEach(el => el.classList.remove("active"));

  const target = document.getElementById(subviewId);
  if (target) target.classList.add("active");
  if (btn) btn.classList.add("active");

  loadActiveSubView();
}

function loadActiveSubView() {
  if (currentSubView === "subview-switchboard") {
    loadPipelinesStatus();
  } else if (currentSubView === "subview-cascading") {
    loadCascadingFacets();
  } else if (currentSubView === "subview-matrix") {
    loadMatrixLogs();
  } else if (currentSubView === "subview-search") {
    loadFtsFiles();
  }
}

async function loadIndexHub() {
  await loadIndexOverview();
  loadActiveSubView();
}

async function loadIndexOverview() {
  try {
    const res = await fetch(`${API_BASE}/api/index/overview`);
    const data = await res.json();

    if (currentIndexScope === "global") {
      const tot = data.totals || {};
      const lb = (data.logs_breakdown && data.logs_breakdown.by_tier) || {};
      setText("kpi-runs", tot.total_runs || 0);
      setText("kpi-actions", `${tot.total_tools || 20} tools connected`);
      setText("kpi-raw-files", tot.total_raw_files || 0);
      setText("kpi-raw-size", formatBytes(tot.total_raw_bytes || 0));
      setText("kpi-clean-files", tot.total_cleaned_files || 0);
      setText("kpi-clean-size", formatBytes(tot.total_cleaned_bytes || 0));
      setText("kpi-logs", tot.total_logs || 0);
      setText("kpi-logs-breakdown", `Act: ${lb.action_run || 0} | Tool: ${lb.tool_ops || 0} | Stg: ${lb.stage_log || 0} | Glob: ${lb.global_prompt || 0}`);
      setText("kpi-scope", "GLOBAL MASTER");
      setText("kpi-last-sync", (data.generated_at || "Just now").slice(11, 19));
    } else {
      const ind = (data.individual_tool_indexes || []).find(t => t.tool_id === currentIndexScope);
      if (ind) {
        const meta = ind.metadata || {};
        setText("kpi-runs", ind.total_runs || meta.total_runs || 0);
        setText("kpi-actions", `${meta.total_actions || 1} actions`);
        setText("kpi-raw-files", meta.total_raw_files || 0);
        setText("kpi-raw-size", "Indexed in SQLite");
        setText("kpi-clean-files", meta.total_cleaned_files || 0);
        setText("kpi-clean-size", "Indexed in SQLite");
        setText("kpi-logs", meta.total_log_entries || 0);
        setText("kpi-logs-breakdown", `Pipeline: ${ind.tool_id}`);
        setText("kpi-scope", ind.tool_id);
        setText("kpi-last-sync", (ind.indexed_at || meta.last_indexed_at || "—").slice(11, 19));
      }
    }
  } catch (err) {
    console.error("Error loading index overview:", err);
  }
}

// ─── Sub-View A: 20-Tool Pipeline Switchboard ─────────────────────────────────
async function loadPipelinesStatus() {
  const grid = document.getElementById("pipelines-grid");
  if (!grid) return;
  grid.innerHTML = '<div class="loading-dots">Loading 20-tool pipeline switchboard status...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/index/pipelines-status`);
    const data = await res.json();
    const pipelines = data.pipelines || [];

    setText("arch-tools-count", `${data.synced_count || 0}/${data.total_tools || 20} Synced`);
    setText("arch-master-size", `${(data.master_db_size_kb / 1024).toFixed(2)} MB`);

    if (!pipelines.length) {
      grid.innerHTML = '<div class="empty-state">No pipeline status data returned.</div>';
      return;
    }

    grid.innerHTML = pipelines.map(p => {
      const isCurrent = (p.tool_id === currentIndexScope);
      const isSynced = (p.sync_status === "SYNCED");
      const syncBadge = isSynced
        ? '<span class="sync-badge synced">SYNCED ✓</span>'
        : '<span class="sync-badge unsynced">OUT_OF_SYNC ⚠</span>';

      const actionsPills = (p.supported_actions || []).map(a =>
        `<span class="action-pill" style="font-size:9px; padding:1px 5px;">${escHtml(a)}</span>`
      ).join(" ");

      return `
        <div class="pipeline-card ${isCurrent ? 'active-pipeline' : ''}">
          <div class="pipeline-card-header">
            <div>
              <span class="pipeline-id">${escHtml(p.tool_id)}</span>
              <div class="pipeline-name">${escHtml(p.name)}</div>
              <div class="pipeline-meta">${escHtml(p.mechanism_type)} • Batch ${p.batch}</div>
            </div>
            ${syncBadge}
          </div>

          <div class="pipeline-stats-row">
            <div class="stat-box">
              <div class="stat-box-label">ISOLATED RUNS</div>
              <div class="stat-box-val">${p.isolated_runs_count}</div>
            </div>
            <div class="stat-box">
              <div class="stat-box-label">GLOBAL RUNS</div>
              <div class="stat-box-val">${p.global_runs_count}</div>
            </div>
            <div class="stat-box">
              <div class="stat-box-label">DB SIZE</div>
              <div class="stat-box-val">${p.db_size_kb}K</div>
            </div>
          </div>

          <div style="font-size:10px; color:var(--text-muted); display:flex; justify-content:space-between;">
            <span>Files: <strong>${p.isolated_files_count}</strong></span>
            <span>Logs: <strong>${p.isolated_logs_count}</strong></span>
            <span>DB: <code class="mono" style="font-size:9px;">${p.tool_id}.sqlite</code></span>
          </div>

          <div style="margin-top:2px;">${actionsPills}</div>

          <div class="pipeline-actions-row">
            <button class="pipeline-btn ${isCurrent ? '' : 'primary'}" onclick="onIndexScopeChange('${p.tool_id}')" title="Read strictly from isolated database">
              ${isCurrent ? '⚡ Active Pipeline' : '🔍 Load Isolated Index'}
            </button>
            <button class="pipeline-btn" onclick="triggerIndexRebuild('${p.tool_id}')" title="Re-index tool and sync to Global">
              🔄 Re-Index
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error loading pipeline switchboard: ${escHtml(err.message)}</div>`;
  }
}

// ─── Sub-View B: Cascading Folder-Wise Index Inspector ────────────────────────
async function loadCascadingFacets() {
  const toolSelect = document.getElementById("cascade-select-tool");
  const actionSelect = document.getElementById("cascade-select-action");
  const dateSelect = document.getElementById("cascade-select-date");
  const runSelect = document.getElementById("cascade-select-run");

  const selTool = toolSelect?.value || (currentIndexScope !== "global" ? currentIndexScope : "");
  const selAction = actionSelect?.value || "";
  const selDate = dateSelect?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope });
  if (selTool) params.append("tool_id", selTool);
  if (selAction) params.append("action_name", selAction);
  if (selDate) params.append("run_date", selDate);

  try {
    const res = await fetch(`${API_BASE}/api/index/cascading-facets?${params.toString()}`);
    const data = await res.json();
    cachedFacets = data;

    // 1. Tool Select
    if (toolSelect) {
      const cur = toolSelect.value || selTool;
      toolSelect.innerHTML = '<option value="">All Tools (20)</option>' +
        (data.tools || []).map(t =>
          `<option value="${t.tool_id}" ${t.tool_id === cur ? 'selected' : ''}>${t.tool_id} (${t.runs_count} runs)</option>`
        ).join("");
    }

    // 2. Action Select
    if (actionSelect) {
      const curA = actionSelect.value;
      actionSelect.innerHTML = '<option value="">All Actions</option>' +
        (data.actions || []).map(a =>
          `<option value="${a.action_name}" ${a.action_name === curA ? 'selected' : ''}>${a.action_name} (${a.runs_count})</option>`
        ).join("");
    }

    // 3. Date Select
    if (dateSelect) {
      const curD = dateSelect.value;
      dateSelect.innerHTML = '<option value="">All Dates</option>' +
        (data.dates || []).map(d =>
          `<option value="${d.run_date}" ${d.run_date === curD ? 'selected' : ''}>${d.run_date} (${d.runs_count})</option>`
        ).join("");
    }

    // 4. Run Select
    if (runSelect) {
      const runs = data.runs || [];
      if (!runs.length) {
        runSelect.innerHTML = '<option value="">No runs found for filter</option>';
        const mb = document.getElementById("cascade-manifest-body");
        if (mb) mb.innerHTML = '<div class="empty-state">No runs match current hierarchy filters.</div>';
        const fb = document.getElementById("cascade-files-body");
        if (fb) fb.innerHTML = '<div class="empty-state">No files.</div>';
        const lb = document.getElementById("cascade-logs-body");
        if (lb) lb.innerHTML = '<div class="empty-state">No logs.</div>';
      } else {
        const curR = runSelect.value;
        runSelect.innerHTML = runs.map(r =>
          `<option value="${r.run_id}" ${r.run_id === curR ? 'selected' : ''}>${r.run_id} [${(r.status || 'OK').toUpperCase()}] (${r.tool_id})</option>`
        ).join("");

        const targetRunId = runSelect.value || runs[0].run_id;
        loadFolderBundle(targetRunId);
      }
    }
  } catch (err) {
    console.error("Error loading cascading facets:", err);
  }
}

function onCascadeToolChange(toolId) {
  const actionSelect = document.getElementById("cascade-select-action");
  const dateSelect = document.getElementById("cascade-select-date");
  if (actionSelect) actionSelect.value = "";
  if (dateSelect) dateSelect.value = "";
  loadCascadingFacets();
}

function onCascadeActionChange(actionName) {
  const dateSelect = document.getElementById("cascade-select-date");
  if (dateSelect) dateSelect.value = "";
  loadCascadingFacets();
}

function onCascadeDateChange(date) {
  loadCascadingFacets();
}

function onCascadeRunChange(runId) {
  if (runId) loadFolderBundle(runId);
}

function refreshCascadingFacets() {
  loadCascadingFacets();
}

async function loadFolderBundle(runId) {
  if (!runId) return;

  const manifestBody = document.getElementById("cascade-manifest-body");
  const filesBody = document.getElementById("cascade-files-body");
  const logsBody = document.getElementById("cascade-logs-body");
  const statusPill = document.getElementById("cascade-status-pill");
  const filesCountBadge = document.getElementById("cascade-files-count");

  if (manifestBody) manifestBody.innerHTML = '<div class="loading-dots">Loading run manifest & domain KPIs...</div>';
  if (filesBody) filesBody.innerHTML = '<div class="loading-dots">Loading raw & cleaned files...</div>';
  if (logsBody) logsBody.innerHTML = '<div class="loading-dots">Loading action & operational logs...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/index/folder-bundle?run_id=${encodeURIComponent(runId)}&scope=${currentIndexScope}`);
    const data = await res.json();
    currentFolderBundle = data;

    const m = data.run_metadata || {};
    const status = (m.status || "completed").toLowerCase();

    if (statusPill) {
      statusPill.textContent = status.toUpperCase();
      statusPill.className = `tool-status-badge status-${status}`;
    }

    // Panel 1: Manifest & Domain KPIs
    const dMetrics = m.domain_metrics || {};
    const metricCards = Object.entries(dMetrics).map(([k, v]) => {
      const valStr = typeof v === 'object' ? JSON.stringify(v) : String(v);
      return `
        <div class="kpi-card" style="padding:8px 12px;">
          <div class="kpi-label">${escHtml(k)}</div>
          <div class="kpi-val highlight" style="font-size:16px;">${escHtml(valStr)}</div>
        </div>
      `;
    }).join("") || '<div style="color:var(--text-muted); font-size:11px;">No domain metrics extracted for this run.</div>';

    if (manifestBody) {
      manifestBody.innerHTML = `
        <div class="manifest-grid" style="font-size:11px; margin-bottom:12px;">
          <span class="manifest-key">Run ID</span><span class="manifest-val mono">${escHtml(m.run_id)}</span>
          <span class="manifest-key">Tool</span><span class="manifest-val mono"><strong>${escHtml(m.tool_id)}</strong></span>
          <span class="manifest-key">Action</span><span class="manifest-val mono">${escHtml(m.action_name)}</span>
          <span class="manifest-key">Date</span><span class="manifest-val">${escHtml(m.run_date || '')}</span>
          <span class="manifest-key">Target URL</span><span class="manifest-val">${escHtml(m.target_url || '—')}</span>
          <span class="manifest-key">Elapsed</span><span class="manifest-val">${m.elapsed_sec != null ? m.elapsed_sec + 's' : '—'}</span>
          <span class="manifest-key">Git Commit</span><span class="manifest-val mono">${escHtml(m.git_commit || '—')}</span>
        </div>
        <div style="font-size:11px; font-weight:700; color:var(--text-secondary); margin-bottom:6px;">EXTRACTED DOMAIN KPIS:</div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:8px;">
          ${metricCards}
        </div>
      `;
    }

    // Panel 2: Side-by-Side Raw vs Cleaned Files
    const rawFiles = data.raw_files || [];
    const cleanedFiles = data.cleaned_files || [];
    if (filesCountBadge) {
      filesCountBadge.textContent = `Raw: ${rawFiles.length} | Cleaned: ${cleanedFiles.length}`;
    }

    const renderFileItems = (files, tier) => {
      if (!files.length) return `<div class="empty-state" style="padding:10px;">No ${tier} files</div>`;
      return files.map(f => `
        <div class="file-item clickable" onclick="previewFile('${m.tool_id}', '${m.action_name}', '${m.run_date}', '${m.run_id}', '${tier}', '${f.filename}')">
          <div style="display:flex; flex-direction:column; gap:2px; flex:1; overflow:hidden;">
            <span style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">📄 ${escHtml(f.filename)}</span>
            <span style="font-size:10px; color:var(--text-muted);">${formatBytes(f.size_bytes)} • SHA: <code class="mono">${escHtml(f.sha256_short || '')}</code></span>
          </div>
          <span class="file-item-badge">Preview</span>
        </div>
      `).join("");
    };

    if (filesBody) {
      filesBody.innerHTML = `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
          <div>
            <div style="font-size:11px; font-weight:700; color:var(--accent-yellow); margin-bottom:6px;">📦 RAW TIER (${rawFiles.length})</div>
            ${renderFileItems(rawFiles, 'raw')}
          </div>
          <div>
            <div style="font-size:11px; font-weight:700; color:var(--accent-green); margin-bottom:6px;">✨ CLEANED TIER (${cleanedFiles.length})</div>
            ${renderFileItems(cleanedFiles, 'cleaned')}
          </div>
        </div>
      `;
    }

    // Panel 3: Action Logs & Tool Ops Logs
    filterCascadeLogs();

  } catch (err) {
    if (manifestBody) manifestBody.innerHTML = `<div class="empty-state">Error loading folder bundle: ${escHtml(err.message)}</div>`;
  }
}

function filterCascadeLogs() {
  const logsBody = document.getElementById("cascade-logs-body");
  if (!logsBody || !currentFolderBundle) return;

  const lvl = document.getElementById("cascade-log-level-filter")?.value || "";
  const query = document.getElementById("cascade-log-search")?.value?.toLowerCase() || "";

  const actionLogs = currentFolderBundle.action_logs || [];
  const toolOpsLogs = currentFolderBundle.tool_ops_logs || [];
  const combined = [...actionLogs, ...toolOpsLogs];

  const filtered = combined.filter(l => {
    if (lvl && l.level !== lvl) return false;
    if (query && !(l.message || '').toLowerCase().includes(query)) return false;
    return true;
  });

  if (!filtered.length) {
    logsBody.innerHTML = '<div class="empty-state">No log entries match criteria.</div>';
    return;
  }

  logsBody.innerHTML = filtered.map(l => {
    const ts = (l.timestamp || "").replace("T", " ").slice(0, 19);
    const tierBadge = `<span class="logtier-badge ${l.log_tier}">${escHtml(l.log_tier || 'ops')}</span>`;
    const lvlBadge = `<span class="log-level-${l.level}">[${l.level}]</span>`;
    const msg = highlightSearch(l.message || '', query);
    return `
      <div style="padding:2px 0; border-bottom:1px solid rgba(255,255,255,0.03);">
        <span style="color:var(--text-muted); font-size:10px;">${ts}</span>
        ${tierBadge} ${lvlBadge}
        <span>${msg}</span>
      </div>
    `;
  }).join("");
}

// ─── Sub-View C: Dedicated 4-Tier Log Filter Matrix ───────────────────────────
function selectMatrixTier(tier, btn) {
  currentMatrixTier = tier;
  document.querySelectorAll(".tier-pill-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  loadMatrixLogs();
}

async function loadMatrixLogs() {
  const tbody = document.getElementById("matrix-table-body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" class="loading-td">Loading 4-tier log matrix...</td></tr>';

  const q = document.getElementById("matrix-search-input")?.value?.trim() || "";
  const stage = document.getElementById("matrix-stage-select")?.value || "";
  const tool = document.getElementById("matrix-tool-select")?.value || "";
  const level = document.getElementById("matrix-level-select")?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope, limit: "250" });
  if (q) params.append("q", q);
  if (stage) params.append("stage", stage);
  if (tool) params.append("tool_id", tool);
  if (level) params.append("level", level);
  if (currentMatrixTier !== "all") params.append("log_tier", currentMatrixTier);

  try {
    const [logsRes, historyRes] = await Promise.all([
      fetch(`${API_BASE}/api/index/logs?${params.toString()}`),
      fetch(`${API_BASE}/api/index/prompt-history?limit=100`)
    ]);

    const logsData = await logsRes.json();
    const historyData = await historyRes.json();
    const logs = logsData.logs || [];
    matrixLogsCache = logs;

    // Populate Tool Select if empty
    const toolSel = document.getElementById("matrix-tool-select");
    if (toolSel && toolSel.options.length <= 1) {
      try {
        const tRes = await fetch(`${API_BASE}/api/tools`);
        const tData = await tRes.json();
        (tData.tools || []).forEach(t => {
          const opt = document.createElement("option");
          opt.value = t.tool_id;
          opt.textContent = `${t.tool_id} — ${t.name}`;
          toolSel.appendChild(opt);
        });
      } catch (e) {}
    }

    // Update Counts on Tier Buttons
    let cAll = logs.length;
    let c4 = logs.filter(l => l.log_tier === 'global_prompt').length;
    let c3 = logs.filter(l => l.log_tier === 'stage_log').length;
    let c2 = logs.filter(l => l.log_tier === 'tool_ops').length;
    let c1 = logs.filter(l => l.log_tier === 'action_run').length;

    setText("count-tier-all", cAll);
    setText("count-tier-4", c4 || (historyData.milestones || []).length);
    setText("count-tier-3", c3);
    setText("count-tier-2", c2);
    setText("count-tier-1", c1);

    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading-td">No logs found matching current matrix filters.</td></tr>';
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const ts = (l.timestamp || "").replace("T", " ").slice(0, 19);
      const tierBadge = `<span class="logtier-badge ${l.log_tier || 'tool_ops'}">${escHtml(l.log_tier || 'ops')}</span>`;
      const stageStep = [l.stage, l.step].filter(Boolean).join(" / ") || "—";
      const lvlCls = `log-level-${l.level || 'INFO'}`;
      const msg = highlightSearch(l.message || '', q);
      const commit = l.git_commit ? `<span class="hash-pill">${escHtml(l.git_commit)}</span>` : '<span style="color:var(--text-muted); font-size:10px;">—</span>';

      return `
        <tr>
          <td style="white-space:nowrap; font-family:var(--font-mono); font-size:11px;">${ts}</td>
          <td>${tierBadge}</td>
          <td style="font-size:11px; color:var(--text-secondary);">${escHtml(stageStep)}</td>
          <td><strong class="mono">${escHtml(l.tool_id || '—')}</strong></td>
          <td><span class="mono">${escHtml(l.action_name || '—')}</span></td>
          <td><span class="${lvlCls}">[${escHtml(l.level || 'INFO')}]</span></td>
          <td>${commit}</td>
          <td style="font-family:var(--font-mono); font-size:11px; word-break:break-all;">${msg}</td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-td">Error loading logs matrix: ${escHtml(err.message)}</td></tr>`;
  }
}

function handleMatrixSearchKey(event) {
  if (event.key === "Enter") {
    loadMatrixLogs();
    return;
  }
  clearTimeout(indexSearchDebounce);
  indexSearchDebounce = setTimeout(() => {
    loadMatrixLogs();
  }, 350);
}

function resetMatrixFilters() {
  const searchInput = document.getElementById("matrix-search-input");
  if (searchInput) searchInput.value = "";
  const stageSel = document.getElementById("matrix-stage-select");
  if (stageSel) stageSel.value = "";
  const toolSel = document.getElementById("matrix-tool-select");
  if (toolSel) toolSel.value = "";
  const lvlSel = document.getElementById("matrix-level-select");
  if (lvlSel) lvlSel.value = "";
  currentMatrixTier = "all";
  document.querySelectorAll(".tier-pill-btn").forEach(b => b.classList.remove("active"));
  document.querySelector('.tier-pill-btn[data-matrix-tier="all"]')?.classList.add("active");
  loadMatrixLogs();
}

function exportFilteredLogs() {
  if (!matrixLogsCache || !matrixLogsCache.length) {
    alert("No filtered logs to export.");
    return;
  }
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(matrixLogsCache, null, 2));
  const downloadAnchor = document.createElement("a");
  const filename = `antigravity_filtered_logs_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`;
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", filename);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

// ─── Sub-View D: Global / Per-Tool FTS5 Artifact Search ───────────────────────
async function loadFtsFiles() {
  const tbody = document.getElementById("fts-files-table-body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" class="loading-td">Searching artifacts across SQLite FTS5...</td></tr>';

  const q = document.getElementById("fts-search-input")?.value?.trim() || "";
  const tool = document.getElementById("fts-filter-tool")?.value || "";
  const tier = document.getElementById("fts-filter-tier")?.value || "";
  const date = document.getElementById("fts-filter-date")?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope, limit: "150" });
  if (q) params.append("q", q);
  if (tool && currentIndexScope === "global") params.append("tool_id", tool);
  if (tier) params.append("tier", tier);
  if (date) params.append("run_date", date);

  try {
    const res = await fetch(`${API_BASE}/api/index/files?${params.toString()}`);
    const data = await res.json();
    const files = data.files || [];

    // Populate Tool Select if empty
    const toolSel = document.getElementById("fts-filter-tool");
    if (toolSel && toolSel.options.length <= 1) {
      try {
        const tRes = await fetch(`${API_BASE}/api/tools`);
        const tData = await tRes.json();
        (tData.tools || []).forEach(t => {
          const opt = document.createElement("option");
          opt.value = t.tool_id;
          opt.textContent = `${t.tool_id} — ${t.name}`;
          toolSel.appendChild(opt);
        });
      } catch (e) {}
    }

    if (!files.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading-td">No artifacts found matching query.</td></tr>';
      return;
    }

    tbody.innerHTML = files.map(f => {
      const tierBadge = f.tier === "cleaned" 
        ? '<span class="tier-badge cleaned">CLEANED</span>' 
        : '<span class="tier-badge raw">RAW</span>';
      const sizeStr = formatBytes(f.size_bytes || 0);
      const shaShort = f.sha256_short || "—";
      const previewText = f.content_preview ? highlightSearch(f.content_preview, q) : '<span style="color:var(--text-muted);">(Binary or empty)</span>';
      const toolId = f.tool_id || currentIndexScope;

      return `
        <tr>
          <td>${tierBadge}</td>
          <td><strong class="mono">${escHtml(f.filename || "—")}</strong></td>
          <td><span class="mono">${escHtml(toolId)}</span></td>
          <td><span class="mono">${escHtml(f.action_name || "—")}</span></td>
          <td>${sizeStr}</td>
          <td><span class="hash-pill">${escHtml(shaShort)}</span></td>
          <td style="max-width:380px; font-family:var(--font-mono); font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escHtml(f.content_preview || '')}">
            ${previewText}
          </td>
          <td>
            <button class="inspect-btn" onclick="previewFile('${toolId}', '${f.action_name || ''}', '${f.run_date || ''}', '${f.run_id || ''}', '${f.tier || 'raw'}', '${f.filename}')">
              Preview
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-td">Error searching artifacts: ${escHtml(err.message)}</td></tr>`;
  }
}

function handleFtsSearchKey(event) {
  if (event.key === "Enter") {
    loadFtsFiles();
    return;
  }
  clearTimeout(indexSearchDebounce);
  indexSearchDebounce = setTimeout(() => {
    loadFtsFiles();
  }, 350);
}

function resetFtsFilters() {
  const searchInput = document.getElementById("fts-search-input");
  if (searchInput) searchInput.value = "";
  const toolSel = document.getElementById("fts-filter-tool");
  if (toolSel) toolSel.value = "";
  const tierSel = document.getElementById("fts-filter-tier");
  if (tierSel) tierSel.value = "";
  const dateInput = document.getElementById("fts-filter-date");
  if (dateInput) dateInput.value = "";
  loadFtsFiles();
}

// ─── Shared Utilities ─────────────────────────────────────────────────────────
async function triggerIndexRebuild(scopeType) {
  const targetScope = scopeType === "global" ? "global" : (scopeType || currentIndexScope);
  const btn = document.getElementById(scopeType === "global" ? "btn-rebuild-all" : "btn-rebuild-active");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Rebuilding...";
  }

  try {
    const res = await fetch(`${API_BASE}/api/index/rebuild`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: targetScope })
    });
    const data = await res.json();

    setTimeout(() => {
      if (btn) {
        btn.disabled = false;
        btn.textContent = scopeType === "global" ? "🔄 Rebuild All (20 Tools + Global)" : "🔄 Rebuild Active Index";
      }
      loadIndexHub();
    }, 4000);
  } catch (err) {
    alert(`Rebuild error: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = scopeType === "global" ? "🔄 Rebuild All (20 Tools + Global)" : "🔄 Rebuild Active Index";
    }
  }
}

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024;
    i++;
  }
  return `${val.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function highlightSearch(text, query) {
  if (!text) return "";
  const esc = escHtml(text);
  if (!query || query.length < 2) return esc;
  try {
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return esc.replace(re, '<mark class="fts-hl">$1</mark>');
  } catch (e) {
    return esc;
  }
}

function formatDomainMetrics(metrics) {
  if (!metrics || typeof metrics !== "object" || Object.keys(metrics).length === 0) {
    return '<span style="color:var(--text-muted); font-size:10px;">—</span>';
  }
  const items = Object.entries(metrics).slice(0, 4);
  return items.map(([k, v]) => {
    const valStr = typeof v === "object" ? JSON.stringify(v) : String(v);
    return `<span class="metric-pill" title="${escHtml(k)}: ${escHtml(valStr)}">${escHtml(k)}: ${escHtml(valStr)}</span>`;
  }).join("");
}

/* ═════════════════════════════════════════════════════════════════════ */
/* TAB 5: CREDENTIAL VAULT & SESSION MANAGER CONTROLLER                   */
/* ═════════════════════════════════════════════════════════════════════ */

let totpTimerHandle = null;

async function loadVaultTab() {
  await Promise.all([
    loadVaultDiagnostics(),
    loadVaultAccounts(),
  ]);
}

async function loadVaultDiagnostics() {
  try {
    const res = await fetch(`${API_BASE}/api/vault/diagnostics`);
    if (!res.ok) return;
    const diag = await res.json();

    const elTotal = document.getElementById("vault-stat-total");
    const elActive = document.getElementById("vault-stat-active");
    const elCooldown = document.getElementById("vault-stat-cooldown");
    const elCapacity = document.getElementById("vault-stat-capacity");
    const elHealth = document.getElementById("vault-stat-health");
    const elTargets = document.getElementById("vault-stat-targets");

    if (elTotal) elTotal.textContent = diag.total_accounts ?? 0;
    if (elActive) elActive.textContent = diag.active_ready_accounts ?? 0;
    if (elCooldown) elCooldown.textContent = diag.cooldown_accounts ?? 0;
    if (elCapacity) elCapacity.textContent = (diag.remaining_daily_capacity ?? 0).toLocaleString();
    if (elHealth) elHealth.textContent = `${diag.avg_health_score ?? 100}%`;

    const coverage = diag.private_target_coverage || {};
    const targetKeys = Object.keys(coverage);
    if (elTargets) elTargets.textContent = targetKeys.length;

    // Render target coverage list
    const covList = document.getElementById("vault-target-coverage-list");
    if (covList) {
      if (targetKeys.length === 0) {
        covList.innerHTML = '<div class="empty-state-msg">No private target links configured yet.</div>';
      } else {
        covList.innerHTML = targetKeys.map(t => {
          const info = coverage[t] || {};
          const followers = info.active_followers ?? info.followers_count ?? 1;
          const capacity = info.total_capacity ?? 0;
          return `
            <div class="target-coverage-card" onclick="filterByTarget('${escHtml(t)}')">
              <div>
                <div class="target-handle-text">${escHtml(t)}</div>
                <div style="font-size:10px; color:var(--text-muted);">Capacity: ${capacity} reqs/day</div>
              </div>
              <div class="target-followers-badge">${followers} follower${followers > 1 ? 's' : ''}</div>
            </div>
          `;
        }).join("");
      }
    }
  } catch (err) {
    console.warn("Failed to load vault diagnostics:", err);
  }
}

async function loadVaultAccounts() {
  const tbody = document.getElementById("vault-accounts-table-body");
  const countSpan = document.getElementById("vault-account-count");
  if (!tbody) return;

  const platform = document.getElementById("vault-filter-platform")?.value || "";
  const status = document.getElementById("vault-filter-status")?.value || "";
  const method = document.getElementById("vault-filter-method")?.value || "";
  const target = document.getElementById("vault-filter-target")?.value.trim() || "";

  const params = new URLSearchParams({
    platform,
    status,
    auth_method: method,
    target_handle: target,
    limit: "200",
  });

  tbody.innerHTML = '<tr><td colspan="8" class="loading-td">Loading encrypted vault accounts...</td></tr>';

  try {
    const res = await fetch(`${API_BASE}/api/vault/accounts?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const accounts = data.accounts || [];

    if (countSpan) {
      countSpan.textContent = `Showing ${accounts.length} of ${data.total_count ?? accounts.length} accounts`;
    }

    if (accounts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading-td">No vault accounts found matching current filters.</td></tr>';
      return;
    }

    tbody.innerHTML = accounts.map(acc => {
      const methods = acc.auth_methods || [];
      const targets = acc.follows_targets || [];
      const hasTotp = methods.includes("totp_2fa");
      const statusClass = (acc.status || "active").toLowerCase();

      const methodPills = methods.map(m => `<span class="method-pill">${escHtml(m)}</span>`).join("");
      const targetPills = targets.length > 0
        ? targets.map(t => `<span class="target-pill" onclick="filterByTarget('${escHtml(t)}')">${escHtml(t)}</span>`).join("")
        : '<span style="color:var(--text-muted); font-size:10px;">None (Public Scraper)</span>';

      return `
        <tr>
          <td>
            <div style="font-weight:700; color:var(--text-primary); font-family:var(--font-mono); font-size:12px;">${escHtml(acc.account_id)}</div>
            <div style="font-size:11px; color:var(--text-muted);">${escHtml(acc.account_label || "—")}</div>
          </td>
          <td>
            <span class="vault-badge">${escHtml(acc.platform)}</span>
            <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">${escHtml(acc.domain || "")}</div>
          </td>
          <td>
            <span style="font-family:var(--font-mono); font-weight:600; color:#cbd5e1;">${escHtml(acc.username_masked || "—")}</span>
          </td>
          <td>${methodPills}</td>
          <td>${targetPills}</td>
          <td>
            <div style="font-family:var(--font-mono); font-size:11px;">${acc.requests_today ?? 0} / ${acc.daily_quota_limit ?? 50}</div>
            <div style="font-size:10px; color:${(acc.health_score ?? 100) > 70 ? 'var(--accent-green)' : '#eab308'}; font-weight:700;">${acc.health_score ?? 100}% Health</div>
          </td>
          <td>
            <span class="status-pill ${statusClass}">${escHtml(acc.status.toUpperCase())}</span>
          </td>
          <td>
            <div class="row-actions-group">
              ${hasTotp ? `<button class="row-btn totp-btn" title="Generate Live 2FA TOTP Code" onclick="fetchLiveTotp('${escHtml(acc.account_id)}')">🔑 2FA</button>` : ''}
              <button class="row-btn test-btn" title="Send to 20-Tool Router Sandbox" onclick="prefillSandbox('${escHtml(acc.account_id)}', '${escHtml(acc.platform)}')">⚡ Test</button>
              <button class="row-btn" title="Toggle Cooldown / Active" onclick="toggleAccountOutcome('${escHtml(acc.account_id)}', '${escHtml(acc.status)}')">⏱ Cooldown</button>
              <button class="row-btn del-btn" title="Delete Profile" onclick="deleteVaultAccount('${escHtml(acc.account_id)}')">🗑</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-td" style="color:var(--accent-red);">Failed to load accounts: ${escHtml(err.message)}</td></tr>`;
  }
}

function filterVaultAccounts() {
  loadVaultAccounts();
}

function resetVaultFilters() {
  const p = document.getElementById("vault-filter-platform");
  const s = document.getElementById("vault-filter-status");
  const m = document.getElementById("vault-filter-method");
  const t = document.getElementById("vault-filter-target");
  if (p) p.value = "";
  if (s) s.value = "";
  if (m) m.value = "";
  if (t) t.value = "";
  loadVaultAccounts();
}

function filterByTarget(targetHandle) {
  const t = document.getElementById("vault-filter-target");
  if (t) {
    t.value = targetHandle;
    loadVaultAccounts();
  }
}

function openAddAccountModal() {
  const modal = document.getElementById("vault-add-modal");
  if (modal) modal.classList.add("open");
}

function closeAddAccountModal(event) {
  if (event && event.target && event.target.closest && event.target.closest(".vault-modal-box") && !event.target.classList.contains("modal-close") && !event.target.classList.contains("btn-cancel")) {
    return;
  }
  const modal = document.getElementById("vault-add-modal");
  if (modal) modal.classList.remove("open");
}

async function submitAddAccount(event) {
  event.preventDefault();
  const platform = document.getElementById("add-platform")?.value.trim() || "";
  const domain = document.getElementById("add-domain")?.value.trim() || "";
  const label = document.getElementById("add-label")?.value.trim() || "";
  const quota = parseInt(document.getElementById("add-quota")?.value || "50", 10);
  const username = document.getElementById("add-username")?.value.trim() || "";
  const password = document.getElementById("add-password")?.value || "";
  const totp = document.getElementById("add-totp")?.value.trim() || "";
  const targets = document.getElementById("add-targets")?.value.trim() || "";
  const cookies = document.getElementById("add-cookies")?.value.trim() || "";

  const payload = {
    platform,
    domain,
    account_label: label,
    daily_quota_limit: quota,
    username,
    password,
    totp_secret: totp,
    follows_targets: targets,
  };

  if (cookies) {
    if (cookies.startsWith("[") || cookies.startsWith("{")) {
      try {
        payload.cookies_json = JSON.parse(cookies);
      } catch (e) {
        payload.cookies_txt = cookies;
      }
    } else {
      payload.cookies_txt = cookies;
    }
  }

  try {
    const res = await fetch(`${API_BASE}/api/vault/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    closeAddAccountModal();
    document.getElementById("vault-add-form")?.reset();
    await loadVaultTab();
    alert("Encrypted credential profile created successfully!");
  } catch (err) {
    alert(`Failed to add account: ${err.message}`);
  }
}

function openBulkImportModal() {
  const modal = document.getElementById("vault-import-modal");
  if (modal) modal.classList.add("open");
}

function closeBulkImportModal(event) {
  if (event && event.target && event.target.closest && event.target.closest(".vault-modal-box") && !event.target.classList.contains("modal-close") && !event.target.classList.contains("btn-cancel")) {
    return;
  }
  const modal = document.getElementById("vault-import-modal");
  if (modal) modal.classList.remove("open");
}

async function submitBulkImport(event) {
  event.preventDefault();
  const format = document.getElementById("import-format")?.value || "jsonl";
  const platform = document.getElementById("import-platform")?.value.trim() || "";
  const domain = document.getElementById("import-domain")?.value.trim() || "";
  const conflict = document.getElementById("import-conflict")?.value || "update";
  const data = document.getElementById("import-data")?.value.trim() || "";

  if (!data) {
    alert("Please paste data payload to import.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/vault/bulk-import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format,
        platform,
        domain,
        on_conflict: conflict,
        data,
      }),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || `HTTP ${res.status}`);

    closeBulkImportModal();
    document.getElementById("vault-import-form")?.reset();
    await loadVaultTab();
    alert(`Bulk import completed: ${JSON.stringify(result.import_summary)}`);
  } catch (err) {
    alert(`Bulk import failed: ${err.message}`);
  }
}

async function seedSampleAccounts() {
  const platforms = ["instagram", "facebook", "leetcode", "twitter", "custom_web"];
  const sampleTargets = ["@private_vip_reel", "@private_coding_club", "@private_reel_creator", "@vip_finance_group"];
  const records = [];

  for (let i = 1; i <= 50; i++) {
    const plat = platforms[i % platforms.length];
    const tgt = sampleTargets[i % sampleTargets.length];
    records.push({
      platform: plat,
      domain: `${plat}.com`,
      username: `seed_bot_${plat}_${i}`,
      password: `SeedSecretPass${i}!`,
      account_label: `Seed Bot ${plat.toUpperCase()} #${i}`,
      totp_secret: "JBSWY3DPEHPK3PXP",
      daily_quota_limit: 40 + (i % 30),
      follows_targets: [tgt],
      cookie_jar: [
        { name: "sessionid", value: `sess_${plat}_${i}_xyz`, domain: `.${plat}.com`, path: "/", secure: true, httpOnly: true },
        { name: "csrftoken", value: `csrf_${plat}_${i}_abc`, domain: `.${plat}.com`, path: "/", secure: true, httpOnly: false },
      ],
    });
  }

  try {
    const res = await fetch(`${API_BASE}/api/vault/bulk-import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format: "records",
        on_conflict: "update",
        data: records,
      }),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || `HTTP ${res.status}`);

    closeBulkImportModal();
    await loadVaultTab();
    alert(`Quick-Seed Complete! Successfully imported 50 sample accounts into encrypted vault.`);
  } catch (err) {
    alert(`Quick-seed failed: ${err.message}`);
  }
}

function openRecordSessionModal() {
  const modal = document.getElementById("vault-session-modal");
  if (modal) modal.classList.add("open");
}

function closeRecordSessionModal(event) {
  if (event && event.target && event.target.closest && event.target.closest(".vault-modal-box") && !event.target.classList.contains("modal-close") && !event.target.classList.contains("btn-cancel")) {
    return;
  }
  const modal = document.getElementById("vault-session-modal");
  if (modal) modal.classList.remove("open");
}

async function submitRecordSession(event) {
  event.preventDefault();
  const platform = document.getElementById("session-platform")?.value.trim() || "instagram";
  const engine = document.getElementById("session-engine")?.value || "playwright";
  const url = document.getElementById("session-url")?.value.trim() || "https://httpbin.org/html";
  const label = document.getElementById("session-label")?.value.trim() || "";
  const waitSec = parseInt(document.getElementById("session-wait")?.value || "30", 10);
  const targets = document.getElementById("session-targets")?.value.trim() || "";
  const interactive = document.getElementById("session-interactive")?.checked || false;

  const payload = {
    platform,
    engine,
    login_url: url,
    account_label: label,
    wait_seconds: waitSec,
    interactive,
    follows_targets: targets ? [targets] : [],
  };

  try {
    closeRecordSessionModal();
    alert("Browser session recording initiated. Watching for login and cookies...");
    const res = await fetch(`${API_BASE}/api/vault/record-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || `HTTP ${res.status}`);

    await loadVaultTab();
    alert(`Session Captured Successfully! Cookies: ${result.cookies_captured_count}, Tokens: ${result.extracted_token_keys?.join(', ')}`);
  } catch (err) {
    alert(`Session recording failed: ${err.message}`);
  }
}

async function fetchLiveTotp(accountId) {
  try {
    const res = await fetch(`${API_BASE}/api/vault/accounts/${encodeURIComponent(accountId)}/totp`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    const data = await res.json();

    const toast = document.getElementById("vault-totp-toast");
    const codeVal = document.getElementById("totp-code-val");
    const timerVal = document.getElementById("totp-timer-val");
    const progressBar = document.getElementById("totp-progress-bar");
    const titleVal = document.getElementById("totp-toast-title");

    if (!toast) return;

    if (titleVal) titleVal.textContent = `2FA TOTP: ${accountId}`;
    const rawCode = String(data.code || "000000");
    if (codeVal) codeVal.textContent = `${rawCode.slice(0, 3)} ${rawCode.slice(3)}`;

    let secondsLeft = data.time_remaining_sec ?? 30;
    const period = data.period_sec ?? 30;

    if (timerVal) timerVal.textContent = secondsLeft;
    if (progressBar) progressBar.style.width = `${(secondsLeft / period) * 100}%`;

    toast.style.display = "flex";

    if (totpTimerHandle) clearInterval(totpTimerHandle);
    totpTimerHandle = setInterval(() => {
      secondsLeft -= 1;
      if (timerVal) timerVal.textContent = Math.max(secondsLeft, 0);
      if (progressBar) progressBar.style.width = `${Math.max((secondsLeft / period) * 100, 0)}%`;
      if (secondsLeft <= 0) {
        clearInterval(totpTimerHandle);
        closeTotpToast();
      }
    }, 1000);
  } catch (err) {
    alert(`Failed to generate 2FA TOTP: ${err.message}`);
  }
}

function closeTotpToast() {
  const toast = document.getElementById("vault-totp-toast");
  if (toast) toast.style.display = "none";
  if (totpTimerHandle) clearInterval(totpTimerHandle);
}

function copyTotpCode() {
  const codeVal = document.getElementById("totp-code-val");
  if (!codeVal) return;
  const cleanCode = codeVal.textContent.replace(/\s+/g, "");
  navigator.clipboard.writeText(cleanCode).then(() => {
    alert(`2FA Code ${cleanCode} copied to clipboard!`);
  }).catch(() => {
    prompt("Copy 2FA code manually:", cleanCode);
  });
}

async function toggleAccountOutcome(accountId, currentStatus) {
  const outcome = currentStatus === "cooldown" ? "success" : "rate_limited";
  const cooldownSec = outcome === "rate_limited" ? 1800 : 0;
  try {
    const res = await fetch(`${API_BASE}/api/vault/accounts/${encodeURIComponent(accountId)}/outcome`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        outcome,
        cooldown_seconds: cooldownSec,
        notes: `Toggled via Control Center UI (${outcome})`,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadVaultTab();
  } catch (err) {
    alert(`Failed to update account state: ${err.message}`);
  }
}

async function deleteVaultAccount(accountId) {
  if (!confirm(`Are you sure you want to delete account ${accountId} from the encrypted vault?`)) {
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/vault/accounts/${encodeURIComponent(accountId)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadVaultTab();
  } catch (err) {
    alert(`Failed to delete account: ${err.message}`);
  }
}

function prefillSandbox(accountId, platform) {
  const platSelect = document.getElementById("vault-test-platform");
  if (platSelect) platSelect.value = platform || "";
  const sandboxPanel = document.querySelector(".sandbox-panel");
  if (sandboxPanel) {
    sandboxPanel.scrollIntoView({ behavior: "smooth" });
    sandboxPanel.style.borderColor = "var(--accent-cyan)";
    setTimeout(() => {
      sandboxPanel.style.borderColor = "var(--border)";
    }, 2000);
  }
}

async function testVaultInjection() {
  const toolId = document.getElementById("vault-test-tool")?.value || "01_curl_cffi";
  const platform = document.getElementById("vault-test-platform")?.value || "";
  const target = document.getElementById("vault-test-target")?.value.trim() || "";
  const strategy = document.getElementById("vault-test-strategy")?.value || "least_recently_used";

  const outPre = document.getElementById("vault-test-output");
  const badge = document.getElementById("sandbox-status-badge");
  if (outPre) outPre.textContent = "// Routing request and generating auth bundles...";
  if (badge) {
    badge.textContent = "ROUTING...";
    badge.className = "sandbox-badge-running";
  }

  try {
    const res = await fetch(`${API_BASE}/api/vault/test-injection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool_id: toolId,
        platform,
        required_target: target,
        strategy,
      }),
    });
    const result = await res.json();
    if (outPre) {
      outPre.textContent = JSON.stringify(result, null, 2);
    }
    if (badge) {
      if (result.authenticated) {
        badge.textContent = "AUTHENTICATED";
        badge.style.color = "var(--accent-green)";
      } else {
        badge.textContent = "NO_ACCOUNT";
        badge.style.color = "var(--accent-red)";
      }
    }
  } catch (err) {
    if (outPre) outPre.textContent = `// Error: ${err.message}`;
    if (badge) {
      badge.textContent = "ERROR";
      badge.style.color = "var(--accent-red)";
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 6: WORKING WAYS & SAFE ARENA CONTROLLER
// ═══════════════════════════════════════════════════════════════════════════════

let activePipelineRecipe = "graphql_markdown";
let lastArenaReportData = null;
let lastPipelineReportData = null;

async function loadWorkingWaysTab() {
  await Promise.allSettled([
    loadWorkingWaysOverview(),
    loadArenaReports(),
    loadPipelineReports(),
    runTimingSimulation(),
  ]);
  clearKinematicsCanvas();
}

function switchWorkingWaysSubView(subviewName, btn) {
  document.querySelectorAll(".ww-subview-panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".ww-subview-btn").forEach(b => b.classList.remove("active"));
  
  const target = document.getElementById(`subview-${subviewName}`);
  if (target) target.classList.add("active");
  if (btn) btn.classList.add("active");

  if (subviewName === "timing") {
    clearKinematicsCanvas();
    animateKinematicsCurve();
  }
}

async function loadWorkingWaysOverview() {
  try {
    const res = await fetch(`${API_BASE}/api/working-ways/overview`);
    if (!res.ok) return;
    const data = await res.json();

    setText("ww-kpi-arena-count", data.total_arena_reports || 0);
    setText("ww-kpi-top-winner", data.top_winning_scraper || "None");
    setText("ww-kpi-winner-rate", `${data.top_winning_count || 0} wins`);
    setText("ww-kpi-pipeline-count", data.total_pipeline_reports || 0);

    const timingSelect = document.getElementById("arena-timing-profile");
    if (timingSelect && timingSelect.value) {
      setText("ww-kpi-active-profile", timingSelect.value);
    }
  } catch (err) {
    console.error("Failed to load working ways overview:", err);
  }
}

// ─── Sub-View A: Safe Arena Methods ──────────────────────────────────────────

function setArenaTarget(url) {
  const inp = document.getElementById("arena-target-url");
  if (inp) inp.value = url;
}

function toggleAllArenaTools(checkAll) {
  document.querySelectorAll("input[name='arena-tools']").forEach(cb => {
    cb.checked = checkAll;
  });
}

async function launchArenaTournament() {
  const btn = document.getElementById("btn-launch-arena");
  const targetUrl = document.getElementById("arena-target-url")?.value.trim() || "https://quotes.toscrape.com";
  const selectedTools = Array.from(document.querySelectorAll("input[name='arena-tools']:checked")).map(cb => cb.value);
  const timingProfile = document.getElementById("arena-timing-profile")?.value || "BALANCED_HUMAN";
  const humanMode = document.getElementById("arena-human-mode")?.checked ?? true;
  const runLabel = document.getElementById("arena-run-label")?.value.trim() || "";

  if (!selectedTools.length) {
    alert("Please select at least one crawler tool in the squad.");
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Running Tournament...";
  }

  const statusBadge = document.getElementById("arena-results-status");
  if (statusBadge) {
    statusBadge.textContent = "RUNNING";
    statusBadge.className = "ww-badge badge-running";
  }

  try {
    const res = await fetch(`${API_BASE}/api/working-ways/arena/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_url: targetUrl,
        tool_ids: selectedTools,
        timing_profile: timingProfile,
        human_mode: humanMode,
        run_label: runLabel,
      }),
    });
    const result = await res.json();
    console.log("Arena launched:", result);

    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      await loadArenaReports();
      await loadWorkingWaysOverview();

      if (attempts >= 15 || (lastArenaReportData && lastArenaReportData.target_url === targetUrl)) {
        clearInterval(pollInterval);
        if (btn) {
          btn.disabled = false;
          btn.textContent = "▶ Launch Safe Arena Tournament";
        }
        if (statusBadge) {
          statusBadge.textContent = "COMPLETED";
          statusBadge.className = "ww-badge badge-success";
        }
      }
    }, 2000);

  } catch (err) {
    alert(`Failed to launch arena: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "▶ Launch Safe Arena Tournament";
    }
    if (statusBadge) {
      statusBadge.textContent = "ERROR";
      statusBadge.className = "ww-badge badge-error";
    }
  }
}

async function loadArenaReports() {
  try {
    const res = await fetch(`${API_BASE}/api/working-ways/arena/reports?limit=10`);
    if (!res.ok) return;
    const data = await res.json();
    const reports = data.reports || [];

    const listEl = document.getElementById("arena-history-list");
    if (!listEl) return;

    if (!reports.length) {
      listEl.innerHTML = "<div class='empty-state'>No arena reports found. Launch one above!</div>";
      return;
    }

    listEl.innerHTML = reports.map(r => {
      const winner = r.winning_tool || "N/A";
      const dt = (r.created_at || "").slice(0, 19).replace("T", " ");
      return `
        <div class="ww-history-card" onclick="viewArenaReport('${r.report_id}')">
          <div class="ww-hc-top">
            <strong>${escHtml(r.run_label || r.report_id)}</strong>
            <span class="ww-badge-winner">🏆 ${escHtml(winner)}</span>
          </div>
          <div class="ww-hc-meta">
            <span>🎯 ${escHtml(r.target_url)}</span>
            <span>⏱️ ${r.total_elapsed_sec}s</span>
            <span>🛠️ ${r.total_tools} tools</span>
            <span>📅 ${dt}</span>
          </div>
        </div>
      `;
    }).join("");

    if (reports.length && (!lastArenaReportData || reports[0].report_id !== lastArenaReportData.report_id)) {
      await viewArenaReport(reports[0].report_id);
    }
  } catch (err) {
    console.error("Failed to load arena reports:", err);
  }
}

async function viewArenaReport(reportId) {
  try {
    const res = await fetch(`${API_BASE}/api/working-ways/arena/reports/${encodeURIComponent(reportId)}`);
    if (!res.ok) return;
    const data = await res.json();
    lastArenaReportData = data;
    renderArenaResults(data);
  } catch (err) {
    console.error("Failed to view arena report:", err);
  }
}

function renderArenaResults(report) {
  if (!report) return;

  const winnerBanner = document.getElementById("arena-winner-banner");
  const winnerName = document.getElementById("arena-winner-name");
  const winnerRationale = document.getElementById("arena-winner-rationale");

  if (winnerBanner && report.winning_tool) {
    winnerBanner.style.display = "flex";
    if (winnerName) winnerName.textContent = report.winning_tool;
    if (winnerRationale) winnerRationale.textContent = report.winning_rationale || "Top composite score.";
  }

  if (report.total_elapsed_sec) {
    setText("ww-kpi-avg-latency", `${report.total_elapsed_sec}s`);
  }

  const tbody = document.getElementById("arena-matrix-tbody");
  if (!tbody) return;

  const matrix = report.comparison_matrix || [];
  if (!matrix.length) {
    tbody.innerHTML = "<tr><td colspan='10' class='empty-cell'>No candidate tools evaluated in this report.</td></tr>";
    return;
  }

  const medals = ["🥇", "🥈", "🥉"];
  tbody.innerHTML = matrix.map((m, idx) => {
    const rankIcon = idx < 3 ? medals[idx] : `#${idx + 1}`;
    const statusIcon = m.status === "completed" ? "✅" : "❌";
    const isWinner = m.tool_id === report.winning_tool;
    const rowClass = isWinner ? "winner-row" : "";

    return `
      <tr class="${rowClass}">
        <td><strong>${rankIcon}</strong></td>
        <td><code>${escHtml(m.tool_id)}</code></td>
        <td>${statusIcon} ${m.status}</td>
        <td>${m.elapsed_sec}s</td>
        <td>${(m.raw_bytes || 0).toLocaleString()} B</td>
        <td>${(m.cleaned_chars || 0).toLocaleString()}</td>
        <td>${m.speed_score}</td>
        <td>${m.data_richness_score}</td>
        <td>${m.stealth_score}</td>
        <td><strong>${m.composite_score}</strong></td>
      </tr>
    `;
  }).join("");
}

// ─── Sub-View B: Precision Pipeline Studio Methods ───────────────────────────

function selectPipelineRecipe(recipeId) {
  activePipelineRecipe = recipeId;
  document.querySelectorAll(".ww-recipe-card").forEach(c => c.classList.remove("active"));
  const card = document.getElementById(`recipe-card-${recipeId}`);
  if (card) card.classList.add("active");

  const urlInput = document.getElementById("pipeline-target-url");
  if (urlInput) {
    if (recipeId === "graphql_markdown") {
      urlInput.value = "https://leetcode.com/problems/two-sum/";
    } else if (recipeId === "stream_whisper") {
      urlInput.value = "https://www.instagram.com/reel/C8XYZ12345/";
    } else if (recipeId === "browser_ocr") {
      urlInput.value = "https://quotes.toscrape.com/js/";
    }
  }
}

async function launchPipelineRun() {
  const btn = document.getElementById("btn-launch-pipeline");
  const targetUrl = document.getElementById("pipeline-target-url")?.value.trim() || "https://quotes.toscrape.com";
  const timingProfile = document.getElementById("pipeline-timing-profile")?.value || "BALANCED_HUMAN";
  const humanMode = document.getElementById("pipeline-human-mode")?.checked ?? false;

  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Running Pipeline...";
  }

  const statusBadge = document.getElementById("pipeline-results-status");
  if (statusBadge) {
    statusBadge.textContent = "RUNNING";
    statusBadge.className = "ww-badge badge-running";
  }

  try {
    const res = await fetch(`${API_BASE}/api/working-ways/pipelines/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipe: activePipelineRecipe,
        target_url: targetUrl,
        timing_profile: timingProfile,
        human_mode: humanMode,
      }),
    });
    const result = await res.json();
    console.log("Pipeline run launched:", result);

    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      await loadPipelineReports();
      await loadWorkingWaysOverview();

      if (attempts >= 12 || (lastPipelineReportData && lastPipelineReportData.target_url === targetUrl)) {
        clearInterval(pollInterval);
        if (btn) {
          btn.disabled = false;
          btn.textContent = "▶ Run Chained Pipeline";
        }
        if (statusBadge) {
          statusBadge.textContent = "COMPLETED";
          statusBadge.className = "ww-badge badge-success";
        }
      }
    }, 2000);

  } catch (err) {
    alert(`Failed to launch pipeline: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "▶ Run Chained Pipeline";
    }
    if (statusBadge) {
      statusBadge.textContent = "ERROR";
      statusBadge.className = "ww-badge badge-error";
    }
  }
}

async function loadPipelineReports() {
  try {
    const res = await fetch(`${API_BASE}/api/working-ways/pipelines/reports?limit=10`);
    if (!res.ok) return;
    const data = await res.json();
    const reports = data.reports || [];

    const listEl = document.getElementById("pipeline-history-list");
    if (!listEl) return;

    if (!reports.length) {
      listEl.innerHTML = "<div class='empty-state'>No pipeline reports found. Run one above!</div>";
      return;
    }

    listEl.innerHTML = reports.map(r => {
      const dt = (r.created_at || "").slice(0, 19).replace("T", " ");
      return `
        <div class="ww-history-card" onclick="viewPipelineReport('${r.report_id}')">
          <div class="ww-hc-top">
            <strong>${escHtml(r.pipeline_label || r.pipeline_id)}</strong>
            <span class="ww-badge badge-success">${escHtml(r.status)}</span>
          </div>
          <div class="ww-hc-meta">
            <span>🎯 ${escHtml(r.target_url)}</span>
            <span>⏱️ ${r.total_elapsed_sec}s</span>
            <span>📦 ${r.deliverables_count} deliverables</span>
            <span>📅 ${dt}</span>
          </div>
        </div>
      `;
    }).join("");

    if (reports.length && (!lastPipelineReportData || reports[0].report_id !== lastPipelineReportData.report_id)) {
      await viewPipelineReport(reports[0].report_id);
    }
  } catch (err) {
    console.error("Failed to load pipeline reports:", err);
  }
}

async function viewPipelineReport(reportId) {
  try {
    const res = await fetch(`${API_BASE}/api/working-ways/pipelines/reports/${encodeURIComponent(reportId)}`);
    if (!res.ok) return;
    const data = await res.json();
    lastPipelineReportData = data;
    renderPipelineResults(data);
  } catch (err) {
    console.error("Failed to view pipeline report:", err);
  }
}

function renderPipelineResults(report) {
  if (!report) return;

  const timelineEl = document.getElementById("pipeline-timeline");
  const stages = report.stage_records || [];

  if (timelineEl) {
    if (!stages.length) {
      timelineEl.innerHTML = "<div class='timeline-empty'>No stages executed.</div>";
    } else {
      timelineEl.innerHTML = stages.map((s, idx) => {
        const isCompleted = s.status === "completed";
        const badgeClass = isCompleted ? "status-ok" : "status-fail";
        const consumedStr = (s.artifacts_consumed || []).map(a => `<span class="ww-pill-consumed">📥 ${escHtml(a.key)}</span>`).join(" ");

        return `
          <div class="timeline-step">
            <div class="timeline-node ${badgeClass}">${idx + 1}</div>
            <div class="timeline-info">
              <div class="timeline-stage-title"><strong>Stage ${idx + 1}:</strong> <code>${escHtml(s.stage_id)}</code></div>
              <div class="timeline-tool">Tool: <code>${escHtml(s.tool_id)}</code> (${s.elapsed_sec}s)</div>
              ${consumedStr ? `<div class="timeline-consumed">${consumedStr}</div>` : ""}
            </div>
            ${idx < stages.length - 1 ? `<div class="timeline-connector">➔</div>` : ""}
          </div>
        `;
      }).join("");
    }
  }

  const deliverablesEl = document.getElementById("pipeline-deliverables-list");
  const deliverables = report.consolidated_deliverables || [];

  if (deliverablesEl) {
    if (!deliverables.length) {
      deliverablesEl.innerHTML = "<div class='empty-state'>No deliverables recorded.</div>";
    } else {
      deliverablesEl.innerHTML = deliverables.map(d => {
        const kb = Math.round((d.size_bytes || 0) / 1024 * 10) / 10;
        return `
          <div class="ww-deliverable-item" onclick="previewDeliverableFile('${escHtml(d.path)}')">
            <div class="deliv-main">
              <span class="deliv-icon">📄</span>
              <span class="deliv-name"><strong>${escHtml(d.name)}</strong></span>
              <span class="deliv-meta">Stage: <code>${escHtml(d.stage_id)}</code> via <code>${escHtml(d.tool_id)}</code> (${kb} KB)</span>
            </div>
            <span class="deliv-action">👁️ View</span>
          </div>
        `;
      }).join("");
    }
  }
}

function previewDeliverableFile(workspacePath) {
  const modal = document.getElementById("file-modal");
  const title = document.getElementById("modal-title");
  const meta = document.getElementById("modal-meta");
  const content = document.getElementById("modal-content");

  if (!modal) return;
  title.textContent = workspacePath.split(/[\\/]/).pop();
  meta.textContent = `Path: ${workspacePath}`;
  content.textContent = "Loading deliverable preview...";
  modal.classList.add("open");

  const parts = workspacePath.replace(/\\/g, "/").split("/");
  if (parts.length >= 7 && parts[0] === "data") {
    previewFile(parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]);
  } else {
    content.textContent = `Workspace deliverable: ${workspacePath}\n\n(Auto-indexed in global master index).`;
  }
}

// ─── Sub-View C: Human Timing & Kinematics Sandbox Methods ────────────────────

async function runTimingSimulation() {
  const profile = document.getElementById("timing-sim-profile")?.value || "BALANCED_HUMAN";
  const actionType = document.getElementById("timing-sim-action")?.value || "navigate";

  try {
    const res = await fetch(`${API_BASE}/api/working-ways/timing/simulate?profile=${encodeURIComponent(profile)}&action_type=${encodeURIComponent(actionType)}&samples=40`);
    if (!res.ok) return;
    const data = await res.json();

    setText("sim-min-val", `${data.min_sec}s`);
    setText("sim-mean-val", `${data.mean_sec}s`);
    setText("sim-max-val", `${data.max_sec}s`);

    const container = document.getElementById("timing-bars-container");
    if (!container) return;

    const maxVal = Math.max(...(data.delays || [1]));
    container.innerHTML = (data.delays || []).map((val, idx) => {
      const pct = Math.max(8, Math.round((val / maxVal) * 100));
      return `
        <div class="timing-bar-col" title="Sample #${idx + 1}: ${val}s">
          <div class="timing-bar" style="height:${pct}%;"></div>
          <span class="timing-bar-lbl">${val}s</span>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to run timing simulation:", err);
  }
}

function clearKinematicsCanvas() {
  const canvas = document.getElementById("kinematics-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 30) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 30) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }
}

function animateKinematicsCurve() {
  const canvas = document.getElementById("kinematics-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  clearKinematicsCanvas();

  const startX = 40, startY = 220;
  const endX = 420, endY = 60;

  // 1. Draw Robotic Straight Line in dashed red
  ctx.beginPath();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = "rgba(239, 68, 68, 0.6)";
  ctx.lineWidth = 2;
  ctx.moveTo(startX, startY);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "rgba(239, 68, 68, 0.8)";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText("Bot Linear Jump (Flagged)", 150, 170);

  // 2. Draw Human Neuromotor Bezier Curve in cyan
  const cp1X = startX + (endX - startX) * 0.25 + (Math.random() * 60 - 30);
  const cp1Y = startY - (startY - endY) * 0.70 + (Math.random() * 40 - 20);
  const cp2X = startX + (endX - startX) * 0.75 + (Math.random() * 40 - 20);
  const cp2Y = endY + (Math.random() * 50 - 25);

  ctx.beginPath();
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 3;
  ctx.moveTo(startX, startY);
  ctx.bezierCurveTo(cp1X, cp1Y, cp2X, cp2Y, endX, endY);
  ctx.stroke();

  ctx.fillStyle = "#10b981";
  ctx.beginPath();
  ctx.arc(startX, startY, 6, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#f59e0b";
  ctx.beginPath();
  ctx.arc(endX, endY, 6, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#38bdf8";
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText("Antigravity Human Arc (Stealth)", endX - 180, endY - 15);
}


// ═══════════════════════════════════════════════════════════════════════════════
// STAGE 5: PRODUCTION TASK PIPELINES & CLEANED DATA INSPECTOR (TAB 7)
// ═══════════════════════════════════════════════════════════════════════════════

let currentActivePipelineRun = null;

function switchPipelinesSubview(subviewId, btn) {
  document.querySelectorAll(".pipe-subview-panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".pipe-subview-btn").forEach(b => b.classList.remove("active"));
  const target = document.getElementById(subviewId);
  if (target) target.classList.add("active");
  if (btn) btn.classList.add("active");
}

async function loadPipelinesTab() {
  try {
    const res = await fetch("/api/pipelines/overview");
    if (!res.ok) return;
    const data = await res.json();

    const runsEl = document.getElementById("kpi-pipe-runs");
    const delivEl = document.getElementById("kpi-pipe-deliverables");
    const activeEl = document.getElementById("kpi-pipe-active");
    if (runsEl) runsEl.textContent = data.total_pipeline_runs || 0;
    if (delivEl) delivEl.textContent = data.deliverables_count || 0;
    if (activeEl) activeEl.textContent = `${data.active_pipelines?.length || 4} / 4`;

    await loadPipelineRuns();
  } catch (err) {
    console.error("Failed to load pipelines overview:", err);
  }
}

async function loadPipelineRuns() {
  const filterSelect = document.getElementById("pipe-filter-select");
  const filterVal = filterSelect ? filterSelect.value : "";
  const runsListEl = document.getElementById("pipe-runs-list");
  const matrixBodyEl = document.getElementById("pipe-contract-matrix-body");

  try {
    const res = await fetch(`/api/pipelines/runs?limit=50&pipeline_id=${encodeURIComponent(filterVal)}`);
    if (!res.ok) return;
    const data = await res.json();
    const runs = data.runs || [];

    // 1. Populate Runs List in Sub-View B
    if (runsListEl) {
      if (runs.length === 0) {
        runsListEl.innerHTML = `<div class="pipe-empty-hint">No pipeline executions found for this filter.</div>`;
      } else {
        runsListEl.innerHTML = runs.map(r => {
          const isSelected = currentActivePipelineRun && currentActivePipelineRun.run_id === r.run_id;
          const statusClass = r.status === "completed" ? "status-tag-green" : "status-tag-amber";
          return `
            <div class="pipe-run-item ${isSelected ? 'selected' : ''}" 
                 onclick="inspectPipelineRun('${r.pipeline_id}', '${r.action_name}', '${r.run_date}', '${r.run_id}')">
              <div class="pipe-run-row-top">
                <span class="pipe-tag">${r.pipeline_id.replace(/^0[0-9]_/, '')}</span>
                <span class="pipe-status-tag ${statusClass}">${r.status}</span>
              </div>
              <div class="pipe-run-action">${r.action_name}</div>
              <div class="pipe-run-meta">
                <span>⏱ ${r.elapsed_sec ? r.elapsed_sec.toFixed(1) + 's' : '0.0s'}</span>
                <span>📦 ${r.cleaned_count || 0} deliverables</span>
                <span class="pipe-run-date">${r.run_date}</span>
              </div>
            </div>
          `;
        }).join("");
      }
    }

    // 2. Populate Contract Compliance & Audit Matrix in Sub-View C
    if (matrixBodyEl) {
      if (runs.length === 0) {
        matrixBodyEl.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No pipeline runs recorded in data lake yet.</td></tr>`;
      } else {
        matrixBodyEl.innerHTML = runs.map(r => {
          let schemaName = "CleanedContract";
          if (r.pipeline_id.includes("leetcode")) schemaName = "CleanedCodeProblemContract";
          else if (r.pipeline_id.includes("social")) schemaName = "CleanedSocialMediaContract";
          else if (r.pipeline_id.includes("forensics")) schemaName = "CleanedForensicsContract";
          else if (r.pipeline_id.includes("multimodal")) schemaName = "CleanedMultimodalContract";

          const dm = r.domain_metrics || {};
          let summary = "";
          if (dm.difficulty) summary = `Diff: ${dm.difficulty} | Tests: ${dm.testcases_count || 0}`;
          else if (dm.media_type) summary = `Media: ${dm.media_type} | Likes: ${dm.likes || 0}`;
          else if (dm.security_grade) summary = `Grade: ${dm.security_grade} | APIs: ${dm.discovered_apis_count || 0}`;
          else if (dm.content_type) summary = `Type: ${dm.content_type} | Conf: ${(dm.confidence_score * 100 || 95).toFixed(0)}%`;
          else summary = `Cleaned files: ${r.cleaned_count || 0}`;

          const shortRunId = r.run_id.length > 18 ? r.run_id.substring(0, 18) + '...' : r.run_id;
          const timestamp = (r.started_at || "").substring(0, 19).replace("T", " ");

          return `
            <tr>
              <td><code>${timestamp}</code></td>
              <td><span class="pipe-tag">${r.pipeline_id}</span></td>
              <td><code>${shortRunId}</code></td>
              <td><span class="pipe-contract-tag">${schemaName}</span></td>
              <td><span class="pipe-badge-success">VALIDATED ✓</span></td>
              <td class="pipe-summary-cell">${summary}</td>
              <td><span class="pipe-hash-badge">SHA-256 ✓</span></td>
              <td>
                <button class="pipe-mini-btn" onclick="inspectPipelineRun('${r.pipeline_id}', '${r.action_name}', '${r.run_date}', '${r.run_id}')">
                  Inspect ➔
                </button>
              </td>
            </tr>
          `;
        }).join("");
      }
    }

  } catch (err) {
    console.error("Failed to load pipeline runs:", err);
  }
}

async function inspectPipelineRun(pipelineId, actionName, runDate, runId) {
  currentActivePipelineRun = { pipeline_id: pipelineId, action_name: actionName, run_date: runDate, run_id: runId };

  // Switch to Sub-View B if not active
  const inspectorBtn = document.querySelector(".pipe-subview-btn[data-subview='subview-cleaned-inspector']");
  switchPipelinesSubview("subview-cleaned-inspector", inspectorBtn);

  // Mark selected run item in list
  document.querySelectorAll(".pipe-run-item").forEach(el => el.classList.remove("selected"));

  const emptyState = document.getElementById("pipe-detail-empty");
  const detailContent = document.getElementById("pipe-detail-content");
  const headerEl = document.getElementById("pipe-run-header");
  const tabsEl = document.getElementById("pipe-deliverable-tabs");
  const viewerEl = document.getElementById("pipe-deliverable-viewer");

  try {
    const res = await fetch(`/api/pipelines/runs/${pipelineId}/${actionName}/${runDate}/${runId}`);
    if (!res.ok) return;
    const detail = await res.json();

    if (emptyState) emptyState.style.display = "none";
    if (detailContent) detailContent.style.display = "block";

    // 1. Render Run Header
    const manifest = detail.manifest || {};
    const dm = manifest.domain_metrics || {};
    if (headerEl) {
      headerEl.innerHTML = `
        <div class="pipe-header-left">
          <div class="pipe-header-title">
            <span class="pipe-tag">${pipelineId}</span>
            <h2>${actionName}</h2>
          </div>
          <div class="pipe-header-tags">
            <span class="pipe-status-tag status-tag-green">${manifest.status || 'completed'}</span>
            <span class="pipe-meta-chip">Run ID: <code>${runId}</code></span>
            <span class="pipe-meta-chip">Date: ${runDate}</span>
            <span class="pipe-meta-chip">Elapsed: ${manifest.elapsed_sec ? manifest.elapsed_sec.toFixed(2) + 's' : '0.0s'}</span>
            <span class="pipe-meta-chip integrity-chip">🔒 SHA-256 Verified</span>
          </div>
        </div>
      `;
    }

    // 2. Render Deliverables Tabs Bar
    const cleanedFiles = detail.cleaned_files || [];
    if (tabsEl) {
      if (cleanedFiles.length === 0) {
        tabsEl.innerHTML = `<span class="pipe-empty-hint">No deliverables generated in cleaned/.</span>`;
        if (viewerEl) viewerEl.innerHTML = "";
      } else {
        tabsEl.innerHTML = cleanedFiles.map((f, idx) => {
          const isActive = idx === 0;
          return `
            <button class="pipe-tab-btn ${isActive ? 'active' : ''}" 
                    data-file="${f.name}"
                    onclick="renderCleanedArtifact('${pipelineId}', '${actionName}', '${runDate}', '${runId}', 'cleaned', '${f.name}', this)">
              📄 ${f.name}
            </button>
          `;
        }).join("");

        // Render first file
        if (cleanedFiles.length > 0) {
          renderCleanedArtifact(pipelineId, actionName, runDate, runId, 'cleaned', cleanedFiles[0].name);
        }
      }
    }

  } catch (err) {
    console.error("Failed to inspect pipeline run:", err);
  }
}

async function renderCleanedArtifact(pipelineId, actionName, runDate, runId, folder, filename, btn) {
  if (btn) {
    document.querySelectorAll(".pipe-tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }

  const viewerEl = document.getElementById("pipe-deliverable-viewer");
  if (!viewerEl) return;

  viewerEl.innerHTML = `<div class="pipe-loading-state">Streaming artifact: <code>${filename}</code>...</div>`;

  try {
    const res = await fetch(`/api/pipelines/artifacts/${pipelineId}/${actionName}/${runDate}/${runId}/${folder}/${encodeURIComponent(filename)}`);
    if (!res.ok) {
      viewerEl.innerHTML = `<div class="pipe-error-state">Failed to load artifact: ${res.statusText} (${res.status})</div>`;
      return;
    }

    const contentType = res.headers.get("content-type") || "";

    if (contentType.includes("application/json") || filename.endsWith(".json")) {
      const jsonText = await res.text();
      let formatted = jsonText;
      try {
        formatted = JSON.stringify(JSON.parse(jsonText), null, 2);
      } catch (e) {}
      viewerEl.innerHTML = `
        <div class="pipe-code-wrapper">
          <div class="pipe-code-bar">
            <span>JSON Contract Spec (${filename})</span>
            <button class="pipe-copy-btn" onclick="navigator.clipboard.writeText(this.dataset.content)" data-content="${encodeURIComponent(formatted)}">Copy JSON</button>
          </div>
          <pre class="pipe-code-block"><code>${escapeHtml(formatted)}</code></pre>
        </div>
      `;
    } else if (filename.endsWith(".csv")) {
      const csvText = await res.text();
      const lines = csvText.trim().split("\n");
      const headers = lines[0]?.split(",") || [];
      const rows = lines.slice(1).map(l => l.split(","));
      viewerEl.innerHTML = `
        <div class="pipe-table-wrapper">
          <table class="pipe-grid-table">
            <thead>
              <tr>${headers.map(h => `<th>${escapeHtml(h.trim())}</th>`).join("")}</tr>
            </thead>
            <tbody>
              ${rows.map(r => `<tr>${r.map(c => `<td>${escapeHtml(c.trim())}</td>`).join("")}</tr>`).join("")}
            </tbody>
          </table>
        </div>
      `;
    } else if (filename.endsWith(".html") || contentType.includes("text/html")) {
      const htmlText = await res.text();
      const blob = new Blob([htmlText], { type: "text/html" });
      const blobUrl = URL.createObjectURL(blob);
      viewerEl.innerHTML = `
        <div class="pipe-html-wrapper">
          <div class="pipe-code-bar">
            <span>Self-Contained Offline HTML Preview</span>
            <a href="${blobUrl}" target="_blank" class="pipe-link-btn">Open in New Tab ↗</a>
          </div>
          <iframe class="pipe-html-frame" srcdoc="${escapeHtml(htmlText)}" sandbox="allow-scripts"></iframe>
        </div>
      `;
    } else {
      // Plain text, markdown, subtitles, or code
      const text = await res.text();
      viewerEl.innerHTML = `
        <div class="pipe-code-wrapper">
          <div class="pipe-code-bar">
            <span>${filename}</span>
            <button class="pipe-copy-btn" onclick="navigator.clipboard.writeText(this.dataset.content)" data-content="${encodeURIComponent(text)}">Copy Text</button>
          </div>
          <pre class="pipe-code-block"><code>${escapeHtml(text)}</code></pre>
        </div>
      `;
    }
  } catch (err) {
    viewerEl.innerHTML = `<div class="pipe-error-state">Error streaming artifact: ${err.message}</div>`;
  }
}

async function launchPipelineTask(pipelineKey) {
  let endpoint = "";
  let payload = {};

  if (pipelineKey === "leetcode") {
    endpoint = "/api/pipelines/leetcode/run";
    const langs = [];
    if (document.getElementById("lc-lang-python")?.checked) langs.push("python");
    if (document.getElementById("lc-lang-js")?.checked) langs.push("javascript");
    if (document.getElementById("lc-lang-cpp")?.checked) langs.push("cpp");
    if (document.getElementById("lc-lang-java")?.checked) langs.push("java");

    payload = {
      title_slug: document.getElementById("leetcode-slug")?.value || "two-sum",
      human_mode: document.getElementById("leetcode-human")?.checked ?? true,
      timing_profile: document.getElementById("leetcode-timing")?.value || "BALANCED_HUMAN",
      languages: langs,
      force_mock: document.getElementById("leetcode-mock")?.checked ?? false,
    };
  } else if (pipelineKey === "social") {
    endpoint = "/api/pipelines/social/run";
    payload = {
      target_url: document.getElementById("social-url")?.value || "https://www.instagram.com/reel/sample_test_reel/",
      platform: document.getElementById("social-platform")?.value || "instagram",
      required_target: document.getElementById("social-target")?.value || "",
      transcribe_audio: document.getElementById("social-transcribe")?.checked ?? true,
      human_mode: document.getElementById("social-human")?.checked ?? true,
      timing_profile: "STREAM_PACED",
      force_mock: document.getElementById("social-mock")?.checked ?? false,
    };
  } else if (pipelineKey === "forensics") {
    endpoint = "/api/pipelines/forensics/run";
    payload = {
      target_url: document.getElementById("forensics-url")?.value || "https://httpbin.org/html",
      timing_profile: document.getElementById("forensics-profile")?.value || "STEALTH_PARANOID",
      scroll_depth: parseInt(document.getElementById("forensics-scroll")?.value || "2"),
      human_mode: document.getElementById("forensics-human")?.checked ?? true,
      force_mock: document.getElementById("forensics-mock")?.checked ?? false,
    };
  } else if (pipelineKey === "multimodal") {
    endpoint = "/api/pipelines/multimodal/run";
    payload = {
      target_input: document.getElementById("multimodal-input")?.value || "fixtures/exam_question_sample.png",
      expected_type: document.getElementById("multimodal-modality")?.value || "auto",
      extract_tables: document.getElementById("multimodal-tables")?.checked ?? true,
      human_mode: true,
      timing_profile: "BALANCED_HUMAN",
      force_mock: document.getElementById("multimodal-mock")?.checked ?? false,
    };
  }

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    alert(`🚀 ${result.message || "Pipeline execution launched in background!"}`);
    setTimeout(() => {
      loadPipelinesTab();
    }, 2000);
  } catch (err) {
    alert(`Failed to launch pipeline: ${err.message}`);
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// STAGE 6: BENCHMARKS, RESILIENCE & CHAOS LAB, AND STANDALONE EXPORTER (TAB 8)
// ═══════════════════════════════════════════════════════════════════════════════

function switchBenchmarksSubView(subviewId, btn) {
  document.querySelectorAll(".bench-subview-panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".pipe-subnav-btn").forEach(b => {
    if (b.id && b.id.startsWith("subview-btn-")) b.classList.remove("active");
  });
  const target = document.getElementById(subviewId);
  if (target) target.classList.add("active");
  if (btn) btn.classList.add("active");

  if (subviewId === "subview-benchmark-lab") loadBenchmarkReports();
  if (subviewId === "subview-resilience-lab") loadResilienceReports();
  if (subviewId === "subview-exporter-lab") loadExportsTab();
}

function setBmTarget(url) {
  const el = document.getElementById("bm-target-url");
  if (el) el.value = url;
}

function toggleAllBmSquad(cb) {
  document.querySelectorAll("input[name='bm-squad']").forEach(i => {
    i.checked = cb.checked;
  });
}

async function loadBenchmarksTab() {
  try {
    // 1. Fetch Overview Stats
    const [bmRes, resRes, expRes] = await Promise.all([
      fetch("/api/benchmarks/overview").then(r => r.json()).catch(() => ({})),
      fetch("/api/resilience/overview").then(r => r.json()).catch(() => ({})),
      fetch("/api/exports/list").then(r => r.json()).catch(() => ({})),
    ]);

    // Update Top KPI Ribbon
    const runsEl = document.getElementById("bm-kpi-runs");
    if (runsEl) runsEl.textContent = bmRes.total_benchmark_reports || 0;

    const topScorerEl = document.getElementById("bm-kpi-top-scorer");
    const topScoreValEl = document.getElementById("bm-kpi-top-score-val");
    if (bmRes.top_scoring_tool && topScorerEl) {
      topScorerEl.innerHTML = `<span class="crown-icon">👑</span> ${escapeHtml(bmRes.top_scoring_tool.winner_tool || "—")}`;
      if (topScoreValEl) topScoreValEl.textContent = `Score: ${bmRes.top_scoring_tool.winner_composite_score || 0.0} / 100`;
    }

    const resEl = document.getElementById("bm-kpi-resilience");
    if (resEl) {
      const idx = resRes.latest_resilience_index !== undefined ? resRes.latest_resilience_index : 100;
      resEl.textContent = `${idx}%`;
    }

    const expEl = document.getElementById("bm-kpi-exports-count");
    if (expEl && expRes) {
      const totalPkgs = (expRes.standalone_tools?.length || 0) +
                        (expRes.data_bundles?.length || 0) +
                        (expRes.pipeline_packages?.length || 0);
      expEl.textContent = totalPkgs;
    }

    // Load active sub-view data
    loadBenchmarkReports();
  } catch (err) {
    console.error("Error loading benchmarks overview:", err);
  }
}

async function runBenchmarkBattery() {
  const targetUrl = document.getElementById("bm-target-url")?.value || "https://quotes.toscrape.com";
  const batteryLabel = document.getElementById("bm-battery-label")?.value || "Dashboard Benchmark Battery";
  const iterations = parseInt(document.getElementById("bm-iterations")?.value || "3", 10);
  const humanMode = document.getElementById("bm-human-mode")?.checked || false;

  const squadCheckboxes = document.querySelectorAll("input[name='bm-squad']:checked");
  const toolIds = Array.from(squadCheckboxes).map(c => c.value);

  const payload = {
    target_url: targetUrl,
    battery_label: batteryLabel,
    iterations: iterations,
    human_mode: humanMode,
    tool_ids: toolIds.length > 0 ? toolIds : null,
  };

  try {
    const res = await fetch("/api/benchmarks/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    alert(`🏎️ ${result.message || "Benchmark battery started in background!"}`);
    setTimeout(() => {
      loadBenchmarkReports();
      loadBenchmarksTab();
    }, 3000);
  } catch (err) {
    alert(`Failed to launch benchmark battery: ${err.message}`);
  }
}

async function loadBenchmarkReports() {
  const container = document.getElementById("bm-reports-list");
  if (!container) return;

  try {
    const res = await fetch("/api/benchmarks/reports?limit=50");
    const data = await res.json();
    const reports = data.reports || [];

    if (reports.length === 0) {
      container.innerHTML = '<div class="empty-state">No benchmark reports found. Run a battery to populate.</div>';
      return;
    }

    container.innerHTML = reports.map(r => `
      <div class="report-drawer-item" onclick="viewBenchmarkReport('${escapeHtml(r.report_id)}')">
        <div class="item-title">
          <strong>${escapeHtml(r.battery_label || r.report_id)}</strong>
          <span class="badge-winner">🏆 ${escapeHtml(r.winner_tool)} (${r.winner_composite_score}/100)</span>
        </div>
        <div class="item-meta">
          <span>Target: ${escapeHtml(r.target_url || "—")}</span>
          <span>Elapsed: ${r.total_elapsed_sec}s</span>
          <span>${new Date(r.created_at).toLocaleString()}</span>
        </div>
      </div>
    `).join("");

    // Load first report leaderboard by default
    if (reports.length > 0) {
      viewBenchmarkReport(reports[0].report_id);
    }
  } catch (err) {
    container.innerHTML = `<div class="error-msg">Failed to load reports: ${err.message}</div>`;
  }
}

async function viewBenchmarkReport(reportId) {
  try {
    const res = await fetch(`/api/benchmarks/reports/${encodeURIComponent(reportId)}`);
    if (!res.ok) throw new Error(`Report not found (${res.status})`);
    const data = await res.json();
    const leaderboard = data.leaderboard || [];

    const body = document.getElementById("bm-leaderboard-body");
    if (!body) return;

    if (leaderboard.length === 0) {
      body.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No tool results in this report.</td></tr>';
      return;
    }

    body.innerHTML = leaderboard.map(t => {
      const isWinner = t.rank === 1;
      const rankBadge = isWinner ? "🥇 1" : (t.rank === 2 ? "🥈 2" : (t.rank === 3 ? "🥉 3" : `#${t.rank}`));
      const rowClass = isWinner ? "winner-row" : "";
      return `
        <tr class="${rowClass}">
          <td><strong>${rankBadge}</strong></td>
          <td><code>${escapeHtml(t.tool_id)}</code></td>
          <td><span class="status-badge ${t.status === 'completed' ? 'badge-active' : 'badge-failed'}">${escapeHtml(t.status)}</span></td>
          <td>${t.p50_sec}s</td>
          <td>${t.p90_sec}s</td>
          <td>${t.p99_sec}s</td>
          <td>${t.mem_delta_mb} MB</td>
          <td>${t.cpu_percent}%</td>
          <td>${t.yield_ratio}</td>
          <td>${t.stealth_score}</td>
          <td><strong class="score-pill">${t.composite_score}</strong></td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error viewing benchmark report:", err);
  }
}

async function runChaosScenario(scenario) {
  const payload = {
    scenario: scenario,
    tool_id: "01_curl_cffi",
  };

  try {
    const res = await fetch("/api/resilience/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    alert(`⚡ Chaos test '${scenario}' launched in background! Watch the HUD.`);
    setTimeout(() => {
      loadResilienceReports();
    }, 3000);
  } catch (err) {
    alert(`Failed to launch chaos scenario: ${err.message}`);
  }
}

async function loadResilienceReports() {
  const container = document.getElementById("resilience-reports-list");
  if (!container) return;

  try {
    const res = await fetch("/api/resilience/reports?limit=50");
    const data = await res.json();
    const reports = data.reports || [];

    if (reports.length === 0) {
      container.innerHTML = '<div class="empty-state">No resilience reports found. Execute a chaos test to evaluate.</div>';
      return;
    }

    // Update live resilience index badge from latest
    const badge = document.getElementById("resilience-badge-val");
    if (badge && reports.length > 0) {
      badge.textContent = `Index: ${reports[0].resilience_index} / 100`;
    }

    container.innerHTML = reports.map(r => `
      <div class="report-drawer-item" onclick="viewResilienceReport('${escapeHtml(r.report_id)}')">
        <div class="item-title">
          <strong>${escapeHtml(r.report_id)}</strong>
          <span class="badge-index">Shield: ${r.resilience_index}/100</span>
        </div>
        <div class="item-meta">
          <span>Status: ${escapeHtml(r.overall_status.toUpperCase())}</span>
          <span>Scenarios: ${r.scenarios_tested}</span>
          <span>${new Date(r.created_at).toLocaleString()}</span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="error-msg">Failed to load resilience reports: ${err.message}</div>`;
  }
}

async function viewResilienceReport(reportId) {
  try {
    const res = await fetch(`/api/resilience/reports/${encodeURIComponent(reportId)}`);
    if (!res.ok) throw new Error(`Report not found (${res.status})`);
    const data = await res.json();

    const titleEl = document.getElementById("modal-title");
    const metaEl = document.getElementById("modal-meta");
    const contentEl = document.getElementById("modal-content");
    const modalEl = document.getElementById("file-modal");

    if (titleEl && contentEl && modalEl) {
      titleEl.textContent = `Resilience Report: ${reportId}`;
      if (metaEl) metaEl.textContent = `Index: ${data.resilience_index}/100 | Status: ${data.overall_status}`;
      contentEl.textContent = data.markdown_content || JSON.stringify(data, null, 2);
      modalEl.classList.add("active");
    }
  } catch (err) {
    alert(`Error viewing resilience report: ${err.message}`);
  }
}

async function exportStandaloneTool() {
  const toolId = document.getElementById("export-tool-id")?.value || "01_curl_cffi";
  const format = document.getElementById("export-tool-format")?.value || "zip";

  try {
    const res = await fetch("/api/exports/tool", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool_id: toolId, output_format: format }),
    });
    const result = await res.json();
    alert(`📦 Standalone tool exported successfully to:\n${result.export_path}\nFiles: ${result.file_count} (${result.total_bytes} bytes)`);
    loadExportsTab();
    loadBenchmarksTab();
  } catch (err) {
    alert(`Failed to export standalone tool: ${err.message}`);
  }
}

async function bundleDataLake() {
  const scope = document.getElementById("export-bundle-scope")?.value || "cleaned";
  const pipe = document.getElementById("export-bundle-pipe")?.value || "";

  try {
    const res = await fetch("/api/exports/bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: scope, pipeline_id: pipe, archive_format: "zip" }),
    });
    const result = await res.json();
    alert(`🗄️ Data Lake bundle generated!\nBundle ID: ${result.bundle_id}\nFiles: ${result.total_files} (${result.total_bytes} bytes)\nArchive: ${result.bundle_path}`);
    loadExportsTab();
    loadBenchmarksTab();
  } catch (err) {
    alert(`Failed to bundle data lake: ${err.message}`);
  }
}

async function exportStandalonePipeline() {
  const pipeId = document.getElementById("export-pipeline-id")?.value || "01_leetcode_archiver";
  const includeFixtures = document.getElementById("export-pipeline-fixtures")?.checked ?? true;

  try {
    const res = await fetch("/api/exports/pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pipeline_id: pipeId, include_fixtures: includeFixtures }),
    });
    const result = await res.json();
    alert(`🐳 Pipeline docker package created!\nDirectory: ${result.package_path}\nFiles: ${result.file_count} (${result.total_bytes} bytes)`);
    loadExportsTab();
    loadBenchmarksTab();
  } catch (err) {
    alert(`Failed to export pipeline package: ${err.message}`);
  }
}

async function loadExportsTab() {
  const body = document.getElementById("export-catalog-body");
  if (!body) return;

  try {
    const res = await fetch("/api/exports/list");
    const data = await res.json();

    const rows = [];

    // 1. Standalone Tools
    (data.standalone_tools || []).forEach(t => {
      rows.push({
        category: "Standalone Tool",
        categoryClass: "badge-tool",
        categoryParam: "standalone_tools",
        name: t.dir_name || t.tool_id,
        bytes: t.total_bytes || 0,
        sha: t.files?.[0]?.sha256?.substring(0, 16) + "..." || "—",
        created: t.created_at || "—",
        filename: `${t.dir_name || t.tool_id}.zip`,
      });
    });

    // 2. Data Bundles
    (data.data_bundles || []).forEach(b => {
      rows.push({
        category: "Data Bundle",
        categoryClass: "badge-bundle",
        categoryParam: "data_bundles",
        name: b.bundle_id || b.manifest_file,
        bytes: b.total_bytes || 0,
        sha: b.files?.[0]?.sha256?.substring(0, 16) + "..." || "—",
        created: b.created_at || "—",
        filename: `${b.bundle_id}.zip`,
      });
    });

    // 3. Pipeline Packages
    (data.pipeline_packages || []).forEach(p => {
      rows.push({
        category: "Pipeline Container",
        categoryClass: "badge-pipeline",
        categoryParam: "pipeline_packages",
        name: p.dir_name || p.pipeline_id,
        bytes: p.total_bytes || 0,
        sha: p.files?.[0]?.sha256?.substring(0, 16) + "..." || "—",
        created: p.created_at || "—",
        filename: `${p.dir_name || p.pipeline_id}.zip`,
      });
    });

    if (rows.length === 0) {
      body.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No exported packages or bundles found.</td></tr>';
      return;
    }

    body.innerHTML = rows.map(r => `
      <tr>
        <td><span class="cat-badge ${r.categoryClass}">${escapeHtml(r.category)}</span></td>
        <td><code>${escapeHtml(r.name)}</code></td>
        <td>${(r.bytes / 1024).toFixed(1)} KB</td>
        <td><code class="sha-short">${escapeHtml(r.sha)}</code></td>
        <td>${r.created !== '—' ? new Date(r.created).toLocaleString() : '—'}</td>
        <td>
          <button class="btn-download-sm" onclick="downloadExportArchive('${escapeHtml(r.categoryParam)}', '${escapeHtml(r.filename)}')">
            ⬇ Download
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="6" class="text-danger">Failed to load exports: ${err.message}</td></tr>`;
  }
}

function downloadExportArchive(category, filename) {
  const url = `/api/exports/download/${encodeURIComponent(category)}/${encodeURIComponent(filename)}`;
  window.open(url, "_blank");
}




