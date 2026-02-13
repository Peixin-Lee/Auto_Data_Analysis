import { Button } from './ui/button';
import { Moon, Sun, Gift } from 'lucide-react';
import { motion } from 'framer-motion';

interface HeaderProps {
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function Header({ theme, onToggleTheme }: HeaderProps) {
  return (
    <header className={`py-4 px-6 border-b backdrop-blur-xl transition-all ${
      theme === 'light' 
        ? 'bg-white/40 border-white/20 shadow-lg shadow-purple-500/5' 
        : 'bg-slate-900/60 border-slate-700/50 shadow-lg shadow-blue-500/10'
    }`}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
            theme === 'light'
              ? 'from-indigo-600 via-purple-600 to-pink-600'
              : 'from-blue-400 via-cyan-400 to-teal-400'
          }`}>
             <span className={`${theme === 'light' ? 'text-gray-500' : 'text-gray-300'}`}></span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onToggleTheme}
            className={`gap-2 backdrop-blur-sm transition-all ${
              theme === 'light'
                ? 'border-indigo-200 bg-white/50 hover:bg-indigo-50 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-200/50'
                : 'border-slate-600 bg-slate-800/50 hover:bg-slate-700/70 hover:border-blue-400/50 hover:shadow-lg hover:shadow-blue-500/30 text-gray-100'
            }`}
          >
            {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            切换主题
          </Button>
        </div>
      </div>
    </header>
  );
}
