/* ============================================================
   PKU Red Defense — Runtime
   Renders slides from slides.json into <deck-stage>
   ============================================================ */

(function () {
  "use strict";

  const NS = (window.PKU = window.PKU || {});

  // ---------- helpers ----------
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));
  const esc = (s) =>
    String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  // Allow a tiny markup vocab in body strings: <em>...</em>, **...**,
  // <br>, and <span class="accent">...</span> (the brand red highlight).
  const rich = (s) => {
    if (s == null) return "";
    let t = esc(s);
    // markdown-style emphasis
    t = t.replace(/\*\*([\s\S]+?)\*\*/g, "<em>$1</em>");
    // re-enable whitelisted inline HTML that survived escaping
    t = t.replace(
      /&lt;span class=&quot;accent&quot;&gt;([\s\S]*?)&lt;\/span&gt;/g,
      '<span class="accent">$1</span>'
    );
    t = t.replace(/&lt;em&gt;([\s\S]*?)&lt;\/em&gt;/g, "<em>$1</em>");
    t = t.replace(/&lt;br\s*\/?&gt;/g, "<br>");
    return t;
  };
  const cls = (...xs) => xs.filter(Boolean).join(" ");

  // ---------- image slot ----------
  function imageSlot(img, extraClass = "") {
    if (!img) return "";
    const fit = img.fit || "cover";
    const fitClass = "fit-" + fit;
    const fx = img.focalPoint?.x;
    const fy = img.focalPoint?.y;
    const style = [];
    if (fx != null) style.push(`--focal-x:${(fx * 100).toFixed(1)}%`);
    if (fy != null) style.push(`--focal-y:${(fy * 100).toFixed(1)}%`);
    const styleAttr = style.length ? ` style="${style.join(";")}"` : "";
    const framed = fit === "contain" || fit === "diagram" || fit === "logo" ? "image-slot--framed" : "";
    return `
      <div class="image-slot ${fitClass} ${framed} ${extraClass}"${styleAttr}>
        <img src="${esc(img.src)}" alt="${esc(img.alt || "")}">
        ${img.caption ? `<div class="caption">${esc(img.caption)}</div>` : ""}
      </div>
    `;
  }

  // ---------- shared chrome ----------
  function chrome(slide, ctx) {
    const idx = ctx.contentIndex;
    const total = ctx.totalContent;
    const chapters = ctx.deck.chapters || [];
    const chIdx = slide.chapterIndex;
    const navItems = chapters
      .map((c, i) => {
        const active = i === chIdx ? "is-active" : "";
        const label = typeof c === "string" ? c : c.title;
        return `<span class="nav-item ${active}">${esc(label)}</span>`;
      })
      .join("");

    const sectionTag = slide.sectionTitle
      ? `<div class="section-tag">${esc(slide.sectionTitle)}${
          slide.sectionTitleEn
            ? `<span class="en">${esc(slide.sectionTitleEn)}</span>`
            : ""
        }</div>`
      : "";

    const pageNum = total
      ? `<div class="page-num"><span class="current">${String(idx).padStart(2, "0")}</span> / ${String(total).padStart(2, "0")}</div>`
      : "";

    const footerTag = slide.footerTag
      ? `<div class="footer-tag">${esc(slide.footerTag)}</div>`
      : "";

    return `
      ${sectionTag}
      ${chapters.length ? `<div class="chapter-nav">${navItems}</div>` : ""}
      <div class="top-rule"></div>
      ${slide.headline ? `<div class="headline">${rich(slide.headline)}</div>` : ""}
      ${slide.subheadline ? `<div class="headline-sub">${esc(slide.subheadline)}</div>` : ""}
      ${pageNum}
      ${footerTag}
    `;
  }

  // ---------- layouts ----------
  const layouts = {};

  layouts.cover = (s, ctx) => {
    const m = ctx.deck.meta || {};
    const deco = Array.from({ length: 18 })
      .map((_, i) => {
        // sparse pattern, top-right
        const fill = [0, 1, 3, 6, 9, 12].includes(i) ? "fill" : "";
        return `<div class="c ${fill}"></div>`;
      })
      .join("");
    return `
      <div class="cover-watermark"></div>
      <div class="cover-deco">${deco}</div>
      <div class="cover-brand">
        ${m.logo ? `<img src="${esc(m.logo)}" alt="logo">` : ""}
      </div>
      <div class="cover-body">
        <div class="cover-title">${rich(s.title || m.title || "")}</div>
        ${s.subtitle || m.subtitle ? `<div class="cover-subtitle">${esc(s.subtitle || m.subtitle)}</div>` : ""}
      </div>
      <div class="cover-footer">
        <div>
          ${m.date ? `<div class="date">${esc(m.date)}</div>` : ""}
          <div class="cover-arrow">→</div>
        </div>
        <div class="motto">${esc(m.motto || "")}</div>
      </div>
    `;
  };

  layouts.contents = (s, ctx) => {
    const chapters = s.chapters || ctx.deck.chapters || [];
    const items = chapters
      .map(
        (c, i) => `
        <div class="contents-item">
          <div class="num">${String(i + 1).padStart(2, "0")}</div>
          <div class="text">
            <div class="cn">${esc(typeof c === "string" ? c : c.title)}</div>
            <div class="en">${esc((typeof c === "object" && c.subtitle) || s.chapterEn?.[i] || "")}</div>
          </div>
        </div>`
      )
      .join("");
    return `
      <div class="contents-head">
        <div class="kicker">CONTENTS</div>
        <div class="title-cn">目录</div>
        <div class="title-en">CONTENTS</div>
        <div class="rule"></div>
        <div class="meta">${esc(s.note || "依次包含背景与意义、综述与评述、思路与内容、过程与方法、成果与展望。")}</div>
      </div>
      <div class="contents-list">${items}</div>
    `;
  };

  layouts["section-divider"] = (s, ctx) => {
    const ch = (ctx.deck.chapters || [])[s.chapterIndex];
    const num = String((s.chapterIndex ?? 0) + 1).padStart(2, "0");
    const title = s.title || (typeof ch === "string" ? ch : ch?.title) || "";
    const en = s.titleEn || (typeof ch === "object" && ch?.subtitle) || "";
    const points = (s.points || []).slice(0, 3);
    return `
      <div class="sd-wrap">
        <div class="sd-num">${num}</div>
        <div class="sd-kicker">PART ${num}</div>
        <div class="sd-bar"></div>
        <div class="sd-title">${rich(title)}</div>
        ${en ? `<div class="sd-en">${esc(en)}</div>` : ""}
        ${
          points.length
            ? `<div class="sd-points">${points
                .map(
                  (p, i) =>
                    `<div class="pt"><span class="ord">0${i + 1}</span><span>${esc(p)}</span></div>`
                )
                .join("")}</div>`
            : ""
        }
      </div>
    `;
  };

  layouts["image-analysis"] = (s, ctx) => `
    ${chrome(s, ctx)}
    <div class="content">
      ${imageSlot(s.images?.[0], "ia-img")}
      <div class="ia-list">
        ${(s.items || [])
          .map(
            (it, i) => `
          <div class="ia-item">
            <div class="ia-num">${String(i + 1).padStart(2, "0")}</div>
            <div class="ia-text">
              <div class="title">${esc(it.title || "")}</div>
              <div class="body">${rich(it.body || "")}</div>
            </div>
          </div>`
          )
          .join("")}
      </div>
    </div>
  `;

  layouts["chart-analysis"] = (s, ctx) => `
    ${chrome(s, ctx)}
    <div class="content">
      ${imageSlot(s.images?.[0] || s.chartImage, "ca-chart")}
      <div class="ca-insights">
        ${(s.insights || [])
          .map(
            (it) => `
          <div class="ca-insight">
            <div class="ca-h">${esc(it.title || "")}</div>
            <div class="ca-b">${rich(it.body || "")}</div>
          </div>`
          )
          .join("")}
      </div>
    </div>
  `;

  layouts.timeline = (s, ctx) => {
    const steps = s.steps || [];
    const cols = Math.max(2, Math.min(steps.length, 6));
    return `
      ${chrome(s, ctx)}
      <div class="content">
        <div class="tl" style="--cols:${cols}">
          ${steps
            .map(
              (st) => `
            <div class="tl-step">
              <div class="yr">${esc(st.label || "")}</div>
              <div class="dot"></div>
              <div class="title">${esc(st.title || "")}</div>
              <div class="body">${rich(st.body || "")}</div>
            </div>`
            )
            .join("")}
        </div>
      </div>
    `;
  };

  layouts["theory-cards"] = (s, ctx) => {
    const cards = s.cards || [];
    const cols = Math.max(2, Math.min(cards.length, 4));
    return `
      ${chrome(s, ctx)}
      <div class="content" style="--cols:${cols}">
        ${cards
          .map(
            (c, i) => `
          <div class="theory-card">
            <div class="tc-head">
              <div class="ord">理论 0${i + 1} · THEORY</div>
              <div class="tc-title">${esc(c.title || "")}</div>
            </div>
            <div class="tc-body">
              ${c.label ? `<span class="lbl">${esc(c.label)}</span>` : ""}
              ${rich(c.body || "")}
            </div>
          </div>`
          )
          .join("")}
      </div>
    `;
  };

  layouts["multi-card"] = (s, ctx) => {
    const cards = s.cards || [];
    const cols = s.cols || Math.max(2, Math.min(cards.length, 4));
    return `
      ${chrome(s, ctx)}
      <div class="content" style="--cols:${cols}">
        ${cards
          .map(
            (c, i) => `
          <div class="multi-card">
            <div class="mc-top">
              <div class="mc-num">${String(i + 1).padStart(2, "0")}</div>
              <div class="mc-title">${esc(c.title || "")}</div>
            </div>
            <div class="mc-body">${rich(c.body || "")}</div>
            ${c.tag ? `<div class="mc-foot">${esc(c.tag)}</div>` : ""}
          </div>`
          )
          .join("")}
      </div>
    `;
  };

  layouts.framework = (s, ctx) => {
    const nodes = s.nodes || [];
    const cols = nodes.length;
    return `
      ${chrome(s, ctx)}
      <div class="content">
        <div class="fw" style="--cols:${cols}">
          ${nodes
            .map(
              (n, i) => `
            <div class="fw-node ${n.primary ? "primary" : ""}">
              <div class="ord">STEP 0${i + 1}</div>
              <div class="title">${esc(n.title || "")}</div>
              <div class="body">${rich(n.body || "")}</div>
              ${
                n.tags && n.tags.length
                  ? `<div class="tags">${n.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>`
                  : ""
              }
            </div>`
            )
            .join("")}
        </div>
      </div>
    `;
  };

  layouts.vs = (s, ctx) => `
    ${chrome(s, ctx)}
    <div class="content">
      <div class="vs-col left">
        <div class="vs-kicker">${esc(s.leftKicker || "PROS · 优势")}</div>
        <div class="vs-title">${esc(s.leftTitle || "")}</div>
        <div class="vs-items">
          ${(s.leftItems || [])
            .map(
              (it) =>
                `<div class="vs-item"><div class="bullet"></div><div>${
                  it.title ? `<span class="lbl">${esc(it.title)}</span>` : ""
                }${rich(it.body || it)}</div></div>`
            )
            .join("")}
        </div>
      </div>
      <div class="vs-mid"><div class="vs-circle">VS</div></div>
      <div class="vs-col right">
        <div class="vs-kicker">${esc(s.rightKicker || "CONS · 劣势")}</div>
        <div class="vs-title">${esc(s.rightTitle || "")}</div>
        <div class="vs-items">
          ${(s.rightItems || [])
            .map(
              (it) =>
                `<div class="vs-item"><div class="bullet"></div><div>${
                  it.title ? `<span class="lbl">${esc(it.title)}</span>` : ""
                }${rich(it.body || it)}</div></div>`
            )
            .join("")}
        </div>
      </div>
    </div>
  `;

  layouts.swot = (s, ctx) => {
    const quad = (slot, key, label, ltr, title, items) => `
      <div class="sw-quad sw-q-${slot}">
        <div class="ltr">${ltr}</div>
        <div class="lbl">${esc(label)}</div>
        <div class="title">${esc(title)}</div>
        <ul>${(items || []).map((it) => `<li>${rich(it)}</li>`).join("")}</ul>
      </div>
    `;
    return `
      ${chrome(s, ctx)}
      <div class="content">
        ${quad("s", "s", "Strengths · 优势", "S", s.strengthsTitle || "内部优势", s.strengths)}
        <div class="sw-center">
          <div class="sw-disc">
            <div class="cn">SWOT<br>分析</div>
            <div class="en">Analysis</div>
          </div>
        </div>
        ${quad("w", "w", "Weaknesses · 劣势", "W", s.weaknessesTitle || "内部劣势", s.weaknesses)}
        ${quad("o", "o", "Opportunities · 机会", "O", s.opportunitiesTitle || "外部机会", s.opportunities)}
        ${quad("t", "t", "Threats · 威胁", "T", s.threatsTitle || "外部威胁", s.threats)}
      </div>
    `;
  };

  layouts.method = (s, ctx) => {
    const methods = s.methods || [];
    const cols = s.cols || Math.max(2, Math.min(methods.length, 4));
    return `
      ${chrome(s, ctx)}
      <div class="content" style="--cols:${cols}">
        ${methods
          .map(
            (m, i) => `
          <div class="method-card">
            <div class="mtag">METHOD 0${i + 1}</div>
            <div class="mtitle">${esc(m.title || "")}</div>
            ${m.en ? `<div class="men">${esc(m.en)}</div>` : ""}
            <div class="mbody">${rich(m.body || "")}</div>
          </div>`
          )
          .join("")}
      </div>
    `;
  };

  layouts["section-text"] = (s, ctx) => `
    ${chrome(s, ctx)}
    <div class="content">
      <div class="st-side">
        <div class="quote">${esc(s.sideMark || "”")}</div>
        <div class="meta">${esc(s.sideMeta || s.sectionTitle || "")}</div>
      </div>
      <div class="st-body">
        ${(s.blocks || [])
          .map(
            (b) => `
          <div class="st-block">
            ${b.label ? `<div class="lbl">${esc(b.label)}</div>` : ""}
            <div class="txt">${rich(b.text || "")}</div>
          </div>`
          )
          .join("")}
      </div>
    </div>
  `;

  layouts.closing = (s, ctx) => {
    const m = ctx.deck.meta || {};
    return `
      <div class="cover-watermark"></div>
      <div class="cl-brand">${m.logo ? `<img src="${esc(m.logo)}" alt="logo">` : ""}</div>
      <div class="cl-body">
        <div class="cl-title">${esc(s.title || "感谢您的倾听！")}</div>
        <div class="cl-sub">${esc(s.subtitle || "THANK YOU FOR LISTENING")}</div>
        <div class="cl-rule"></div>
        <div class="cl-msg">${esc(s.message || "敬请各位老师批评指正。")}</div>
      </div>
      <div class="cl-foot">
        <div>${esc(m.presenter || "")}　/　${esc(m.advisor || "")}</div>
        <div>${esc(m.date || "")}</div>
      </div>
    `;
  };

  // ---------- render ----------
  function classesFor(slide) {
    return cls("slide", "layout-" + slide.layout, slide.className);
  }

  function renderSlide(slide, ctx) {
    const fn = layouts[slide.layout];
    const inner = fn ? fn(slide, ctx) : `<div style="padding:80px">Unknown layout: ${esc(slide.layout)}</div>`;
    return { className: classesFor(slide), html: inner };
  }

  function renderDeck(deck, root) {
    const slides = deck.slides || [];
    // Pre-compute content page numbering: skip cover / contents / section-divider / closing
    const nonChromeLayouts = new Set(["cover", "contents", "section-divider", "closing"]);
    let totalContent = 0;
    slides.forEach((s) => {
      if (!nonChromeLayouts.has(s.layout)) totalContent++;
    });

    let runningContent = 0;
    root.innerHTML = "";
    slides.forEach((s, i) => {
      let contentIndex = 0;
      if (!nonChromeLayouts.has(s.layout)) {
        runningContent++;
        contentIndex = runningContent;
      }
      const ctx = { deck, contentIndex, totalContent, index: i };
      const out = renderSlide(s, ctx);
      const sec = document.createElement("section");
      sec.className = out.className;
      sec.setAttribute("data-screen-label", s.label || `${String(i + 1).padStart(2, "0")} ${s.layout}`);
      sec.innerHTML = out.html;
      root.appendChild(sec);
    });
  }

  async function loadDeck(src) {
    if (typeof src === "string") {
      const res = await fetch(src);
      if (!res.ok) throw new Error("Failed to load " + src);
      return res.json();
    }
    return src;
  }

  async function init() {
    const stage = document.querySelector("deck-stage");
    if (!stage) {
      console.error("[PKU] no <deck-stage> element found");
      return;
    }
    let deck;
    if (window.__PKU_DECK_INLINE) {
      deck = window.__PKU_DECK_INLINE;
    } else {
      const src = stage.getAttribute("data-deck") || "data/slides.json";
      try {
        deck = await loadDeck(src);
      } catch (err) {
        console.error("[PKU]", err);
        stage.innerHTML = `<section class="slide" style="padding:60px"><h1 style="color:#9A0000">无法加载 ${src}</h1><p>${err.message}</p><p style="margin-top:20px;color:#555">如果您是直接在本地文件系统打开 index.html，浏览器会阻止 <code>fetch</code> 读取 JSON。请改用本地服务器（例如 <code>python -m http.server</code>）或在 HTML 中以 <code>window.__PKU_DECK_INLINE</code> 内联数据。</p></section>`;
        return;
      }
    }
    NS.deck = deck;
    renderDeck(deck, stage);
    injectPdfButton();
    injectEditPanel();
    injectNavArrows();
    /* Replay persisted field-edits against the freshly-rendered slides.
     * deck-stage rebuilds slides from JSON each load, so DOM edits don't
     * survive a reload without this. */
    replaySavedEdits();
  }

  function injectPdfButton() {
    if (document.querySelector(".pdf-export-btn")) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pdf-export-btn";
    btn.title = "导出 PDF（在打印对话框中选择「另存为 PDF」）";
    btn.innerHTML = '<span>⇩</span><span>导出 PDF</span>';
    btn.style.cssText = [
      "position:fixed", "right:24px", "bottom:24px", "z-index:2147483600",
      "display:inline-flex", "align-items:center", "gap:8px",
      "padding:10px 16px", "border-radius:999px",
      "background:#9A0000", "color:#fff", "border:1px solid rgba(255,255,255,.18)",
      'font:600 13px/1 "Source Han Sans SC","Noto Sans SC","PingFang SC",-apple-system,sans-serif',
      "letter-spacing:.04em", "cursor:pointer",
      "box-shadow:0 8px 24px rgba(154,0,0,.35)",
      "transition:transform .18s ease, background .18s ease",
    ].join(";");
    btn.addEventListener("mouseenter", () => {
      btn.style.background = "#b50000";
      btn.style.transform = "translateY(-1px)";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.background = "#9A0000";
      btn.style.transform = "translateY(0)";
    });
    btn.addEventListener("click", () => {
      setTimeout(() => window.print(), 60);
    });
    document.body.appendChild(btn);
    /* hide button in print */
    const tag = document.createElement("style");
    tag.textContent = "@media print{.pdf-export-btn{display:none!important}}";
    document.head.appendChild(tag);
    /* P-key shortcut */
    document.addEventListener("keydown", (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "p" || e.key === "P") {
        e.preventDefault();
        setTimeout(() => window.print(), 60);
      }
    });
  }

  /* ---------- field-edit panel ----------
   * Same UX as the html-ppt runtime: a 360px sidebar with two textareas
   * (verbatim find / replace) that mutates text nodes of the currently
   * visible slide. Slides are light-DOM children of <deck-stage> projected
   * through a <slot>, so a normal TreeWalker works. Edits are persisted to
   * localStorage and re-applied on reload; re-export rewrites both
   * index.html and data/slides.json so the edits survive a fresh open. */
  const EDITS_KEY = "fxt-ppt-deck-edits:" + location.pathname;
  function loadStoredEdits() {
    try {
      const raw = localStorage.getItem(EDITS_KEY);
      if (!raw) return [];
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }
  function saveStoredEdits(arr) {
    try { localStorage.setItem(EDITS_KEY, JSON.stringify(arr)); } catch (e) {}
  }
  function appendStoredEdit(find, replace, slideIndex) {
    const arr = loadStoredEdits();
    const entry = { find: find, replace: replace, ts: Date.now() };
    if (typeof slideIndex === "number") entry.slideIndex = slideIndex;
    arr.push(entry);
    saveStoredEdits(arr);
  }
  function popStoredEdit() {
    const arr = loadStoredEdits();
    const last = arr.pop();
    saveStoredEdits(arr);
    return last;
  }
  function clearStoredEdits() {
    try { localStorage.removeItem(EDITS_KEY); } catch (e) {}
  }
  function deckSections() {
    const stage = document.querySelector("deck-stage");
    if (!stage) return [];
    return Array.from(stage.querySelectorAll(":scope > section"));
  }
  function activeSlideEl() {
    const stage = document.querySelector("deck-stage");
    if (!stage) return null;
    return (
      stage.querySelector('[data-deck-active]') ||
      stage.querySelector('section.is-active') ||
      stage.querySelector('section')
    );
  }
  function activeSlideIndex() {
    const sections = deckSections();
    if (!sections.length) return -1;
    const active = activeSlideEl();
    const i = active ? sections.indexOf(active) : -1;
    return i >= 0 ? i : 0;
  }
  function replaceInTextNodes(root, needle, replacement) {
    const result = { count: 0, snapshots: [] };
    if (!root || !needle) return result;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const hits = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && node.nodeValue.indexOf(needle) !== -1) hits.push(node);
    }
    hits.forEach((n) => {
      const before = n.nodeValue;
      const after = before.split(needle).join(replacement);
      if (after !== before) {
        result.snapshots.push({ node: n, before: before });
        n.nodeValue = after;
        result.count += before.split(needle).length - 1;
      }
    });
    return result;
  }
  function replaySavedEdits() {
    const saved = loadStoredEdits();
    if (!saved.length) return;
    const stage = document.querySelector("deck-stage");
    if (!stage) return;
    const sections = deckSections();
    saved.forEach((op) => {
      if (!op || op.find == null || op.replace == null) return;
      const target =
        typeof op.slideIndex === "number" && sections[op.slideIndex]
          ? sections[op.slideIndex]
          : stage; /* legacy ops without slideIndex fall back to whole deck */
      replaceInTextNodes(target, op.find, op.replace);
    });
  }
  /* Recursively map every string under `value` with one find/replace op. */
  function mapStrings(value, needle, repl) {
    if (typeof value === "string") return value.split(needle).join(repl);
    if (Array.isArray(value)) return value.map((v) => mapStrings(v, needle, repl));
    if (value && typeof value === "object") {
      const out = {};
      for (const k of Object.keys(value)) out[k] = mapStrings(value[k], needle, repl);
      return out;
    }
    return value;
  }
  /* Rewrite a parsed slides.json with all persisted edit ops. Per-op:
   * if slideIndex present, apply only inside that slide's object; else
   * apply across the whole deck (legacy ops). */
  function applyEditsToDeckJson(deckObj, ops) {
    if (!deckObj || !ops || !ops.length) return deckObj;
    const slides = Array.isArray(deckObj.slides) ? deckObj.slides : null;
    let out = deckObj;
    ops.forEach((op) => {
      if (!op || op.find == null || op.replace == null || op.find === "") return;
      if (typeof op.slideIndex === "number" && slides && slides[op.slideIndex] != null) {
        slides[op.slideIndex] = mapStrings(slides[op.slideIndex], op.find, op.replace);
      } else {
        out = mapStrings(out, op.find, op.replace);
      }
    });
    return out;
  }
  function deriveDeckZipUrl() {
    if (location.protocol === "file:") return null;
    const m = /^(.*)\/index\.html$/i.exec(location.pathname);
    const base = m ? m[1] : location.pathname.replace(/\/$/, "");
    if (!/\/decks\/[^/]+$/.test(base)) return null;
    return location.origin + base + ".zip";
  }
  function loadJSZip() {
    if (window.JSZip) return Promise.resolve(window.JSZip);
    function inject(src) {
      return new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = src;
        s.onload = () => window.JSZip ? resolve(window.JSZip) : reject(new Error("JSZip 未加载成功"));
        s.onerror = () => reject(new Error("JSZip 加载失败：" + src));
        document.head.appendChild(s);
      });
    }
    /* Vendor-first; CDN only as fallback. */
    return inject("assets/jszip.min.js").catch(() =>
      inject("https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js")
    );
  }
  function serializeDeckForExport() {
    const clone = document.documentElement.cloneNode(true);
    const dropSelectors = [
      ".edit-panel", ".edit-panel-toggle-btn",
      ".pdf-export-btn",
      ".nav-arrows"
    ];
    dropSelectors.forEach((sel) => {
      clone.querySelectorAll(sel).forEach((el) => el.remove());
    });
    return "<!doctype html>\n<html" + (clone.getAttribute("lang") ? ' lang="' + clone.getAttribute("lang") + '"' : "") + ">\n" + clone.innerHTML + "\n</html>";
  }
  async function downloadEditedZip() {
    const zipUrl = deriveDeckZipUrl();
    if (!zipUrl) {
      throw new Error("当前页不是可下载的生成结果（仅生成结果页支持二次导出）");
    }
    const ops = loadStoredEdits();
    const JSZip = await loadJSZip();
    const resp = await fetch(zipUrl);
    if (!resp.ok) throw new Error("原网页包获取失败（HTTP " + resp.status + "）");
    const buf = await resp.arrayBuffer();
    const zip = await JSZip.loadAsync(buf);
    const indexPath = Object.keys(zip.files).find((p) =>
      /(^|\/)index\.html$/i.test(p) && !zip.files[p].dir
    );
    if (!indexPath) throw new Error("原网页包内未找到 index.html");
    zip.file(indexPath, serializeDeckForExport());
    /* PKU decks re-render from data/slides.json on every load, so the
     * edits must be baked into the JSON or they'd be wiped on reopen. */
    const slidesPath = Object.keys(zip.files).find((p) =>
      /(^|\/)data\/slides\.json$/i.test(p) && !zip.files[p].dir
    );
    if (slidesPath && ops.length) {
      const raw = await zip.files[slidesPath].async("string");
      try {
        const parsed = JSON.parse(raw);
        const rewritten = applyEditsToDeckJson(parsed, ops);
        zip.file(slidesPath, JSON.stringify(rewritten, null, 2));
      } catch (e) {
        console.warn("[PKU] failed to rewrite slides.json:", e);
      }
    }
    const blob = await zip.generateAsync({ type: "blob" });
    const a = document.createElement("a");
    const baseName = zipUrl.split("/").pop().replace(/\.zip$/i, "");
    a.href = URL.createObjectURL(blob);
    a.download = baseName + "-edited.zip";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1500);
  }
  function injectEditPanel() {
    if (document.querySelector(".edit-panel-toggle-btn")) return;

    /* Inject CSS for both the toggle button and the panel */
    const css = document.createElement("style");
    css.textContent = [
      '.edit-panel{position:fixed;top:0;right:0;width:360px;height:100vh;z-index:2147483601;',
      ' background:#0f1115;color:#e6edf3;border-left:1px solid rgba(255,255,255,.08);',
      ' display:none;flex-direction:column;padding:20px 18px;gap:12px;overflow-y:auto;',
      ' font:14px/1.55 "Source Han Sans SC","Noto Sans SC",-apple-system,BlinkMacSystemFont,sans-serif;',
      ' box-shadow:-12px 0 32px rgba(0,0,0,.35);box-sizing:border-box}',
      'body.has-edit-panel .edit-panel{display:flex}',
      '.edit-panel *{box-sizing:border-box}',
      '.edit-panel-head{display:flex;align-items:center;justify-content:space-between;gap:8px}',
      '.edit-panel-head h3{margin:0;font-size:15px;font-weight:700;letter-spacing:.04em}',
      '.edit-panel-close{background:transparent;border:1px solid rgba(255,255,255,.18);color:#e6edf3;',
      ' width:28px;height:28px;border-radius:8px;font-size:16px;cursor:pointer;line-height:1;padding:0}',
      '.edit-panel-close:hover{background:rgba(255,255,255,.08)}',
      '.edit-panel .hint{font-size:12px;color:#8b949e;line-height:1.6;margin:0}',
      '.edit-panel .warn{font-size:12px;color:#f5a524;line-height:1.6;margin:0}',
      '.edit-panel label{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#8b949e;font-weight:700}',
      '.edit-panel textarea{width:100%;min-height:96px;resize:vertical;background:#161922;color:#e6edf3;',
      ' border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:10px 12px;',
      ' font:13px/1.55 ui-monospace,"JetBrains Mono",SFMono-Regular,Menlo,monospace}',
      '.edit-panel textarea:focus{outline:none;border-color:#9A0000;box-shadow:0 0 0 2px rgba(154,0,0,.25)}',
      '.edit-panel .apply-row{display:flex;flex-direction:column;gap:8px}',
      '.edit-panel .apply-btn,.edit-panel .undo-btn,.edit-panel .export-btn,.edit-panel .clear-btn{',
      ' appearance:none;border-radius:8px;padding:10px 14px;',
      ' font:600 13px/1 -apple-system,sans-serif;cursor:pointer;letter-spacing:.04em}',
      '.edit-panel .apply-btn{background:#9A0000;color:#fff;border:none}',
      '.edit-panel .apply-btn:hover{background:#b50000}',
      '.edit-panel .undo-btn{background:transparent;color:#e6edf3;border:1px solid rgba(255,255,255,.22)}',
      '.edit-panel .undo-btn:hover:not(:disabled){background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.4)}',
      '.edit-panel .export-btn{background:#1aaf6c;color:#fff;border:none;margin-top:4px}',
      '.edit-panel .export-btn:hover:not(:disabled){background:#16955c}',
      '.edit-panel .clear-btn{background:transparent;color:#f5a524;',
      ' border:1px dashed rgba(245,165,36,.45);font-size:12px;padding:8px 12px}',
      '.edit-panel .clear-btn:hover{background:rgba(245,165,36,.08);border-color:rgba(245,165,36,.7)}',
      '.edit-panel .apply-btn:disabled,.edit-panel .undo-btn:disabled,',
      '.edit-panel .export-btn:disabled,.edit-panel .clear-btn:disabled{opacity:.4;cursor:not-allowed}',
      '.edit-panel .status{font-size:12px;line-height:1.5;margin:0;min-height:18px}',
      '.edit-panel .status.ok{color:#3fb950}',
      '.edit-panel .status.err{color:#f85149}',
      '.edit-panel-toggle-btn{position:fixed;right:24px;bottom:78px;z-index:2147483600;',
      ' display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:999px;',
      ' background:#9A0000;color:#fff;border:1px solid rgba(255,255,255,.18);',
      ' font:600 13px/1 "Source Han Sans SC","Noto Sans SC",-apple-system,sans-serif;',
      ' letter-spacing:.04em;cursor:pointer;box-shadow:0 8px 24px rgba(154,0,0,.35);',
      ' transition:transform .18s ease, background .18s ease}',
      '.edit-panel-toggle-btn:hover{background:#b50000;transform:translateY(-1px)}',
      'body.has-edit-panel deck-stage{transform-origin:top left;',
      ' transform:scale(calc((100vw - 360px) / 100vw))}',
      '@media print{.edit-panel,.edit-panel-toggle-btn{display:none!important}',
      ' body.has-edit-panel deck-stage{transform:none!important}}'
    ].join("\n");
    document.head.appendChild(css);

    /* Build the panel */
    const panel = document.createElement("aside");
    panel.className = "edit-panel";
    panel.innerHTML = [
      '<div class="edit-panel-head">',
      '  <h3>字段修改</h3>',
      '  <button type="button" class="edit-panel-close" title="关闭">×</button>',
      '</div>',
      '<p class="hint">只支持基于当前预览页字段的修改，不支持版式调整。修改保存在本浏览器，刷新仍生效；重新生成会丢失。</p>',
      '<label for="pku-edit-find">要替换的字段（请从当前页面完整粘贴）</label>',
      '<textarea id="pku-edit-find" spellcheck="false" placeholder="例如：基于注意力机制的医学影像分割研究"></textarea>',
      '<label for="pku-edit-replace">替换为</label>',
      '<textarea id="pku-edit-replace" spellcheck="false" placeholder="新内容"></textarea>',
      '<p class="warn">⚠ 新字段字数与原字段差异过大可能导致排版超出当前版面，请尽量控制在相近长度。</p>',
      '<div class="apply-row">',
      '  <button type="button" class="apply-btn">应用替换（仅作用于当前页）</button>',
      '  <button type="button" class="undo-btn" disabled title="撤回上次修改">↶ 撤回上次修改</button>',
      '  <button type="button" class="export-btn" title="下载已编辑后的网页包">⇩ 下载修改后的网页包</button>',
      '  <button type="button" class="clear-btn" title="清空本浏览器内已保存的全部修改">清空所有已保存修改</button>',
      '</div>',
      '<p class="status" role="status"></p>'
    ].join("");
    document.body.appendChild(panel);

    const findEl = panel.querySelector("#pku-edit-find");
    const replEl = panel.querySelector("#pku-edit-replace");
    const status = panel.querySelector(".status");
    const undoBtn = panel.querySelector(".undo-btn");
    const exportBtn = panel.querySelector(".export-btn");
    const clearBtn = panel.querySelector(".clear-btn");
    let lastEdit = null; /* [{ node, before }] — restored on undo */
    function setOpen(open) {
      document.body.classList.toggle("has-edit-panel", !!open);
    }
    panel.querySelector(".edit-panel-close").addEventListener("click", () => setOpen(false));
    panel.querySelector(".apply-btn").addEventListener("click", () => {
      const needle = findEl.value;
      const replacement = replEl.value;
      if (!needle) {
        status.className = "status err";
        status.textContent = "请输入要替换的字段。";
        return;
      }
      const slide = activeSlideEl();
      if (!slide) {
        status.className = "status err";
        status.textContent = "未找到当前幻灯片。";
        return;
      }
      const result = replaceInTextNodes(slide, needle, replacement);
      if (result.count > 0) {
        lastEdit = result.snapshots;
        appendStoredEdit(needle, replacement, activeSlideIndex());
        undoBtn.disabled = false;
        status.className = "status ok";
        status.textContent = "✓ 已在当前页替换 " + result.count + " 处（已保存，刷新仍生效）。";
      } else {
        status.className = "status err";
        status.textContent = "✗ 当前页没有找到该字段。请检查是否完整粘贴自当前预览页（区分空格、标点）。";
      }
    });
    undoBtn.addEventListener("click", () => {
      if (!lastEdit || !lastEdit.length) return;
      let restored = 0;
      lastEdit.forEach((s) => {
        if (s.node && s.node.parentNode) {
          s.node.nodeValue = s.before;
          restored++;
        }
      });
      popStoredEdit();
      lastEdit = null;
      undoBtn.disabled = true;
      status.className = restored ? "status ok" : "status err";
      status.textContent = restored
        ? "↶ 已撤回上一次修改（" + restored + " 处文本恢复）。"
        : "✗ 上次修改的节点已失效，无法撤回。";
    });
    clearBtn.addEventListener("click", () => {
      if (!loadStoredEdits().length) {
        status.className = "status";
        status.textContent = "没有需要清空的已保存修改。";
        return;
      }
      if (!confirm("清空本浏览器中已保存的所有修改？页面会重新加载。")) return;
      clearStoredEdits();
      location.reload();
    });
    exportBtn.addEventListener("click", async () => {
      status.className = "status";
      status.textContent = "正在打包修改后的网页包...";
      exportBtn.disabled = true;
      try {
        await downloadEditedZip();
        status.className = "status ok";
        status.textContent = "✓ 已开始下载修改后的网页包。";
      } catch (e) {
        status.className = "status err";
        status.textContent = "✗ 导出失败：" + (e && e.message ? e.message : e);
      } finally {
        exportBtn.disabled = false;
      }
    });

    /* Toggle button */
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "edit-panel-toggle-btn";
    btn.title = "修改当前页字段（仅文本替换，不改版式）";
    btn.innerHTML = '<span>✎</span><span>修改字段</span>';
    btn.addEventListener("click", () => {
      setOpen(!document.body.classList.contains("has-edit-panel"));
    });
    document.body.appendChild(btn);
  }

  /* ---------- on-screen prev/next nav arrows ----------
   * Small, semi-transparent, grouped at the bottom-left so users can keep
   * navigating while the field-edit panel claims the keyboard. */
  function injectNavArrows() {
    if (document.querySelector(".nav-arrows")) return;
    const css = document.createElement("style");
    css.textContent = [
      '.nav-arrows{position:fixed;left:18px;bottom:18px;z-index:2147483601;',
      ' display:inline-flex;gap:6px;opacity:.35;transition:opacity .18s ease}',
      '.nav-arrows:hover{opacity:.95}',
      '.nav-arrow{appearance:none;width:30px;height:30px;border-radius:50%;',
      ' display:inline-flex;align-items:center;justify-content:center;',
      ' background:rgba(154,0,0,.7);color:#fff;border:1px solid rgba(255,255,255,.22);',
      ' font:600 16px/1 -apple-system,sans-serif;cursor:pointer;padding:0;',
      ' box-shadow:0 4px 12px rgba(0,0,0,.25)}',
      '.nav-arrow:hover{background:rgba(154,0,0,.95)}',
      '.nav-arrow:active{transform:scale(.92)}',
      '@media print{.nav-arrows{display:none!important}}'
    ].join("\n");
    document.head.appendChild(css);

    const nav = document.createElement("div");
    nav.className = "nav-arrows";
    nav.innerHTML =
      '<button type="button" class="nav-arrow nav-prev" title="上一页">‹</button>' +
      '<button type="button" class="nav-arrow nav-next" title="下一页">›</button>';
    const stage = document.querySelector("deck-stage");
    nav.querySelector(".nav-prev").addEventListener("click", () => {
      if (stage && typeof stage.prev === "function") stage.prev();
    });
    nav.querySelector(".nav-next").addEventListener("click", () => {
      if (stage && typeof stage.next === "function") stage.next();
    });
    document.body.appendChild(nav);
  }

  NS.render = renderDeck;
  NS.layouts = layouts;
  NS.init = init;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
