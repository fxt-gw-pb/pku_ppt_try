import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="border-t border-gray-200 bg-white text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
      <div className="container mx-auto flex flex-col gap-6 px-4 py-8 md:flex-row md:items-center md:justify-between">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="font-bold text-gray-950 dark:text-white">fxt ppt</div>
            <div className="text-sm">两页式 fxt ppt 生成网站原型</div>
          </div>
        </Link>

        <div className="flex flex-wrap gap-4 text-sm">
          <Link to="/" className="transition hover:text-blue-600 dark:hover:text-blue-400">
            选模板
          </Link>
          <Link to="/generate" className="transition hover:text-blue-600 dark:hover:text-blue-400">
            输入文稿
          </Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
