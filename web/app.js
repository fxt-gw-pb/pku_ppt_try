// Frontend demo for the PKU PPT generator backend.
// The frontend holds NO API keys. It only talks to its own backend.

const API_BASE = (() => {
  // When served by the FastAPI app itself, "" is fine. If a user opens the
  // file:// version of this page, fall back to localhost:8787.
  if (location.protocol === "file:") return "http://127.0.0.1:8787";
  return "";
})();

const $ = (id) => document.getElementById(id);
const manuscriptEl = $("manuscript");
const countEl = $("count");
const limitEl = $("limit");
const generateBtn = $("generate");
const jobsEl = $("jobs");
const emptyEl = $("status-empty");
const metaEl = $("meta");

let MAX_CHARS = 30000;
const polling = new Map(); // job_id → intervalId

async function loadHealth() {
  try {
    const r = await fetch(`${API_BASE}/api/health`);
    if (!r.ok) throw new Error(`${r.status}`);
    const h = await r.json();
    MAX_CHARS = h.max_input_chars || MAX_CHARS;
    limitEl.textContent = MAX_CHARS;
    metaEl.textContent = `provider: ${h.provider} · max: ${MAX_CHARS} 字`;
    updateCount();
  } catch (e) {
    metaEl.textContent = "backend offline — start with: uvicorn server.app:app --reload";
  }
}

function updateCount() {
  const n = manuscriptEl.value.length;
  countEl.textContent = n;
  const over = n > MAX_CHARS;
  countEl.parentElement.classList.toggle("over", over);
  generateBtn.disabled = n === 0 || over;
}

manuscriptEl.addEventListener("input", updateCount);

generateBtn.addEventListener("click", async () => {
  const manuscript = manuscriptEl.value.trim();
  if (!manuscript) return;
  generateBtn.disabled = true;
  try {
    const r = await fetch(`${API_BASE}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ manuscript, style: "academic" }),
    });
    if (!r.ok) {
      const body = await r.text();
      throw new Error(`HTTP ${r.status}: ${body}`);
    }
    const job = await r.json();
    addJobCard(job);
    startPolling(job.job_id);
  } catch (e) {
    alert(`提交失败: ${e.message}`);
  } finally {
    generateBtn.disabled = false;
  }
});

function statusLabel(s) {
  return {
    pending: "等待中",
    running: "生成中",
    done: "已完成",
    failed: "失败",
  }[s] || s;
}

function addJobCard(job) {
  emptyEl.style.display = "none";
  let li = document.getElementById(`job-${job.job_id}`);
  if (!li) {
    li = document.createElement("li");
    li.id = `job-${job.job_id}`;
    li.className = "job";
    jobsEl.prepend(li);
  }
  renderJobCard(li, job);
}

function renderJobCard(li, job) {
  li.classList.remove("pending", "running", "done", "failed");
  li.classList.add(job.status);
  const created = job.created_at ? new Date(job.created_at).toLocaleTimeString() : "";
  const slideInfo = job.slide_count ? ` · ${job.slide_count} slides` : "";

  let actions = "";
  if (job.status === "done") {
    actions = `
      <div class="job-actions">
        <a href="${API_BASE}${job.preview_url}" target="_blank" rel="noopener">在线预览</a>
        <a href="${API_BASE}${job.download_url}">下载 .zip</a>
      </div>`;
  }

  let errorBlock = "";
  if (job.status === "failed" && job.error) {
    errorBlock = `<div class="job-error">${escapeHtml(job.error)}</div>`;
  }

  li.innerHTML = `
    <div class="job-head">
      <span class="job-id">#${job.job_id}</span>
      <span class="job-status ${job.status}">${statusLabel(job.status)}</span>
    </div>
    <div class="job-meta">${created}${slideInfo}</div>
    ${actions}
    ${errorBlock}
  `;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function startPolling(job_id) {
  if (polling.has(job_id)) return;
  const tick = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/jobs/${job_id}`);
      if (!r.ok) throw new Error(`${r.status}`);
      const job = await r.json();
      const li = document.getElementById(`job-${job_id}`);
      if (li) renderJobCard(li, job);
      if (job.status === "done" || job.status === "failed") {
        clearInterval(polling.get(job_id));
        polling.delete(job_id);
      }
    } catch (e) {
      // Network blip — keep polling.
    }
  };
  const id = setInterval(tick, 1200);
  polling.set(job_id, id);
  tick();
}

loadHealth();
updateCount();
