import { useState } from 'react';
import { Header } from './components/Header';
import { DataVisualization } from './components/DataVisualization';
import { ChatAssistant } from './components/ChatAssistant';
import { ReportPreviewModal } from './components/ReportPreviewModal';

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [processedResults, setProcessedResults] = useState<any>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <div 
      className={`min-h-screen flex flex-col transition-all duration-500 relative overflow-hidden ${
        theme === 'light' 
          ? 'text-gray-800' 
          : 'text-gray-100'
      }`}
      style={{ fontFamily: "'HarmonyOS Sans', 'Noto Sans SC', sans-serif" }}
    >
      {/* 背景渐变层 */}
      <div className={`fixed inset-0 -z-10 transition-opacity duration-500 ${
        theme === 'light' 
          ? 'bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50' 
          : 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
      }`} />
      
      {/* 网格背景 */}
      <div 
        className="fixed inset-0 -z-10 opacity-20"
        style={{
          backgroundImage: theme === 'light'
            ? 'radial-gradient(circle at 1px 1px, rgb(99, 102, 241) 1px, transparent 0)'
            : 'radial-gradient(circle at 1px 1px, rgb(56, 189, 248) 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }}
      />
      
      {/* 浮动光晕 */}
      <div className={`fixed top-0 left-1/4 w-96 h-96 rounded-full blur-3xl -z-10 transition-opacity duration-500 ${
        theme === 'light'
          ? 'bg-blue-300/30'
          : 'bg-blue-500/10'
      }`} />
      <div className={`fixed bottom-0 right-1/4 w-96 h-96 rounded-full blur-3xl -z-10 transition-opacity duration-500 ${
        theme === 'light'
          ? 'bg-purple-300/30'
          : 'bg-cyan-500/10'
      }`} />
      <Header theme={theme} onToggleTheme={toggleTheme} />
      
      <main className="flex-1 flex overflow-hidden">
        <DataVisualization
          theme={theme}
          processedResults={processedResults}
          taskId={currentTaskId || undefined}
          onPreviewReport={() => {
            if (currentTaskId) {
              const apiUrl = `http://${window.location.hostname}:8708/report/${currentTaskId}`;
              window.open(apiUrl, '_blank');
            } else {
              setIsReportModalOpen(true);
            }
          }}
        />
        {/* 左右栏分隔线 */}
        <div className={`w-px transition-colors ${
          theme === 'light'
            ? 'bg-gradient-to-b from-indigo-200 via-purple-200 to-pink-200'
            : 'bg-gradient-to-b from-slate-700 via-slate-600 to-slate-700'
        }`} />
        <ChatAssistant
          theme={theme}
          onProcessingComplete={(results: any, taskId: string) => {
            setProcessedResults(results);
            setCurrentTaskId(taskId);
          }}
        />
      </main>

      <footer className={`py-4 text-center border-t backdrop-blur-xl transition-all ${
        theme === 'light' 
          ? 'border-white/20 bg-white/30' 
          : 'border-slate-700/50 bg-slate-900/60'
      }`}>
        <p className="text-sm opacity-70">
          © 2026 AI全自动数据分析系统 — 数据洞察，从提问开始
        </p>
      </footer>

      <ReportPreviewModal 
        isOpen={isReportModalOpen} 
        onClose={() => setIsReportModalOpen(false)}
        theme={theme}
      />
    </div>
  );
}
