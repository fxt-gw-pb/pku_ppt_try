// Keyless static frontend. It only talks to this project's public backend.

const API_BASE = (() => {
  if (location.protocol === "file:") return "http://127.0.0.1:8787";
  if (location.hostname.endsWith("github.io")) return "https://pku-ppt-try.onrender.com";
  return "";
})();

const FALLBACK_TEMPLATES = [
  {
    template_id: "pku-red",
    name: "北大红答辩模板",
    engine: "classic",
    description: "北大红学术答辩风格，适合论文答辩、开题报告和正式学术汇报。作者自制，最不推荐(bushi)。",
    label: "Academic",
    accent: "#b91c1c",
  },
  {
    template_id: "xhs-white-editorial",
    name: "小红书白底杂志风",
    engine: "editorial",
    description: "白底杂志风、强重点块、马卡龙软色卡，适合中文内容帖和知识分享。",
    label: "Editorial",
    accent: "#f97316",
  },
  {
    template_id: "graphify-dark-graph",
    name: "暗底知识图谱",
    engine: "graph",
    description: "深夜渐变、知识图谱和玻璃卡片，适合 AI、数据产品和图谱类分享。",
    label: "Graph",
    accent: "#22c55e",
  },
  {
    template_id: "knowledge-arch-blueprint",
    name: "奶油蓝图架构",
    engine: "blueprint",
    description: "奶油纸面、蓝图网格和硬边框，适合系统架构、工程白皮书和技术路线。",
    label: "Blueprint",
    accent: "#2563eb",
  },
  {
    template_id: "hermes-cyber-terminal",
    name: "暗终端 Cyber",
    engine: "terminal",
    description: "终端窗口、扫描线和代码感，适合 CLI、Agent、工具评测和技术复盘。",
    label: "Terminal",
    accent: "#14b8a6",
  },
  {
    template_id: "obsidian-claude-gradient",
    name: "GitHub 暗紫渐变",
    engine: "developer",
    description: "GitHub dark 加紫蓝渐变，适合开发者工作流、LLM 产品和工具教程。",
    label: "Developer",
    accent: "#7c3aed",
  },
  {
    template_id: "testing-safety-alert",
    name: "红琥珀警示",
    engine: "safety",
    description: "风险警示、事故复盘和安全审查风格，适合 AI 安全、风控和红队汇报。",
    label: "Safety",
    accent: "#dc2626",
  },
  {
    template_id: "xhs-pastel-card",
    name: "小红书柔和马卡龙",
    engine: "pastel",
    description: "柔和卡片、手作杂志感，适合生活方式、成长类和轻内容分享。",
    label: "Pastel",
    accent: "#ec4899",
  },
  {
    template_id: "dir-key-nav-minimal",
    name: "方向键 8 色极简",
    engine: "minimal",
    description: "大留白、一页一观点、强色块切换，适合 keynote 式演讲。",
    label: "Minimal",
    accent: "#0f766e",
  },
  {
    template_id: "pitch-deck",
    name: "Pitch Deck 路演",
    engine: "startup",
    description: "白底蓝紫渐变、指标和融资叙事，适合创业路演和投资人汇报。",
    label: "Startup",
    accent: "#4f46e5",
  },
  {
    template_id: "product-launch",
    name: "Product Launch 发布会",
    engine: "launch",
    description: "深色封面、功能卡片和 CTA，适合产品发布和方案展示。",
    label: "Launch",
    accent: "#ea580c",
  },
  {
    template_id: "tech-sharing",
    name: "Tech Sharing 技术分享",
    engine: "tech",
    description: "GitHub dark、代码块和终端感，适合内部技术分享和会议演讲。",
    label: "Tech",
    accent: "#0891b2",
  },
  {
    template_id: "weekly-report",
    name: "Weekly Report 周报",
    engine: "report",
    description: "清晰商务报表风，适合周报、项目进展和业务复盘。",
    label: "Report",
    accent: "#0284c7",
  },
  {
    template_id: "xhs-post",
    name: "小红书 3:4 图文",
    engine: "social",
    description: "3:4 竖版卡片，适合小红书/社媒图文轮播。",
    label: "Social",
    accent: "#e11d48",
  },
  {
    template_id: "course-module",
    name: "Course Module 教学模块",
    engine: "course",
    description: "课程侧栏和学习目标结构，适合课程、workshop 和培训材料。",
    label: "Course",
    accent: "#ca8a04",
  },
  {
    template_id: "presenter-mode-reveal",
    name: "演讲者模式 Reveal",
    engine: "speaker",
    description: "带逐字稿和演讲者视图的模板，适合技术分享、课程和正式演讲。",
    label: "Speaker",
    accent: "#4338ca",
  },
];

const $ = (id) => document.getElementById(id);

const templatesView = $("templates-view");
const generateView = $("generate-view");
const templateGallery = $("template-gallery");
const templateStrip = $("template-strip");
const templateSource = $("template-source");
const manuscriptEl = $("manuscript");
const countEl = $("count");
const limitEl = $("limit");
const generateBtn = $("generate");
const jobsEl = $("jobs");
const emptyEl = $("status-empty");
const activeChip = $("active-template-chip");
const heroTemplateLabel = $("hero-template-label");
const heroTemplateName = $("hero-template-name");
const heroTemplateNote = $("hero-template-note");
const previewTemplateLabel = $("preview-template-label");
const previewTitle = $("preview-title");
const openDonationBtns = document.querySelectorAll(".donation-trigger");
const closeDonationBtn = $("close-donation");
const donationModal = $("donation-modal");
let activeDonationTrigger = null;

let MAX_CHARS = 30000;
let templates = FALLBACK_TEMPLATES;
let selectedTemplateId = "pku-red";
const polling = new Map();

function normalizeTemplates(remoteTemplates) {
  const byId = new Map(FALLBACK_TEMPLATES.map((tpl) => [tpl.template_id, { ...tpl }]));
  (remoteTemplates || []).forEach((tpl) => {
    const fallback = byId.get(tpl.template_id) || {};
    byId.set(tpl.template_id, { ...fallback, ...tpl });
  });
  return [...byId.values()];
}

async function loadHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    if (!response.ok) throw new Error(`${response.status}`);
    const health = await response.json();
    MAX_CHARS = health.max_input_chars || MAX_CHARS;
    selectedTemplateId = health.default_template_id || selectedTemplateId;
    templates = normalizeTemplates(health.templates);
    templateSource.textContent = `已加载 ${templates.length} 个模板`;
  } catch (error) {
    templates = normalizeTemplates([]);
    templateSource.textContent = `离线模板列表：${templates.length} 个`;
  }

  limitEl.textContent = MAX_CHARS;
  renderTemplates();
  selectTemplate(readTemplateFromUrl() || selectedTemplateId, false);
  updateCount();
}

function readTemplateFromUrl() {
  const params = new URLSearchParams(location.search);
  return params.get("template");
}

function route() {
  const target = location.hash === "#generate" ? "generate" : "templates";
  templatesView.hidden = target !== "templates";
  generateView.hidden = target !== "generate";
  document.querySelectorAll("[data-nav]").forEach((link) => {
    link.classList.toggle("active", link.dataset.nav === target);
  });
}

function renderTemplates() {
  templateGallery.innerHTML = "";
  templateStrip.innerHTML = "";

  templates.forEach((tpl) => {
    templateGallery.appendChild(createTemplateCard(tpl));
    templateStrip.appendChild(createTemplatePill(tpl));
  });
}

function createTemplateCard(tpl) {
  const article = document.createElement("article");
  article.className = "template-card";
  article.dataset.templateId = tpl.template_id;
  article.style.setProperty("--accent", tpl.accent || "#2563eb");
  article.innerHTML = `
    <div class="template-card-top">
      <span class="template-mark">${escapeHtml(tpl.label || tpl.engine)}</span>
      <span class="template-engine">${escapeHtml(tpl.template_id)}</span>
    </div>
    <h3>${escapeHtml(tpl.name)}</h3>
    <p>${escapeHtml(tpl.description || "")}</p>
    <div class="template-actions">
      <button class="text-button" type="button" data-action="select">使用模板</button>
    </div>
  `;
  article.querySelector("[data-action='select']").addEventListener("click", () => {
    selectTemplate(tpl.template_id);
    location.hash = "generate";
  });
  return article;
}

function createTemplatePill(tpl) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "template-pill";
  button.dataset.templateId = tpl.template_id;
  button.style.setProperty("--accent", tpl.accent || "#2563eb");
  button.innerHTML = `
    <span>${escapeHtml(tpl.name)}</span>
    <small>${escapeHtml(tpl.label || tpl.engine)}</small>
  `;
  button.addEventListener("click", () => selectTemplate(tpl.template_id));
  return button;
}

function selectTemplate(templateId, updateUrl = true) {
  const exists = templates.some((tpl) => tpl.template_id === templateId);
  selectedTemplateId = exists ? templateId : "pku-red";
  const tpl = getSelectedTemplate();

  document.querySelectorAll("[data-template-id]").forEach((el) => {
    el.classList.toggle("selected", el.dataset.templateId === selectedTemplateId);
  });

  activeChip.textContent = tpl.name;
  heroTemplateLabel.textContent = tpl.label || tpl.engine;
  heroTemplateName.textContent = tpl.name;
  if (heroTemplateNote) heroTemplateNote.textContent = tpl.description || "";
  previewTemplateLabel.textContent = tpl.label || tpl.engine;
  updatePreviewTitle();

  if (updateUrl) {
    const url = new URL(location.href);
    url.searchParams.set("template", selectedTemplateId);
    history.replaceState(null, "", `${url.pathname}${url.search}${location.hash}`);
  }
}

function getSelectedTemplate() {
  return templates.find((tpl) => tpl.template_id === selectedTemplateId) || templates[0];
}

function updateCount() {
  const length = manuscriptEl.value.length;
  countEl.textContent = length;
  const overLimit = length > MAX_CHARS;
  countEl.parentElement.classList.toggle("over", overLimit);
  generateBtn.disabled = length === 0 || overLimit;
  updatePreviewTitle();
}

function updatePreviewTitle() {
  const firstLine = manuscriptEl.value.trim().split("\n").find(Boolean);
  previewTitle.textContent = firstLine ? firstLine.slice(0, 34) : "fxt ppt 生成预览";
}

async function createJob() {
  const manuscript = manuscriptEl.value.trim();
  if (!manuscript) return;

  generateBtn.disabled = true;
  generateBtn.textContent = "生成中...";

  try {
    const response = await fetch(`${API_BASE}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        manuscript,
        style: "academic",
        template_id: selectedTemplateId,
      }),
    });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(`HTTP ${response.status}: ${body}`);
    }
    const job = await response.json();
    addJobCard(job);
    startPolling(job.job_id);
  } catch (error) {
    addJobCard({
      job_id: "local-error",
      status: "failed",
      template_name: getSelectedTemplate().name,
      error: `提交失败：${error.message}`,
    });
  } finally {
    generateBtn.textContent = "生成 PPT";
    updateCount();
  }
}

function statusLabel(status) {
  return {
    pending: "等待中",
    running: "生成中",
    done: "已完成",
    failed: "失败",
  }[status] || status;
}

function addJobCard(job) {
  emptyEl.hidden = true;
  let item = document.getElementById(`job-${job.job_id}`);
  if (!item) {
    item = document.createElement("li");
    item.id = `job-${job.job_id}`;
    item.className = "job";
    jobsEl.prepend(item);
  }
  renderJobCard(item, job);
}

function renderJobCard(item, job) {
  item.className = `job ${job.status}`;
  const created = job.created_at ? new Date(job.created_at).toLocaleTimeString() : "";
  const slideInfo = job.slide_count ? ` · ${job.slide_count} slides` : "";
  const templateInfo = job.template_name ? ` · ${escapeHtml(job.template_name)}` : "";

  let actions = "";
  if (job.status === "done") {
    actions = `
      <div class="job-actions">
        <a href="${escapeAttr(resolveBackendHref(job.preview_url))}" target="_blank" rel="noopener">进入预览页</a>
        <a href="${escapeAttr(resolveBackendHref(job.download_url))}">下载网页包</a>
      </div>`;
  }

  const errorBlock = job.status === "failed" && job.error
    ? `<div class="job-error">${escapeHtml(job.error)}</div>`
    : "";

  item.innerHTML = `
    <div class="job-head">
      <span class="job-id">#${escapeHtml(job.job_id)}</span>
      <span class="job-status ${escapeHtml(job.status)}">${escapeHtml(statusLabel(job.status))}</span>
    </div>
    <div class="job-meta">${created}${slideInfo}${templateInfo}</div>
    ${actions}
    ${errorBlock}
  `;
}

function startPolling(jobId) {
  if (polling.has(jobId)) return;

  const tick = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
      if (!response.ok) throw new Error(`${response.status}`);
      const job = await response.json();
      const item = document.getElementById(`job-${jobId}`);
      if (item) renderJobCard(item, job);
      if (job.status === "done" || job.status === "failed") {
        clearInterval(polling.get(jobId));
        polling.delete(jobId);
      }
    } catch (error) {
      // Keep polling through short backend cold-start or network blips.
    }
  };

  polling.set(jobId, setInterval(tick, 1200));
  tick();
}

function resolveBackendHref(path) {
  if (!path) return "#";
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE}${path}`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function openDonationModal() {
  activeDonationTrigger = document.activeElement;
  donationModal.hidden = false;
  closeDonationBtn.focus();
}

function closeDonationModal() {
  donationModal.hidden = true;
  if (activeDonationTrigger) {
    activeDonationTrigger.focus();
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !donationModal.hidden) {
    closeDonationModal();
  }
});
manuscriptEl.addEventListener("input", updateCount);
generateBtn.addEventListener("click", createJob);
openDonationBtns.forEach((button) => {
  button.addEventListener("click", openDonationModal);
});
closeDonationBtn.addEventListener("click", closeDonationModal);
donationModal.addEventListener("click", (event) => {
  if (event.target === donationModal) {
    closeDonationModal();
  }
});

loadHealth();
route();
