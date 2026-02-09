import { useState, useRef } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Upload, Send, ChevronDown, ChevronUp, FileText, Loader2, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// API服务配置 - 动态获取主机地址
const getAPIBaseURL = () => {
  // 如果在浏览器环境，使用当前主机名
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8708`;
  }
  return 'http://localhost:8708';
};
const API_BASE_URL = getAPIBaseURL();

// 移除emoji符号的函数
const removeEmojis = (text: string): string => {
  // 移除所有emoji字符，包括 ✅ ❌ 📊 等
  return text.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1F1E0}-\u{1F1FF}]/gu, '').trim();
};

// API调用函数
async function uploadDocument(file: File, userQuery: string = '分析此文档并生成可视化报告') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('enable_description', 'true');
  formData.append('user_query', userQuery);

  const response = await fetch(`${API_BASE_URL}/ocr`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`上传失败: ${response.statusText}`);
  }

  return await response.json();
}

async function getTaskStatus(taskId: string) {
  const response = await fetch(`${API_BASE_URL}/status/${taskId}`);

  if (!response.ok) {
    throw new Error(`获取状态失败: ${response.statusText}`);
  }

  return await response.json();
}

async function pollTaskUntilComplete(taskId: string, onUpdate: (status: any) => void) {
  while (true) {
    const status = await getTaskStatus(taskId);
    onUpdate(status);

    if (status.status === 'completed') {
      return status;
    }

    if (status.status === 'error') {
      throw new Error(status.message);
    }

    // 等待2秒后再次查询
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

interface ChatAssistantProps {
  theme: 'light' | 'dark';
  onProcessingComplete?: (results: any, taskId: string) => void;
}

interface ChatMessage {
  type: 'user' | 'assistant' | 'status';
  content: string;
  progress?: number;
  step?: string;
  completed?: boolean;
}

// 初始消息为空，等待用户上传文件
const initialMessages: ChatMessage[] = [];

export function ChatAssistant({ theme, onProcessingComplete }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isParseOpen, setIsParseOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTask, setCurrentTask] = useState<any>(null);
  const [processedResults, setProcessedResults] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const cardClass = theme === 'light' 
    ? 'bg-white/60 border-white/40 backdrop-blur-xl shadow-xl shadow-indigo-500/10' 
    : 'bg-slate-800/80 border-slate-700/50 backdrop-blur-xl shadow-xl shadow-blue-500/10';

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    if (!currentTask || !currentTask.task_id) {
      setMessages([...messages,
        { type: 'user', content: inputValue },
        { type: 'assistant', content: '请先上传文档，等待处理完成后再提问。' }
      ]);
      setInputValue('');
      return;
    }

    const userQuestion = inputValue;
    setMessages([...messages,
      { type: 'user', content: userQuestion },
      { type: 'assistant', content: '收到您的问题，正在分析数据并生成可视化报告...' }
    ]);
    setInputValue('');

    try {
      // 调用分析接口
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: currentTask.task_id,
          user_query: userQuestion
        })
      });

      if (!response.ok) {
        throw new Error(`分析失败: ${response.statusText}`);
      }

      const result = await response.json();

      // 添加分析结果消息
      const resultMessage: ChatMessage = {
        type: 'assistant',
        content: `分析完成！\n\n${result.summary}\n\n可视化报告已在左侧显示，您可以继续提问进行更深入的分析。`
      };
      setMessages(prev => [...prev, resultMessage]);

      // 通知父组件渲染左侧可视化报告
      if (onProcessingComplete) {
        onProcessingComplete({
          visualization_result: {
            html: result.html,
            title: result.title,
            summary: result.summary,
            answer_id: result.answer_id,
            report_url: result.report_url
          },
          user_query: userQuestion
        }, currentTask.task_id);
      }

    } catch (error) {
      console.error('分析失败:', error);
      const errorMessage: ChatMessage = {
        type: 'assistant',
        content: `分析失败: ${error instanceof Error ? error.message : '未知错误'}`
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file.name);
      setIsParseOpen(true);
      await processDocument(file);
    }
  };

  const processDocument = async (file: File) => {
    setIsProcessing(true);
    setCurrentTask(null);
    setProcessedResults(null);

    // 添加处理开始消息
    const startMessage: ChatMessage = {
      type: 'status',
      content: `开始处理文档 "${file.name}"`,
      progress: 0,
      step: 'OCR识别'
    };
    setMessages(prev => [...prev, startMessage]);

    try {
      // 上传文档
      const uploadResult = await uploadDocument(file);
      const taskId = uploadResult.task_id;

      // 轮询任务状态
      await pollTaskUntilComplete(taskId, (status) => {
        setCurrentTask(status);

        // 更新进度消息
        const progressMessage: ChatMessage = {
          type: 'status',
          content: status.message,
          progress: status.progress,
          step: status.current_step
        };

        setMessages(prev => {
          const newMessages = [...prev];
          // 替换最后的状态消息
          if (newMessages.length > 0 && newMessages[newMessages.length - 1].type === 'status') {
            newMessages[newMessages.length - 1] = progressMessage;
          } else {
            newMessages.push(progressMessage);
          }
          return newMessages;
        });
      });

      // 获取处理结果
      const resultsResponse = await fetch(`${API_BASE_URL}/results/${taskId}`);
      const results = await resultsResponse.json();
      setProcessedResults(results);

      // 通知父组件
      if (onProcessingComplete) {
        onProcessingComplete(results, taskId);
      }

      // 完成消息 - 更新最后的status消息为completed状态
      setMessages(prev => {
        const newMessages = [...prev];
        // 将最后的status消息标记为完成
        if (newMessages.length > 0 && newMessages[newMessages.length - 1].type === 'status') {
          newMessages[newMessages.length - 1] = {
            type: 'status',
            content: '文档已解析完成，可以开始提问了',
            progress: 100,
            step: '解析完成',
            completed: true
          };
        }
        // 添加助手消息
        newMessages.push({
          type: 'assistant',
          content: `文档解析完成！已完成以下处理：\n\n- OCR文字识别\n- 数据结构化提取\n- 内容分析整理\n\n现在您可以在下方输入问题，我将基于文档内容进行深度分析并生成可视化报告。`
        });
        return newMessages;
      });

    } catch (error) {
      console.error('文档处理失败:', error);
      const errorMessage: ChatMessage = {
        type: 'assistant',
        content: `处理失败: ${error instanceof Error ? error.message : '未知错误'}\n\n请检查文档格式是否正确，或重新上传文档。`
      };
      setMessages(prev => {
        // 移除最后的status消息
        const filtered = prev.filter((msg, idx) => !(idx === prev.length - 1 && msg.type === 'status'));
        return [...filtered, errorMessage];
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const previewReport = () => {
    if (currentTask && currentTask.task_id) {
      window.open(`${API_BASE_URL}/report/${currentTask.task_id}`, '_blank');
    }
  };

  return (
    <div className="w-[30%] p-6">
      <div className="h-full flex flex-col">
        <h2 className={`tracking-tight mb-6 bg-gradient-to-r bg-clip-text text-transparent ${
          theme === 'light'
            ? 'from-indigo-600 to-purple-600'
            : 'from-blue-400 to-cyan-400'
        }`}>
          智能分析助理
        </h2>

        <div className="flex-1 overflow-y-auto space-y-4 mb-6">
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={message.type === 'status' ? 'w-full' : `flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.type === 'status' ? (
                // 专业的处理状态卡片
                <div className={`w-full p-4 rounded-xl backdrop-blur-xl border transition-all ${
                  message.completed
                    ? theme === 'light'
                      ? 'bg-gradient-to-br from-green-50/80 to-emerald-50/80 border-green-200/50 shadow-md'
                      : 'bg-gradient-to-br from-green-900/30 to-emerald-900/30 border-green-700/50 shadow-lg shadow-green-500/10'
                    : theme === 'light'
                      ? 'bg-gradient-to-br from-indigo-50/80 to-purple-50/80 border-indigo-200/50 shadow-md'
                      : 'bg-gradient-to-br from-slate-800/80 to-slate-700/80 border-slate-600/50 shadow-lg shadow-blue-500/10'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 rounded-full p-2 ${
                      message.completed
                        ? theme === 'light'
                          ? 'bg-green-100'
                          : 'bg-green-800/50'
                        : theme === 'light'
                          ? 'bg-indigo-100'
                          : 'bg-slate-600'
                    }`}>
                      {message.completed ? (
                        <CheckCircle2 className={`w-4 h-4 ${
                          theme === 'light' ? 'text-green-600' : 'text-green-400'
                        }`} />
                      ) : (
                        <Loader2 className={`w-4 h-4 animate-spin ${
                          theme === 'light' ? 'text-indigo-600' : 'text-blue-400'
                        }`} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-sm font-medium ${
                          message.completed
                            ? theme === 'light' ? 'text-green-800' : 'text-green-300'
                            : theme === 'light' ? 'text-gray-800' : 'text-gray-100'
                        }`}>
                          {message.step || '处理中'}
                        </span>
                        {message.progress !== undefined && (
                          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                            message.completed
                              ? theme === 'light'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-green-800/50 text-green-300'
                              : theme === 'light'
                                ? 'bg-indigo-100 text-indigo-700'
                                : 'bg-slate-600 text-blue-300'
                          }`}>
                            {message.progress}%
                          </span>
                        )}
                      </div>
                      {message.progress !== undefined && (
                        <div className={`h-1.5 rounded-full overflow-hidden mb-2 ${
                          message.completed
                            ? theme === 'light' ? 'bg-green-100' : 'bg-green-900/30'
                            : theme === 'light' ? 'bg-indigo-100' : 'bg-slate-600'
                        }`}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${message.progress}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            className={`h-full rounded-full ${
                              message.completed
                                ? theme === 'light'
                                  ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                                  : 'bg-gradient-to-r from-green-500 to-emerald-400'
                                : theme === 'light'
                                  ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                                  : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                            }`}
                          />
                        </div>
                      )}
                      <p className={`text-xs ${
                        message.completed
                          ? theme === 'light' ? 'text-green-700' : 'text-green-400'
                          : theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                      }`}>
                        {message.content}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                // 原有的用户和助手消息样式
                <div
                  className={`max-w-[80%] p-4 rounded-2xl backdrop-blur-xl shadow-lg ${
                    message.type === 'user'
                      ? theme === 'light'
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-indigo-500/30'
                        : 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-blue-500/40'
                      : theme === 'light'
                        ? 'bg-white/80 text-gray-800 border border-white/40 shadow-gray-200/50'
                        : 'bg-slate-700/90 text-gray-100 border border-slate-600/50 shadow-slate-900/50'
                  }`}
                >
                  <div className="text-sm leading-relaxed prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {removeEmojis(message.content)}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="space-y-4">
          <Card className={`p-4 ${cardClass}`}>
            <Collapsible open={isParseOpen} onOpenChange={setIsParseOpen}>
              <CollapsibleTrigger asChild>
                <button className="w-full flex items-center justify-between hover:opacity-80 transition-opacity">
                  <div className="flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    <span className="text-sm">
                      {uploadedFile ? `已上传: ${uploadedFile}` : '📂 上传PDF文档（点击查看解析结果）'}
                    </span>
                  </div>
                  {isParseOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-4">
                {isProcessing ? (
                  <div className={`p-4 rounded-lg text-sm backdrop-blur-sm ${
                    theme === 'light' ? 'bg-indigo-50/50 border border-indigo-100' : 'bg-slate-700/50 border border-slate-600/50 text-gray-100'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="opacity-80">正在处理文档...</span>
                    </div>
                    {currentTask && (
                      <div className="space-y-1 opacity-70">
                        <p>• 当前步骤: {currentTask.current_step}</p>
                        <p>• 进度: {currentTask.progress}%</p>
                        <p>• 状态: {currentTask.message}</p>
                      </div>
                    )}
                  </div>
                ) : processedResults ? (
                  <div className={`p-4 rounded-lg text-sm backdrop-blur-sm ${
                    theme === 'light' ? 'bg-green-50/50 border border-green-100' : 'bg-green-900/20 border border-green-700/50 text-gray-100'
                  }`}>
                    <p className={`opacity-80 mb-2 font-medium ${theme === 'light' ? 'text-green-700' : 'text-green-400'}`}>文档解析完成</p>
                    <div className="space-y-2 opacity-70">
                      <p>• OCR识别: 已完成</p>
                      <p>• 结构化分析: 已完成</p>
                      <p>• 内容提取: 已完成</p>
                      <div className="mt-3 pt-3 border-t border-green-200/30">
                        <Button
                          onClick={previewReport}
                          size="sm"
                          className={`gap-2 text-xs ${
                            theme === 'light'
                              ? 'bg-green-600 hover:bg-green-700 text-white'
                              : 'bg-green-700 hover:bg-green-600 text-white'
                          }`}
                        >
                          <FileText className="w-3 h-3" />
                          查看解析内容
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`p-4 rounded-lg text-sm backdrop-blur-sm ${
                    theme === 'light' ? 'bg-indigo-50/50 border border-indigo-100' : 'bg-slate-700/50 border border-slate-600/50 text-gray-100'
                  }`}>
                    <p className="opacity-80 mb-2">文档解析结果：</p>
                    <div className="space-y-2 opacity-70">
                      <p>• 文档标题：2024年度销售数据报告</p>
                      <p>• 页数：12页</p>
                      <p>• 关键词：销售趋势、用户增长、产品分析</p>
                      <p>• 摘要：本报告详细分析了2024年上半年的销售数据...</p>
                    </div>
                  </div>
                )}
              </CollapsibleContent>
            </Collapsible>
            
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
              ref={fileInputRef}
              disabled={isProcessing}
            />
            {!uploadedFile && (
              <label
                htmlFor="file-upload"
                className={`mt-3 block text-center py-2 px-4 rounded-lg cursor-pointer transition-all text-sm backdrop-blur-sm ${
                  isProcessing
                    ? 'opacity-50 cursor-not-allowed'
                    : theme === 'light'
                      ? 'bg-indigo-50/50 hover:bg-indigo-100/80 border border-indigo-100'
                      : 'bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600/50 text-gray-200'
                }`}
              >
                {isProcessing ? '处理中...' : '选择文件上传 (PDF/图片/文本)'}
              </label>
            )}
            {uploadedFile && (
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setUploadedFile(null);
                    setProcessedResults(null);
                    setCurrentTask(null);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                  disabled={isProcessing}
                  className={`text-xs ${
                    theme === 'light'
                      ? 'border-red-200 text-red-600 hover:bg-red-50'
                      : 'border-red-700 text-red-400 hover:bg-red-900/20'
                  }`}
                >
                  重新上传
                </Button>
                {processedResults && (
                  <Button
                    size="sm"
                    onClick={previewReport}
                    className={`text-xs gap-1 ${
                      theme === 'light'
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : 'bg-green-700 hover:bg-green-600 text-white'
                    }`}
                  >
                    <FileText className="w-3 h-3" />
                    查看内容
                  </Button>
                )}
              </div>
            )}
          </Card>

          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="请输入你的问题..."
              className={`flex-1 backdrop-blur-xl ${
                theme === 'light'
                  ? 'bg-white/80 border-indigo-200 focus:border-indigo-400 focus:ring-indigo-400'
                  : 'bg-slate-800/70 border-slate-600 focus:border-blue-400 focus:ring-blue-400 text-gray-100 placeholder:text-gray-400'
              }`}
            />
            <Button
              onClick={handleSend}
              className={`gap-2 text-white border-0 shadow-lg transition-all hover:scale-105 ${
                theme === 'light'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60'
                  : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/60'
              }`}
            >
              <Send className="w-4 h-4" />
              发送
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
