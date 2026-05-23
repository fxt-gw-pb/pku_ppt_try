import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, PlayCircle, Sparkles } from 'lucide-react';
import Button from '../../components/ui/button';
import { features, templates } from '../../data/templates';

const Home = () => {
  return (
    <div className="bg-white dark:bg-gray-950">
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50 py-20 dark:from-gray-950 dark:via-gray-900 dark:to-slate-950">
        <div className="absolute left-1/2 top-0 h-72 w-72 -translate-x-1/2 rounded-full bg-blue-400/20 blur-3xl" />
        <div className="absolute bottom-0 right-10 h-80 w-80 rounded-full bg-purple-400/20 blur-3xl" />

        <div className="container relative mx-auto px-4">
          <div className="mx-auto max-w-5xl text-center">
            <span className="inline-flex items-center rounded-full border border-blue-200 bg-white/70 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm backdrop-blur dark:border-blue-900/60 dark:bg-gray-900/70 dark:text-blue-300">
              <Sparkles className="mr-2 h-4 w-4" />
              fxt ppt Studio
            </span>
            <h1 className="mt-8 text-5xl font-bold tracking-tight text-gray-950 dark:text-white md:text-7xl">
              从一段文稿开始，选择模板生成
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 bg-clip-text text-transparent">
                {' '}
                专业 PPT
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-xl leading-8 text-gray-600 dark:text-gray-300">
              面向答辩、技术分享、小红书图文、路演和周报的 fxt ppt 生成网站原型。先选模板，再粘贴文稿。
            </p>
            <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">
              <Link to="/generate">
                <Button size="lg" className="w-full sm:w-auto">
                  开始生成
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <a
                href="#templates"
                className="inline-flex items-center justify-center rounded-lg border-2 border-blue-600 px-6 py-3 text-lg font-medium text-blue-600 transition hover:bg-blue-50 dark:border-blue-400 dark:text-blue-300 dark:hover:bg-blue-950"
              >
                <PlayCircle className="mr-2 h-5 w-5" />
                先看模板
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white py-16 dark:bg-gray-950">
        <div className="container mx-auto px-4">
          <div className="grid gap-6 md:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon;

              return (
                <div
                  key={feature.title}
                  className="rounded-2xl border border-gray-200 bg-white p-6 shadow-lg shadow-blue-900/5 dark:border-gray-800 dark:bg-gray-900"
                >
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-950 dark:text-white">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-400">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section id="templates" className="bg-gray-50 py-20 dark:bg-gray-900">
        <div className="container mx-auto px-4">
          <div className="mb-12 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <p className="font-semibold uppercase tracking-[0.25em] text-blue-600 dark:text-blue-400">
                Template Gallery
              </p>
              <h2 className="mt-3 text-4xl font-bold text-gray-950 dark:text-white">
                选择一个模板作为生成起点
              </h2>
              <p className="mt-3 max-w-2xl text-gray-600 dark:text-gray-300">
                每个模板对应一种表达场景。选择后会带入生成页，你仍然可以在下一页切换。
              </p>
            </div>
            <Link to="/generate">
              <Button variant="outline" size="lg">
                跳到输入文稿
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>

          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {templates.map((template) => {
              const Icon = template.icon;

              return (
                <Link
                  key={template.id}
                  to={`/generate?template=${template.id}`}
                  className="group rounded-3xl border border-gray-200 bg-white p-6 shadow-xl shadow-blue-950/5 transition-all hover:-translate-y-1 hover:border-blue-300 hover:shadow-2xl dark:border-gray-800 dark:bg-gray-950 dark:hover:border-blue-700"
                >
                  <div
                    className={`mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${template.accent} text-white shadow-lg`}
                  >
                    <Icon className="h-7 w-7" />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-xl font-bold text-gray-950 dark:text-white">{template.name}</h3>
                    <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                      {template.label}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-400">
                    {template.description}
                  </p>
                  <div className="mt-5 flex items-center text-sm font-semibold text-blue-600 dark:text-blue-400">
                    用这个模板生成
                    <ArrowRight className="ml-2 h-4 w-4 transition group-hover:translate-x-1" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-gradient-to-r from-blue-600 to-purple-600 py-16">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 text-white md:grid-cols-3">
            {['选择模板', '粘贴文稿', '预览下载'].map((step, index) => (
              <div key={step} className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/15 font-bold">
                  {index + 1}
                </div>
                <div>
                  <div className="flex items-center gap-2 text-xl font-bold">
                    <CheckCircle2 className="h-5 w-5" />
                    {step}
                  </div>
                  <p className="mt-1 text-white/75">三步完成一份 PPT 原型。</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
