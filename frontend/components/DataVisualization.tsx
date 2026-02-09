import { Card } from './ui/card';
import { Button } from './ui/button';
import { FileText, Download, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';

interface DataVisualizationProps {
  theme: 'light' | 'dark';
  onPreviewReport: () => void;
  processedResults?: any;
  taskId?: string;
}

// API配置 - 动态获取主机地址
const getAPIBaseURL = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8708`;
  }
  return 'http://localhost:8708';
};
const API_BASE_URL = getAPIBaseURL();

export function DataVisualization({ theme, onPreviewReport, processedResults, taskId }: DataVisualizationProps) {
  const cardClass = theme === 'light'
    ? 'bg-white/60 border-white/40 shadow-xl shadow-indigo-500/10 hover:shadow-2xl hover:shadow-indigo-500/20 backdrop-blur-xl'
    : 'bg-slate-800/80 border-slate-700/50 shadow-xl shadow-blue-500/10 hover:shadow-2xl hover:shadow-blue-500/20 backdrop-blur-xl';

  // 如果有处理结果，显示可视化报告
  if (processedResults && processedResults.visualization_result) {
    const { html, title, summary, report_url, answer_id } = processedResults.visualization_result;

    const handleExportPDF = async () => {
      if (!taskId || !answer_id) {
        alert('无法导出 PDF：缺少必要的参数');
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/export_pdf`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            task_id: taskId,
            answer_id: answer_id,
            title: title || '数据分析报告',
            regenerate: false  // 可以改为 true 以生成更精美的报告
          })
        });

        if (!response.ok) {
          throw new Error(`导出失败: ${response.statusText}`);
        }

        const result = await response.json();

        // 触发下载
        const downloadUrl = `${API_BASE_URL}${result.pdf_url}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        alert('PDF 报告已开始下载！');
      } catch (error) {
        console.error('导出 PDF 失败:', error);
        alert(`导出 PDF 失败: ${error instanceof Error ? error.message : '未知错误'}`);
      }
    };

    const handleViewFullReport = () => {
      if (report_url) {
        window.open(`${API_BASE_URL}${report_url}`, '_blank');
      }
    };

    return (
      <div className="w-[70%] flex flex-col">
        {/* 顶部操作栏 */}
        <div className={`p-4 border-b backdrop-blur-xl ${
          theme === 'light'
            ? 'bg-white/60 border-white/40'
            : 'bg-slate-800/80 border-slate-700/50'
        }`}>
          <div className="flex items-center justify-between">
            <h2 className={`text-lg font-semibold bg-gradient-to-r bg-clip-text text-transparent ${
              theme === 'light'
                ? 'from-indigo-600 to-purple-600'
                : 'from-blue-400 to-cyan-400'
            }`}>
              {title || '数据分析可视化报告'}
            </h2>
            <div className="flex gap-2">
              <Button
                onClick={handleViewFullReport}
                size="sm"
                variant="outline"
                className={`gap-2 ${
                  theme === 'light'
                    ? 'border-indigo-200 hover:bg-indigo-50'
                    : 'border-slate-600 hover:bg-slate-700 text-gray-300'
                }`}
              >
                <FileText className="w-4 h-4" />
                全屏查看
              </Button>
              <Button
                onClick={handleExportPDF}
                size="sm"
                variant="outline"
                className={`gap-2 ${
                  theme === 'light'
                    ? 'border-indigo-200 hover:bg-indigo-50'
                    : 'border-slate-600 hover:bg-slate-700 text-gray-300'
                }`}
              >
                <Download className="w-4 h-4" />
                导出PDF
              </Button>
            </div>
          </div>
        </div>

        {/* HTML报告渲染区域 */}
        <div className="flex-1 overflow-auto">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full h-full min-h-[800px]"
          >
            <iframe
              srcDoc={html}
              className="w-full h-full border-0"
              title="可视化报告"
              sandbox="allow-scripts allow-same-origin"
              style={{
                minHeight: '800px',
                width: '100%',
                backgroundColor: 'transparent'
              }}
            />
          </motion.div>
        </div>
      </div>
    );
  }

  // 空状态显示 - 等待用户上传文档
  return (
    <div className="w-[70%] p-6 overflow-y-auto flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
          theme === 'light'
            ? 'from-indigo-600 to-purple-600'
            : 'from-blue-400 to-cyan-400'
        }`}>
          数据分析可视化结果
        </h2>
      </div>

      {/* 空状态提示 */}
      <div className="flex-1 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-lg"
        >
          <Card className={`p-12 transition-all relative overflow-hidden ${cardClass}`}>
            <div className={`absolute inset-0 opacity-50 transition-opacity duration-500 ${
              theme === 'light'
                ? 'bg-gradient-to-br from-indigo-500/5 to-purple-500/5'
                : 'bg-gradient-to-br from-blue-500/5 to-cyan-500/5'
            }`} />

            <div className="relative z-10 text-center space-y-6">
              <div className={`w-24 h-24 mx-auto rounded-full flex items-center justify-center ${
                theme === 'light'
                  ? 'bg-indigo-100'
                  : 'bg-slate-700'
              }`}>
                <BarChart3 className={`w-12 h-12 ${
                  theme === 'light' ? 'text-indigo-600' : 'text-blue-400'
                }`} />
              </div>

              <div>
                <h3 className={`text-xl font-semibold mb-2 ${
                  theme === 'light' ? 'text-gray-800' : 'text-gray-100'
                }`}>
                  等待文档上传
                </h3>
                <p className={`text-sm ${
                  theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                }`}>
                  请在右侧上传PDF、图片或文本文件
                </p>
                <p className={`text-sm mt-2 ${
                  theme === 'light' ? 'text-gray-500' : 'text-gray-500'
                }`}>
                  系统将自动进行OCR识别、数据分析和可视化报告生成
                </p>
              </div>

              <div className={`pt-6 border-t ${
                theme === 'light' ? 'border-gray-200' : 'border-slate-600'
              }`}>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className={`text-2xl font-bold ${
                      theme === 'light' ? 'text-indigo-600' : 'text-blue-400'
                    }`}>1</div>
                    <div className={`text-xs mt-1 ${
                      theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                    }`}>OCR识别</div>
                  </div>
                  <div>
                    <div className={`text-2xl font-bold ${
                      theme === 'light' ? 'text-purple-600' : 'text-cyan-400'
                    }`}>2</div>
                    <div className={`text-xs mt-1 ${
                      theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                    }`}>数据分析</div>
                  </div>
                  <div>
                    <div className={`text-2xl font-bold ${
                      theme === 'light' ? 'text-pink-600' : 'text-teal-400'
                    }`}>3</div>
                    <div className={`text-xs mt-1 ${
                      theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                    }`}>生成报告</div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
