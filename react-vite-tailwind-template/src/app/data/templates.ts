import {
  BarChart3,
  BookOpen,
  Code2,
  FileText,
  GraduationCap,
  Image,
  LayoutDashboard,
  Megaphone,
  Presentation,
  ShieldAlert,
  Sparkles,
  Terminal,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type TemplateId =
  | 'pku-red'
  | 'xhs-white-editorial'
  | 'tech-sharing'
  | 'pitch-deck'
  | 'product-launch'
  | 'weekly-report'
  | 'course-module'
  | 'xhs-post';

export interface TemplateOption {
  id: TemplateId;
  name: string;
  label: string;
  description: string;
  bestFor: string;
  icon: LucideIcon;
  accent: string;
}

export const templates: TemplateOption[] = [
  {
    id: 'pku-red',
    name: '北大红答辩',
    label: 'Academic',
    description: '严肃学术风格，适合论文答辩、开题报告和研究汇报。',
    bestFor: '毕业答辩 / 开题报告',
    icon: GraduationCap,
    accent: 'from-red-500 to-rose-600',
  },
  {
    id: 'xhs-white-editorial',
    name: '小红书白底杂志',
    label: 'Editorial',
    description: '白底强重点、杂志式大标题，适合中文知识图文。',
    bestFor: '知识帖 / 图文分享',
    icon: Image,
    accent: 'from-pink-500 to-orange-400',
  },
  {
    id: 'tech-sharing',
    name: '技术分享',
    label: 'Developer',
    description: '深色代码风，适合内部技术分享、架构复盘和工程实践。',
    bestFor: 'Tech Talk',
    icon: Code2,
    accent: 'from-emerald-400 to-sky-500',
  },
  {
    id: 'pitch-deck',
    name: '融资路演',
    label: 'Startup',
    description: '面向投资人的商业叙事结构，突出问题、方案和增长。',
    bestFor: 'Pitch Deck',
    icon: BarChart3,
    accent: 'from-blue-500 to-violet-600',
  },
  {
    id: 'product-launch',
    name: '产品发布',
    label: 'Launch',
    description: '现代发布会视觉，适合介绍产品亮点、定价和 CTA。',
    bestFor: '发布会 / 产品介绍',
    icon: Megaphone,
    accent: 'from-orange-400 to-fuchsia-500',
  },
  {
    id: 'weekly-report',
    name: '周报复盘',
    label: 'Report',
    description: '信息密度高，适合进展同步、数据复盘和下周计划。',
    bestFor: '团队周报',
    icon: LayoutDashboard,
    accent: 'from-cyan-500 to-blue-600',
  },
  {
    id: 'course-module',
    name: '课程模块',
    label: 'Learning',
    description: '带学习目标和模块结构，适合培训课件和工作坊。',
    bestFor: '课程 / Workshop',
    icon: BookOpen,
    accent: 'from-amber-400 to-lime-500',
  },
  {
    id: 'xhs-post',
    name: '竖版图文',
    label: 'Social',
    description: '3:4 图文轮播样式，适合小红书和社媒内容二次分发。',
    bestFor: '小红书轮播',
    icon: FileText,
    accent: 'from-rose-400 to-yellow-400',
  },
];
export const features = [
  {
    title: '文稿自动拆页',
    description: '把摘要、讲稿或 Markdown 自动整理成封面、章节、内容页和结尾页。',
    icon: Sparkles,
  },
  {
    title: '多风格模板',
    description: '学术、技术分享、融资路演、小红书图文等场景都可以快速切换。',
    icon: Presentation,
  },
  {
    title: '安全的后端生成',
    description: 'API Key 留在后端，前端只提交文稿和模板选择，便于上线部署。',
    icon: ShieldAlert,
  },
  {
    title: '可下载 HTML Deck',
    description: '生成结果可以在线预览，也可以下载为完整静态幻灯片包。',
    icon: Terminal,
  },
];
