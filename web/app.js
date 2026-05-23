// Frontend demo for the PKU PPT generator backend.
// The frontend holds NO API keys. It only talks to its own backend.

const API_BASE = (() => {
  // file:// preview → local dev backend.
  if (location.protocol === "file:") return "http://127.0.0.1:8787";
  // GitHub Pages frontend → Render-hosted backend.
  if (location.hostname.endsWith("github.io")) return "https://pku-ppt-try.onrender.com";
  // Served by the FastAPI app itself (local uvicorn) → same origin.
  return "";
})();

const $ = (id) => document.getElementById(id);
const manuscriptEl = $("manuscript");
const countEl = $("count");
const limitEl = $("limit");
const generateBtn = $("generate");
const jobsEl = $("jobs");
const emptyEl = $("status-empty");
const templatesEl = $("templates");

let MAX_CHARS = 30000;
let selectedTemplateId = "pku-red";
const polling = new Map(); // job_id → intervalId

async function loadHealth() {
  try {
    const r = await fetch(`${API_BASE}/api/health`);
    if (!r.ok) throw new Error(`${r.status}`);
    const h = await r.json();
    MAX_CHARS = h.max_input_chars || MAX_CHARS;
    selectedTemplateId = h.default_template_id || selectedTemplateId;
    limitEl.textContent = MAX_CHARS;
    renderTemplates(h.templates || []);
    updateCount();
  } catch (e) {
    // Backend unreachable — the Generate button will surface the error on click.
    renderTemplates([
      {
        template_id: "pku-red",
        name: "北大红答辩模板",
        engine: "pku-json",
        description: "北大红学术答辩风格。",
      },
      {
        template_id: "xhs-white-editorial",
        name: "小红书白底杂志风",
        engine: "html-ppt",
        description: "白底杂志风、强重点块、马卡龙软色卡。",
      },
    ]);
  }
}

function renderTemplates(templates) {
  if (!templatesEl) return;
  templatesEl.innerHTML = "";
  templates.forEach((tpl) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "template-card";
    btn.dataset.templateId = tpl.template_id;
    btn.classList.toggle("selected", tpl.template_id === selectedTemplateId);
    btn.innerHTML = `
      <span class="template-name">${escapeHtml(tpl.name)}</span>
      <span class="template-engine">${escapeHtml(tpl.engine)}</span>
      <span class="template-desc">${escapeHtml(tpl.description || "")}</span>
    `;
    btn.addEventListener("click", () => {
      selectedTemplateId = tpl.template_id;
      document.querySelectorAll(".template-card").forEach((el) => {
        el.classList.toggle("selected", el.dataset.templateId === selectedTemplateId);
      });
    });
    templatesEl.appendChild(btn);
  });
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
      body: JSON.stringify({
        manuscript,
        style: "academic",
        template_id: selectedTemplateId,
      }),
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
  const tplInfo = job.template_name ? ` · ${escapeHtml(job.template_name)}` : "";

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
    <div class="job-meta">${created}${slideInfo}${tplInfo}</div>
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
