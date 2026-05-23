import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle2, Clock3, Download, Eye, FileText, Info, Loader2, Wand2 } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '../../components/ui/button';
import { templates, type TemplateId } from '../../data/templates';

const exampleText =
  '粘贴论文摘要、产品方案、技术分享提纲或小红书长文。AI 会根据文稿结构生成标题、章节、要点和演讲顺序。';

const statusSteps = [
  { label: '解析文稿', isDone: (status: 'idle' | 'generating' | 'done') => status !== 'idle' },
  { label: '匹配模板结构', isDone: (status: 'idle' | 'generating' | 'done') => status !== 'idle' },
  { label: '生成幻灯片预览', isDone: (status: 'idle' | 'generating' | 'done') => status === 'done' },
];

const Generate = () => {
  const [searchParams] = useSearchParams();
  const initialTemplate = (searchParams.get('template') as TemplateId) || 'pku-red';
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId>(
    templates.some((template) => template.id === initialTemplate) ? initialTemplate : 'pku-red'
  );
  const [manuscript, setManuscript] = useState('');
  const [status, setStatus] = useState<'idle' | 'generating' | 'done'>('idle');

  const activeTemplate = useMemo(
    () => templates.find((template) => template.id === selectedTemplate) || templates[0],
    [selectedTemplate]
  );

  const handleGenerate = () => {
    if (!manuscript.trim()) {
      toast.error('请先粘贴文稿内容');
      return;
    }

    setStatus('generating');
    window.setTimeout(() => {
      setStatus('done');
      toast.success('原型生成完成，可以查看预览');
    }, 900);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <section className="bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 py-12 dark:from-gray-950 dark:via-gray-900 dark:to-slate-950">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl text-center">
            <span className="inline-flex items-center rounded-full border border-blue-200 bg-white/70 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm backdrop-blur dark:border-blue-900/60 dark:bg-gray-900/70 dark:text-blue-300">
              <Wand2 className="mr-2 h-4 w-4" />
              AI PPT Generator
            </span>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-gray-950 dark:text-white md:text-5xl">
              输入文稿，生成一份可预览的
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                {' '}
                PPT 原型
              </span>
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-lg text-gray-600 dark:text-gray-300">
              选择模板、粘贴文稿、点击生成。这里展示产品交互原型，后续可接入真实后端任务队列和下载链接。
            </p>
          </div>
        </div>
      </section>

      <main className="container mx-auto grid gap-8 px-4 py-10 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="space-y-6">
          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-xl shadow-blue-900/5 dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-950 dark:text-white">1. 选择模板</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  当前选择：{activeTemplate.name}
                </p>
              </div>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                {activeTemplate.label}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {templates.map((template) => {
                const Icon = template.icon;
                const isSelected = selectedTemplate === template.id;

                return (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`rounded-2xl border p-4 text-left transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 shadow-lg shadow-blue-900/10 dark:border-blue-400 dark:bg-blue-950/30'
                        : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-950 dark:hover:border-blue-700'
                    }`}
                  >
                    <div
                      className={`mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${template.accent} text-white`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="font-semibold text-gray-950 dark:text-white">{template.name}</div>
                    <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {template.bestFor}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-xl shadow-blue-900/5 dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-950 dark:text-white">2. 输入文稿</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                支持中文、Markdown、提纲或完整讲稿。
              </p>
            </div>
            <textarea
              value={manuscript}
              onChange={(event) => setManuscript(event.target.value)}
              placeholder={exampleText}
              className="min-h-72 w-full resize-y rounded-2xl border border-gray-200 bg-gray-50 p-4 text-gray-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-100"
            />
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {manuscript.length} / 30000 字
              </span>
              <Button size="lg" onClick={handleGenerate} isLoading={status === 'generating'}>
                <Wand2 className="mr-2 h-5 w-5" />
                生成 PPT
              </Button>
            </div>
          </div>
        </section>

        <aside className="rounded-3xl border border-gray-200 bg-white p-6 shadow-xl shadow-purple-900/5 dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-950 dark:text-white">生成状态 / 预览</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">模拟后端任务队列和在线预览。</p>
            </div>
            {status === 'done' ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-500" />
            ) : status === 'generating' ? (
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            ) : (
              <Clock3 className="h-6 w-6 text-gray-400" />
            )}
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-gradient-to-br from-gray-950 to-gray-800 text-white shadow-2xl dark:border-gray-700">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
              <div className="flex gap-2">
                <span className="h-3 w-3 rounded-full bg-red-400" />
                <span className="h-3 w-3 rounded-full bg-yellow-400" />
                <span className="h-3 w-3 rounded-full bg-green-400" />
              </div>
              <span className="text-xs text-gray-400">preview.html</span>
            </div>
            <div className="aspect-video p-6">
              <div className="flex h-full flex-col justify-between rounded-xl bg-white p-5 text-gray-950">
                <div>
                  <div className={`mb-5 h-2 w-28 rounded-full bg-gradient-to-r ${activeTemplate.accent}`} />
                  <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-400">
                    {activeTemplate.label}
                  </p>
                  <h3 className="mt-3 text-2xl font-black leading-tight">
                    {manuscript.trim() ? manuscript.trim().split('\n')[0].slice(0, 34) : 'fxt ppt 生成预览'}
                  </h3>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[1, 2, 3].map((item) => (
                    <div key={item} className="rounded-lg bg-gray-100 p-3">
                      <FileText className="mb-2 h-4 w-4 text-gray-400" />
                      <div className="h-2 rounded bg-gray-300" />
                      <div className="mt-2 h-2 w-2/3 rounded bg-gray-200" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {statusSteps.map((step) => (
              <div
                key={step.label}
                className="flex items-center justify-between rounded-xl bg-gray-50 px-4 py-3 dark:bg-gray-950"
              >
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {step.label}
                </span>
                {step.isDone(status) ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <span className="h-5 w-5 rounded-full border border-gray-300 dark:border-gray-700" />
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-100">
            <div className="flex gap-3">
              <Info className="mt-0.5 h-5 w-5 flex-none" />
              <p>
                抱歉，当前 PPT 生成功能只支持导出为 HTML 和 PDF，不支持导出为 PPTX 文件。
                若要导出为 PDF，请点击进入预览页后，在浏览器中使用打印快捷键：
                Windows/Linux 为 <kbd className="rounded border border-amber-300 bg-white px-1.5 py-0.5 text-xs font-semibold text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">Ctrl + P</kbd>
                ，Mac 为 <kbd className="rounded border border-amber-300 bg-white px-1.5 py-0.5 text-xs font-semibold text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">Command + P</kbd>
                ，然后选择“另存为 PDF”或“保存为 PDF”。
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <Button variant="outline" disabled={status !== 'done'}>
              <Eye className="mr-2 h-4 w-4" />
              进入预览页
            </Button>
            <Button variant="secondary" disabled={status !== 'done'}>
              <Download className="mr-2 h-4 w-4" />
              下载 HTML
            </Button>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default Generate;
