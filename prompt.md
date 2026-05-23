下面是一版**整合后的干净版 prompt**，已经包含：

* 你的 GitHub 仓库：`git@github.com:fxt-gw-pb/pku_ppt_try.git`
* SSH 优先规则
* Git 操作规范
* DeepSeek API Key 应该填在哪里
* skill 工程化目标
* 后端 API
* 前端 demo
* README 要求
* mock 模式
* 提交和 push 规则

你可以直接复制给 Codex / Claude Code / 其他编程 agent。

````markdown
你现在要帮我基于一个自制的 PPT skill 文件夹，搭建一个“文稿生成 PPT”的最小可运行工程。

我的 GitHub 仓库是：

```text
git@github.com:fxt-gw-pb/pku_ppt_try.git
````

GitHub 用户名是：

```text
fxt-gw-pb
```

我已经在这台电脑上配置好了 GitHub SSH key。以后和 GitHub 仓库交互时，请优先使用 SSH 地址，不要优先使用 HTTPS token 方式。

---

# 一、GitHub 和 Git 操作规则

请严格遵守以下规则。

## 1. 优先使用 SSH

和 GitHub 仓库交互时，优先使用 SSH 地址，例如：

```bash
git clone git@github.com:fxt-gw-pb/pku_ppt_try.git
```

不要使用 HTTPS token 方式，除非 SSH 失败。

如果需要设置 remote，请使用：

```bash
git remote set-url origin git@github.com:fxt-gw-pb/pku_ppt_try.git
```

## 2. 修改仓库前必须先检查状态

在对仓库做任何修改前，请先执行：

```bash
pwd
git status
git remote -v
git branch
```

请确认：

1. 当前目录是正确的项目目录。
2. 当前仓库是我的仓库。
3. remote 指向的是：

```text
git@github.com:fxt-gw-pb/pku_ppt_try.git
```

4. 当前分支清楚明确，通常应为 `main` 或当前工作分支。

如果当前仓库不是我的仓库，或者 remote 指向别人的仓库，请不要直接 push。请先提醒我需要 fork 或修改 remote。

## 3. 修改代码时的工作流程

如果要修改代码，请遵循：

1. 先说明准备修改哪些文件。
2. 修改后运行必要的测试或检查。
3. 用 `git diff` 展示修改内容。
4. 确认没有无关文件后再 `git add`。
5. commit 信息要简洁清楚。
6. push 前再次执行：

```bash
git status
```

7. 最后 push 到我的 GitHub 仓库。

推荐 commit message 示例：

```bash
git commit -m "Build MVP PPT generation pipeline"
```

## 4. GitHub API 相关规则

如果任务只是 clone、pull、commit、push，请使用 SSH。

但如果任务需要调用 GitHub REST API 或 GraphQL API，例如：

* 创建 issue
* 查询 PR
* 读取 GitHub Actions 状态
* 创建 release
* 访问 `https://api.github.com/...`

那么 SSH key 不能替代 API auth。

此时请优先使用 GitHub CLI 的已登录状态，例如：

```bash
gh api ...
```

如果 `gh` 不可用，再提示我设置：

```bash
GH_TOKEN
```

或：

```bash
GITHUB_TOKEN
```

并遵循最小权限原则。

---

# 二、项目目标

我现在有一个自制的 PPT skill 文件夹，这个 skill 是基于 HTML 的，用于根据输入文稿生成 PPT/幻灯片内容。

我的目标是把它改造成一个可以用于网站服务的工程：

```text
用户在网页提交文稿
  → 后端接收文稿
  → 后端调用 DeepSeek API 把文稿整理成 slide_json
  → 后端调用我的 HTML-based PPT skill 生成幻灯片
  → 输出 HTML / PDF / PPTX
  → 网站前端显示任务状态
  → 用户下载成品文件
```

请注意：

大模型只负责“理解文稿并生成结构化 slide_json”。

PPT skill 负责“根据 slide_json 渲染幻灯片”。

不要让大模型直接生成最终 HTML 或 PPTX。

---

# 三、请先阅读和判断项目结构

请先完整阅读当前文件夹结构和关键文件，理解这个 skill 的运行方式、输入输出格式、依赖、HTML 模板、CSS、主题和渲染逻辑。

不要一开始就大规模重构。

请在尽量保留原有 skill 核心逻辑的基础上，把它封装成一个稳定、可被后端调用的“PPT 生成引擎”。

请判断当前项目更适合 Node.js 还是 Python：

* 如果当前 skill 主要是 HTML / JS / Node.js，请优先使用 Node.js。
* 如果当前 skill 主要是 Python，请优先使用 Python。
* 如果二者都有，请选择改动最少、最适合当前项目的方案。

---

# 四、DeepSeek API Key 配置要求

我准备用 DeepSeek API，因为成本较低。

真实 API Key 只允许填写在：

```text
项目根目录的 .env 文件
```

或者后端部署平台的环境变量设置中。

不要把真实 API Key 写入：

* 前端代码
* GitHub Pages
* HTML 文件
* JS 浏览器端文件
* README
* Git commit
* 任何会被上传到 GitHub 的文件

请创建 `.env.example`，内容至少包括：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

MAX_INPUT_CHARS=30000
OUTPUT_DIR=outputs
JOB_DIR=data/jobs
```

请不要创建包含真实 key 的 `.env`。

我会自己执行：

```bash
cp .env.example .env
```

然后手动编辑 `.env`：

```env
DEEPSEEK_API_KEY=这里填我的真实DeepSeek API Key
```

请新增或更新 `.gitignore`，确保至少包含：

```gitignore
.env
node_modules/
outputs/
data/jobs/
temp/
dist/
__pycache__/
```

后端启动时应从环境变量读取 API Key。

如果没有检测到 `DEEPSEEK_API_KEY`，程序应给出清晰错误提示。

---

# 五、新增 LLM 适配层

请新增一个独立的 LLM 适配层，不要把 DeepSeek 调用逻辑散落在各个文件中。

建议结构：

```text
src/llm/
  ├── index.js / index.py
  └── deepseek.js / deepseek.py
```

请实现通用函数：

```text
generateSlideJson(manuscript, options)
```

功能：

1. 输入用户文稿。
2. 调用 DeepSeek API。
3. 输出严格 JSON。
4. 返回对象必须包含：

   * title
   * subtitle
   * slides

每页 slide 至少包含：

```json
{
  "type": "content",
  "title": "页面标题",
  "bullets": ["要点1", "要点2"],
  "notes": "可选讲稿备注",
  "layout": "可选布局类型"
}
```

可选字段可以包括：

```text
image_prompt
chart_suggestion
speaker_notes
section
```

请使用 OpenAI-compatible SDK 或 HTTP 请求调用 DeepSeek API。

如果是 Node.js，可以使用类似：

```js
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com"
});
```

如果是 Python，可以使用类似：

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
```

调用模型时，请强制要求模型只输出 JSON，不要输出 Markdown，不要解释。

建议 system prompt：

```text
你是一个专业 PPT 策划助手。你的任务是把用户提供的文稿整理成结构化幻灯片 JSON。

请严格输出 JSON，不要输出 Markdown，不要输出解释，不要使用代码块。

JSON 顶层必须包含：
- title
- subtitle
- slides

slides 是数组，每个元素代表一页幻灯片。每页至少包含：
- type
- title
- bullets

可选字段：
- notes
- layout
- image_prompt
- chart_suggestion

请根据文稿内容自动拆分页数，保证逻辑清晰、标题明确、要点简洁。
```

请对模型返回结果做校验：

1. 如果不是合法 JSON，报错并记录原始返回。
2. 如果缺少 `slides` 字段，报错。
3. 如果 `slides` 为空，报错。
4. 如果某页缺少 `title` 或 `bullets`，请做基本修复或报错。
5. 请把最终 `slide_json` 保存到输出目录，方便调试。

---

# 六、增加 mock 模式

请支持 mock 模式，用于在没有真实 DeepSeek API Key 时测试完整流程。

`.env` 中可以设置：

```env
LLM_PROVIDER=mock
```

mock 模式下：

1. 不调用 DeepSeek API。
2. 使用固定示例 `slide_json`。
3. 仍然完整测试：

   * slide_json 生成
   * HTML 渲染
   * 文件导出
   * 后端 API
   * 前端 demo

---

# 七、封装当前 PPT skill

请把当前 HTML 渲染逻辑封装成清晰函数。

建议至少包含：

```text
generateSlideJson(manuscript, options)
renderHtml(slideJson, options)
exportFile(html, outputPath, options)
```

可以根据项目语言整理为：

```text
src/
  ├── llm/
  ├── renderer/
  ├── exporter/
  └── index.js / index.py
```

请尽量保留原有 HTML 模板、CSS、主题和排版逻辑。

目标是让当前 skill 可以通过命令行调用。

Node.js 项目示例：

```bash
npm run generate -- --input examples/input.md --output outputs/demo
```

Python 项目示例：

```bash
python scripts/generate.py --input examples/input.md --output outputs/demo
```

生成结果至少包括：

```text
outputs/demo/slide.json
outputs/demo/index.html
```

如果当前工程方便支持 PDF，请增加：

```text
outputs/demo/output.pdf
```

如果当前工程方便支持 PPTX，请增加：

```text
outputs/demo/output.pptx
```

如果 PDF/PPTX 暂时难度较大，请先实现 HTML 输出，并在 README 中说明后续如何扩展。

---

# 八、新增最小后端 API

请新增 `server` 或 `api` 目录，提供一个最小后端服务。

## 1. 创建任务

```http
POST /api/jobs
```

请求体：

```json
{
  "manuscript": "用户粘贴的文稿",
  "style": "academic"
}
```

返回：

```json
{
  "job_id": "xxx",
  "status": "pending"
}
```

## 2. 查询任务状态

```http
GET /api/jobs/:id
```

返回：

```json
{
  "job_id": "xxx",
  "status": "running",
  "download_url": null,
  "error": null
}
```

任务状态至少包括：

```text
pending
running
done
failed
```

## 3. 下载结果

```http
GET /api/jobs/:id/download
```

如果生成完成，返回生成的 HTML、PDF 或 PPTX 文件。

初版可以用本地 JSON 文件或内存对象保存任务状态，不要求立刻接入数据库。

后端任务流程应为：

```text
用户文稿
  → generateSlideJson()
  → renderHtml()
  → exportFile()
  → 更新 job 状态为 done
```

请对输入文本长度做限制，默认使用：

```env
MAX_INPUT_CHARS=30000
```

任务失败时，应保存错误信息，方便排查。

---

# 九、新增最小前端 demo

请新增 `web` 或 `frontend` 目录，提供一个最小网页 demo。

页面功能：

1. 一个文本框，用于粘贴文稿。
2. 一个“生成 PPT”按钮。
3. 显示任务状态。
4. 生成完成后显示下载链接。

前端通过 HTTP 请求调用后端 API：

```text
POST /api/jobs
GET /api/jobs/:id
GET /api/jobs/:id/download
```

请注意：

1. 前端不要包含 API Key。
2. 前端只和我自己的后端通信。
3. 前端代码未来可以部署到 GitHub Pages。
4. 后端未来可以部署到 Render、Railway、Fly.io、Vercel Serverless 或其他平台。

---

# 十、项目结构建议

请尽量整理成类似结构，但可以根据当前项目实际情况调整：

```text
.
├── README.md
├── package.json / pyproject.toml / requirements.txt
├── .env.example
├── .gitignore
├── examples/
│   └── input.md
├── outputs/
├── data/
│   └── jobs/
├── src/
│   ├── index.js / index.py
│   ├── llm/
│   ├── renderer/
│   ├── exporter/
│   └── schema/
├── scripts/
│   └── generate.js / generate.py
├── server/
│   └── app.js / app.py
└── web/
    ├── index.html
    ├── style.css
    └── app.js
```

---

# 十一、README 文档要求

请新增或更新 `README.md`，必须包含：

1. 当前项目用途。
2. 项目结构说明。
3. 如何安装依赖。
4. 如何配置 DeepSeek API Key。
5. 如何从 `.env.example` 创建 `.env`。
6. 如何运行 mock 模式。
7. 如何运行命令行生成 PPT。
8. 如何启动后端 API。
9. 如何打开前端 demo。
10. 当前支持的输出格式。
11. 当前没有实现但后续可以扩展的能力。
12. 如何部署成：

    * GitHub Pages 前端
    * 独立后端服务
    * 后端环境变量配置

README 中必须明确写：

```text
真实 API Key 只应填写在项目根目录的 .env 文件中，或者填写在后端部署平台的环境变量设置中。不要写入前端代码，不要提交到 GitHub。
```

请给出示例：

```bash
cp .env.example .env
```

然后提示我手动编辑 `.env`：

```env
DEEPSEEK_API_KEY=这里填我的真实DeepSeek API Key
```

---

# 十二、本地验证要求

完成修改后，请尽量在终端验证以下流程：

1. 安装依赖成功。
2. `.env.example` 存在。
3. `.gitignore` 已排除 `.env`。
4. mock 模式能生成 slide_json。
5. mock 模式能生成 HTML。
6. 有真实 DeepSeek API Key 时，可以调用 DeepSeek 生成 slide_json。
7. 后端服务能启动。
8. 前端 demo 能提交文稿并查询任务状态。
9. 生成结果能下载或在浏览器打开。

如果因为没有真实 DeepSeek API Key 无法完整调用，请使用 mock 模式完成端到端验证。

---

# 十三、Git 提交要求

完成工程修改并验证后，请执行：

```bash
git diff
git status
```

确认修改内容合理，没有无关文件。

不要提交：

```text
.env
outputs/
data/jobs/
node_modules/
temp/
dist/
__pycache__/
```

然后执行：

```bash
git add .
git commit -m "Build MVP PPT generation pipeline"
git status
git push origin main
```

如果当前分支不是 `main`，请先告诉我当前分支，并根据情况决定 push 到当前分支还是 main。

push 前必须确认 remote 是：

```text
git@github.com:fxt-gw-pb/pku_ppt_try.git
```

如果不是，请不要 push，先提醒我。

---

# 十四、完成后请输出总结

完成后，请给我一个总结，包含：

1. 当前 skill 原本的核心运行逻辑是什么。
2. 你新增或修改了哪些文件。
3. API Key 应该填在哪里。
4. 如何运行 mock 模式。
5. 如何本地运行命令行生成。
6. 如何启动后端服务。
7. 如何打开前端 demo。
8. 当前输出格式是什么。
9. 已经 push 到哪个 GitHub 仓库和哪个分支。
10. 如果要部署成真正给别人使用的网站，还缺哪些能力。

````

你实际填 API Key 的位置只有两个：

```text
本地开发：项目根目录 .env
线上部署：后端平台的 Environment Variables
````

不要填到 GitHub Pages、前端 JS、HTML、README 或 commit 里。
