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
let currentIndexScope = "global";
let currentSubView = "subview-runs";
let indexSearchDebounce = null;
let indexOverviewData = null;

function onIndexScopeChange(scope) {
  currentIndexScope = scope;
  const pill = document.getElementById("index-scope-pill");
  const kpiScope = document.getElementById("kpi-scope");

  if (scope === "global") {
    if (pill) {
      pill.textContent = "GLOBAL MASTER";
      pill.className = "scope-pill";
    }
    if (kpiScope) kpiScope.textContent = "GLOBAL";
  } else {
    if (pill) {
      pill.textContent = `SEPARATE: ${scope}.sqlite`;
      pill.className = "scope-pill pill-separate";
    }
    if (kpiScope) kpiScope.textContent = scope;
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
  if (currentSubView === "subview-runs") {
    loadIndexRuns();
  } else if (currentSubView === "subview-files") {
    loadIndexFiles();
  } else if (currentSubView === "subview-logs") {
    loadIndexLogs();
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
    indexOverviewData = data;

    // Update KPI Ribbon
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

async function loadIndexRuns() {
  const tbody = document.getElementById("runs-table-body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="9" class="loading-td">Loading indexed runs...</td></tr>';

  const q = document.getElementById("index-search-input")?.value?.trim() || "";
  const batch = document.getElementById("index-filter-batch")?.value || "";
  const tool = document.getElementById("index-filter-tool")?.value || "";
  const action = document.getElementById("index-filter-action")?.value || "";
  const date = document.getElementById("index-filter-date")?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope, limit: "100" });
  if (q) params.append("q", q);
  if (batch) params.append("batch", batch);
  if (tool && currentIndexScope === "global") params.append("tool_id", tool);
  if (action) params.append("action_name", action);
  if (date) params.append("run_date", date);

  try {
    const res = await fetch(`${API_BASE}/api/index/runs?${params.toString()}`);
    const data = await res.json();
    const runs = data.runs || [];

    if (!runs.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="loading-td">No indexed runs found matching criteria.</td></tr>';
      return;
    }

    tbody.innerHTML = runs.map(r => {
      const toolId = r.tool_id || currentIndexScope;
      const metricsPills = formatDomainMetrics(r.domain_metrics || {});
      const statusCls = `manifest-status-${r.status || "completed"}`;
      const elapsed = r.elapsed_sec != null ? `${Number(r.elapsed_sec).toFixed(2)}s` : "—";
      const filesSummary = `<span class="tier-badge raw">R:${r.raw_file_count || 0}</span> <span class="tier-badge cleaned">C:${r.cleaned_file_count || 0}</span>`;

      return `
        <tr>
          <td><strong class="mono">${escHtml(toolId)}</strong></td>
          <td><span class="mono">${escHtml(r.action_name || "—")}</span></td>
          <td><span class="hash-pill" title="${escHtml(r.run_id)}">${escHtml(r.run_id)}</span></td>
          <td>${(r.run_date || "").slice(0, 10)}</td>
          <td>${elapsed}</td>
          <td><span class="${statusCls}">${(r.status || "COMPLETED").toUpperCase()}</span></td>
          <td>${filesSummary}</td>
          <td style="max-width: 320px;">${metricsPills}</td>
          <td>
            <button class="inspect-btn" onclick="jumpToRunDetail('${toolId}', '${r.action_name}', '${r.run_date}', '${r.run_id}')">
              Inspect ➔
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="loading-td">Error loading runs: ${escHtml(err.message)}</td></tr>`;
  }
}

async function loadIndexFiles() {
  const tbody = document.getElementById("files-table-body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" class="loading-td">Loading indexed files (SQLite FTS5)...</td></tr>';

  const q = document.getElementById("index-search-input")?.value?.trim() || "";
  const tool = document.getElementById("index-filter-tool")?.value || "";
  const action = document.getElementById("index-filter-action")?.value || "";
  const date = document.getElementById("index-filter-date")?.value || "";
  const tier = document.getElementById("index-filter-tier")?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope, limit: "100" });
  if (q) params.append("q", q);
  if (tool && currentIndexScope === "global") params.append("tool_id", tool);
  if (action) params.append("action_name", action);
  if (date) params.append("run_date", date);
  if (tier) params.append("tier", tier);

  try {
    const res = await fetch(`${API_BASE}/api/index/files?${params.toString()}`);
    const data = await res.json();
    const files = data.files || [];

    if (!files.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="loading-td">No indexed files found matching query.</td></tr>';
      return;
    }

    tbody.innerHTML = files.map(f => {
      const tierBadge = f.tier === "cleaned" 
        ? '<span class="tier-badge cleaned">CLEANED</span>' 
        : '<span class="tier-badge raw">RAW</span>';
      const sizeStr = formatBytes(f.size_bytes || 0);
      const shaShort = f.sha256_short || "—";
      const previewText = f.content_preview ? highlightSearch(f.content_preview, q) : '<span style="color:var(--text-muted)">(Binary or empty)</span>';
      const toolId = f.tool_id || currentIndexScope;

      return `
        <tr>
          <td>${tierBadge}</td>
          <td><strong class="mono">${escHtml(f.filename || "—")}</strong></td>
          <td><span class="mono">${escHtml(toolId)}</span></td>
          <td><span class="mono">${escHtml(f.action_name || "—")}</span></td>
          <td>${sizeStr}</td>
          <td><span class="hash-pill">${escHtml(shaShort)}</span></td>
          <td style="max-width: 380px; font-family: var(--font-mono); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escHtml(f.content_preview || '')}">
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
    tbody.innerHTML = `<tr><td colspan="8" class="loading-td">Error searching files: ${escHtml(err.message)}</td></tr>`;
  }
}

async function loadIndexLogs() {
  const tbody = document.getElementById("logs-table-body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="loading-td">Loading multi-tier logs...</td></tr>';

  const q = document.getElementById("index-search-input")?.value?.trim() || "";
  const tool = document.getElementById("index-filter-tool")?.value || "";
  const action = document.getElementById("index-filter-action")?.value || "";
  const date = document.getElementById("index-filter-date")?.value || "";
  const logtier = document.getElementById("index-filter-logtier")?.value || "";
  const stage = document.getElementById("index-filter-stage")?.value || "";

  const params = new URLSearchParams({ scope: currentIndexScope, limit: "150" });
  if (q) params.append("q", q);
  if (tool && currentIndexScope === "global") params.append("tool_id", tool);
  if (action) params.append("action_name", action);
  if (date) params.append("run_date", date);
  if (logtier) params.append("log_tier", logtier);
  if (stage) params.append("stage", stage);

  try {
    const res = await fetch(`${API_BASE}/api/index/logs?${params.toString()}`);
    const data = await res.json();
    const logs = data.logs || [];

    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="loading-td">No logs found matching query.</td></tr>';
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const ts = (l.timestamp || "").replace("T", " ").slice(0, 19);
      const tierClass = `logtier-badge ${l.log_tier || "tool_ops"}`;
      const levelClass = `log-level-${l.level || "INFO"}`;
      const stageStep = [l.stage, l.step].filter(Boolean).join(" / ") || "—";
      const toolId = l.tool_id || currentIndexScope || "—";
      const actionName = l.action_name || "—";
      const msgText = highlightSearch(l.message || "", q);

      return `
        <tr>
          <td style="white-space: nowrap; font-family: var(--font-mono); font-size: 11px;">${ts}</td>
          <td><span class="${tierClass}">${escHtml(l.log_tier || "ops")}</span></td>
          <td><span style="font-size: 11px; color: var(--text-secondary);">${escHtml(stageStep)}</span></td>
          <td><strong class="mono">${escHtml(toolId)}</strong></td>
          <td><span class="mono">${escHtml(actionName)}</span></td>
          <td><span class="${levelClass}">${escHtml(l.level || "INFO")}</span></td>
          <td style="font-family: var(--font-mono); font-size: 11px; word-break: break-all;">${msgText}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-td">Error loading logs: ${escHtml(err.message)}</td></tr>`;
  }
}

function handleIndexSearchKey(event) {
  if (event.key === "Enter") {
    executeIndexSearch();
    return;
  }
  clearTimeout(indexSearchDebounce);
  indexSearchDebounce = setTimeout(() => {
    executeIndexSearch();
  }, 350);
}

function executeIndexSearch() {
  loadActiveSubView();
}

function executeIndexFilter() {
  loadActiveSubView();
}

function resetIndexFilters() {
  const searchInput = document.getElementById("index-search-input");
  if (searchInput) searchInput.value = "";

  ["index-filter-stage", "index-filter-logtier", "index-filter-batch", 
   "index-filter-tool", "index-filter-action", "index-filter-date", 
   "index-filter-tier"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });

  loadActiveSubView();
}

async function triggerIndexRebuild(scopeType) {
  const targetScope = scopeType === "global" ? "global" : currentIndexScope;
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


