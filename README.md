# PKU 红 · 文稿生成 PPT

把一段中文文稿（摘要 / 开题报告 / 答辩讲稿）喂给 LLM，自动生成一份 PKU 红风格的学术答辩 HTML 幻灯片，可在线预览或下载为 zip。

```
文稿 ──► DeepSeek (or mock) ──► slide_json
                                    │
                                    ▼
                          编译为 PKU slides.json
                                    │
                                    ▼
                       套用 HTML 模板 → 可运行 deck
                                    │
                                    ▼
                      浏览器预览 / 下载 zip / 打印 PDF
```

> 当前 MVP 输出 **HTML 幻灯片包**（含 deck-stage 渲染时常用的全部资源），可在浏览器内通过 Print → Save as PDF 导出 PDF。PPTX 暂未实现，参见 §扩展 一节。

---

## 项目结构

```
.
├── README.md
├── .env.example                # API key 模板；复制为 .env 后再填真实 key
├── .gitignore
├── requirements.txt
├── CLAUDE.md                   # Claude Code 工作指引
├── prompt.md                   # 原始需求 brief（本工程即按此构建）
│
├── index.html                  # 原始 PKU 模板 deck（独立可运行）
├── deck-stage.js               #   ↳ 通用幻灯片舞台 (web component)
├── data/slides.json            #   ↳ 默认示例 deck 数据
├── assets/                     #   ↳ CSS / 渲染脚本 / 示例图片
│
├── pku-red-defense-ppt/        # 已打包的 Claude skill
│   ├── SKILL.md
│   ├── references/             # 模板规范、JSON schema、layout 选择、图片规则
│   ├── scripts/                # create_deck.py / validate_slides.py
│   └── assets/template/        # ← 后端生成 deck 时拷贝的模板源
│
├── examples/
│   └── input.md                # 示例文稿
│
├── src/                        # 后端核心库
│   ├── llm/                    #   ↳ DeepSeek + mock provider
│   ├── schema/                 #   ↳ 校验 LLM 输出的 generic slide_json
│   ├── renderer/               #   ↳ generic → PKU slides.json 编译
│   └── exporter/               #   ↳ 物化模板 + 打 zip
│
├── scripts/
│   └── generate.py             # 命令行：文稿 → deck
│
├── server/
│   └── app.py                  # FastAPI 后端
│
├── web/                        # 最小前端 demo
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── outputs/                    # （gitignored）生成的 deck 与 zip
└── data/jobs/                  # （gitignored）任务状态 JSON
```

---

## 一、安装

需要 Python 3.10+。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 二、配置 DeepSeek API Key（可选）

**真实 API Key 只允许填写在两个位置：**

1. 本地开发：项目根目录的 `.env` 文件。
2. 线上部署：后端部署平台（Render / Railway / Fly.io / Vercel Serverless 等）的环境变量。

**不要**把真实 key 写入前端代码、HTML、README、commit、GitHub Pages、浏览器端 JS。

复制模板并编辑：

```bash
cp .env.example .env
# 用编辑器打开 .env，填入：
#   LLM_PROVIDER=deepseek
#   DEEPSEEK_API_KEY=你的真实 DeepSeek API Key
```

`.gitignore` 已排除 `.env`，不会被 commit。

---

## 三、Mock 模式（无 Key 也能跑通）

`.env` 里设：

```env
LLM_PROVIDER=mock
```

或者命令行临时指定：

```bash
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
```

Mock 模式下不调用 DeepSeek，使用固定示例 `slide_json`，但其余流程（编译 / 渲染 / 导出 / API / 前端 demo）完全跑通，便于本地端到端调试。

---

## 四、命令行生成 PPT

```bash
python scripts/generate.py \
  --input examples/input.md \
  --output outputs/demo
```

完成后会在 `outputs/demo/` 下得到一份可运行的 deck：

```
outputs/demo/
├── index.html
├── deck-stage.js
├── assets/{base.css, runtime.js, theme-pku-red.css, media/...}
└── data/
    ├── slides.json     # 编译后的 PKU 格式（runtime.js 直接读取）
    └── slide.json      # 原始 LLM 输出（generic 格式，用于调试）
```

浏览器预览：

```bash
cd outputs/demo
python3 -m http.server 8080
# open http://localhost:8080/index.html
```

导出 PDF：浏览器 Print → Save as PDF。`deck-stage.js` 自带 `@media print`，按 1280×720 排版一页一张。

---

## 五、启动后端 API

```bash
uvicorn server.app:app --reload --host 127.0.0.1 --port 8787
```

接口：

| 方法 | 路径 | 用途 |
|------|------|------|
| `GET`  | `/api/health` | 健康检查 + 当前 provider + 字数上限 |
| `POST` | `/api/jobs` | 创建生成任务，body: `{"manuscript": "...", "style": "academic"}` |
| `GET`  | `/api/jobs/{id}` | 查询状态: `pending / running / done / failed` |
| `GET`  | `/api/jobs/{id}/download` | 下载 deck.zip（任务完成后可用） |
| `GET`  | `/api/jobs/{id}/preview`  | 重定向到该 deck 的 `index.html` 在线预览 |

任务状态以 JSON 文件保存在 `data/jobs/<id>.json`（重启后仍可查询）。生成的 deck 与 zip 落在 `outputs/<id>/` 与 `outputs/<id>.zip`。

curl 示例：

```bash
curl -s -X POST http://127.0.0.1:8787/api/jobs \
  -H "Content-Type: application/json" \
  -d "$(jq -Rs '{manuscript: .}' examples/input.md)"

# → {"job_id":"abc123","status":"pending",...}

curl -s http://127.0.0.1:8787/api/jobs/abc123
# → {"job_id":"abc123","status":"done","download_url":"/api/jobs/abc123/download",...}

curl -s -o deck.zip http://127.0.0.1:8787/api/jobs/abc123/download
```

输入文本长度由 `MAX_INPUT_CHARS`（默认 30000）限制；超出返回 413。

---

## 六、前端 demo

后端启动后直接访问 [http://127.0.0.1:8787/](http://127.0.0.1:8787/) — `web/` 已被 FastAPI 静态挂载。

页面功能：

- 一个文本框，粘贴文稿。
- 一个 **生成 PPT** 按钮。
- 实时显示任务状态。
- 完成后给出 **在线预览** 和 **下载 .zip** 两个按钮。

前端只调用本机后端，**不持有任何 API Key**。

---

## 七、当前支持的输出

- ✅ **HTML 幻灯片**（含全部静态资源；用浏览器即可预览）
- ✅ **deck zip**（API 下载格式）
- ✅ **PDF**（通过浏览器 Print → Save as PDF；`deck-stage.js` 已包含打印样式）
- ⏳ **PPTX**：未实现。两条可行路径，见 §扩展。

---

## 八、数据流与 schema

### LLM 输出：generic slide_json（`src/llm/`、`src/schema/`）

```json
{
  "title": "演示主标题",
  "subtitle": "GRADUATION DEFENSE / OPENING REPORT",
  "slides": [
    { "type": "cover",    "title": "...", "bullets": [] },
    { "type": "contents", "title": "目录", "bullets": ["...","..."] },
    { "type": "section",  "title": "背景与意义", "bullets": ["...","..."] },
    {
      "type": "content",
      "title": "选题背景",
      "section": "背景与意义",
      "bullets": ["外部环境驱动：...", "现有方案的局限：..."],
      "layout": "multi-card"
    },
    { "type": "closing", "title": "感谢您的倾听！", "bullets": [] }
  ]
}
```

每页 `type ∈ {cover, contents, section, content, closing}`。可选字段：`notes, layout, image_prompt, chart_suggestion, speaker_notes, section`。

### 编译产物：PKU slides.json（`src/renderer/`）

按 `pku-red-defense-ppt/references/slides-json-schema.md` 描述的 PKU 模板格式输出，含 `meta`、`chapters[3-6]`、`slides[]` 与每个 layout 的特有字段。**`runtime.js` 只认这种格式**。

`runtime.js` 在浏览器端读取 `data/slides.json` 并渲染为一系列 `<section>`，所以后端不参与 HTML 渲染，无需 headless 浏览器或 puppeteer。

---

## 九、扩展（未实现但容易加上）

1. **PPTX 导出**：将 PKU `slides.json` 翻译为 `python-pptx` 调用，每个 layout 写一个对应的 PPTX 构造器；或通过 LibreOffice 把 HTML 转 PPTX。
2. **服务端 PDF**：用 Playwright headless Chromium 加载 `index.html` 后直接 `page.pdf({format:'A4 landscape'})`，省去用户手动 Print。
3. **真实 deepseek 流式调用**：当前 `chat.completions.create` 是单次同步调用；可改为 stream + SSE 让前端实时显示生成进度。
4. **图片自动配图**：`image_prompt` 字段已预留，可接入文生图模型后回填到 `slides[].images[].src`。
5. **任务队列**：当前是进程内 daemon thread；线上部署可换 Redis + RQ / Celery。
6. **多用户、计费、登录**：超出 MVP 范围。

---

## 十、部署提示

**前端**：`web/` 是纯静态，可直接发布到 GitHub Pages / Cloudflare Pages / Vercel Static。注意在 `web/app.js` 中把 `API_BASE` 指向真实后端域名。

**后端**：FastAPI + Uvicorn 可直接部署到 Render / Railway / Fly.io，启动命令：

```bash
uvicorn server.app:app --host 0.0.0.0 --port $PORT
```

部署平台的 **Environment Variables** 设置中填入：

```
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<真实 key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MAX_INPUT_CHARS=30000
```

**Vercel Serverless**：可用，但要把 `outputs/` 改为 S3 / R2 / 临时签名 URL（无状态平台不能依赖本地文件落盘）。

**Cors**：当前 `server/app.py` 开了 `allow_origins=["*"]`。线上请改成你的前端真实域名。

---

## 十一、视觉守则（务必遵守）

PPT 模板部分保留原 PKU 学术答辩风格，**不要**把页面改成网页 landing page、营销卡片、玻璃拟态、紫蓝科技渐变或暗色 hero。详见 [`pku-red-defense-ppt/references/template-spec.md`](pku-red-defense-ppt/references/template-spec.md) 与原 README §视觉守则。

- 16:9 / 1280×720 设计画布；白底内容页；PKU 红 `#9A0000` 是唯一强调色。
- 红色仅用于：导航高亮、序号、关键短语、章节扉页背景、封面背景。
- 卡片浅灰边框 + 白底，不使用浓重投影。
- 这是学术答辩 deck，不是产品发布会。

---

## 十二、原始 PKU 模板（独立运行）

仓库根目录的 `index.html` + `deck-stage.js` + `data/slides.json` 是一套独立可运行的示例 deck，不需要后端：

```bash
python3 -m http.server 8080
# open http://localhost:8080/index.html
```

可以直接修改 `data/slides.json` 替换为你的内容，不走 LLM 流水线。详见 `pku-red-defense-ppt/SKILL.md`。

---

## 致谢与许可

本仓库整合自：
- 原始 PKU 红答辩 HTML 模板（已抽象为 skill `pku-red-defense-ppt/`）
- 本仓库新增的 LLM 适配层 / 编译器 / FastAPI 后端 / 前端 demo

许可：项目本身未指定 license，使用前请先评估贵研究 / 单位的合规要求；引用的字体 / 校徽 / 示例素材按其各自许可使用。
