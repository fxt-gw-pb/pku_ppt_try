import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Sparkles, Wand2, X } from 'lucide-react';

const navLinks = [
  { path: '/', label: '选模板' },
  { path: '/generate', label: '输入文稿' },
];

const Header = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/70 bg-white/85 shadow-sm backdrop-blur-xl dark:border-gray-800/70 dark:bg-gray-950/85">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xl font-black tracking-tight text-gray-950 dark:text-white">
                fxt ppt
              </span>
              <span className="hidden text-xs text-gray-500 dark:text-gray-400 sm:block">
                fxt ppt 生成网站原型
              </span>
            </div>
          </Link>

          <ul className="hidden items-center gap-2 md:flex">
            {navLinks.map((link) => (
              <li key={link.path}>
                <Link
                  to={link.path}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                    isActive(link.path)
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-950 dark:text-gray-300 dark:hover:bg-gray-900 dark:hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="hidden md:block">
            <Link
              to="/generate"
              className="inline-flex items-center rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition hover:shadow-xl"
            >
              <Wand2 className="mr-2 h-4 w-4" />
              开始生成
            </Link>
          </div>

          <button
            type="button"
            onClick={() => setIsMenuOpen((open) => !open)}
            className="rounded-xl p-2 text-gray-700 transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-900 md:hidden"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {isMenuOpen && (
          <div className="mt-4 space-y-2 border-t border-gray-200 pt-4 dark:border-gray-800 md:hidden">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setIsMenuOpen(false)}
                className={`block rounded-xl px-4 py-3 font-semibold ${
                  isActive(link.path)
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                    : 'text-gray-700 dark:text-gray-300'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
