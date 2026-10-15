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
  const tier   = document.getElementById("filter-tier").value;
  const level  = document.getElementById("filter-level").value;
  const tool   = document.getElementById("filter-tool").value;

  if (level && record.level !== level) return false;
  if (tool  && record.tool_id !== tool) return false;
  if (tier) {
    const src = record._source_file || "";
    if (!src.includes(tier)) return false;
  }
  return true;
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

  const rawFiles     = (run.raw_files     || []).map(f => `<div class="file-item">📄 ${f}</div>`).join("") || "<div class='empty-state'>No raw files</div>";
  const cleanedFiles = (run.cleaned_files || []).map(f => `<div class="file-item">✨ ${f}</div>`).join("") || "<div class='empty-state'>No cleaned files</div>";

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

    <div class="file-list-section">
      <div class="file-list-title">📦 Raw Files (${(run.raw_files||[]).length})</div>
      <div class="file-list">${rawFiles}</div>
    </div>

    <div class="file-list-section">
      <div class="file-list-title">✨ Cleaned Files (${(run.cleaned_files||[]).length})</div>
      <div class="file-list">${cleanedFiles}</div>
    </div>
  `;
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
