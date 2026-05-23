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
