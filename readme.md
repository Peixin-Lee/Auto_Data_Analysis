# AI文档分析与可视化系统

## 项目简介

这是一个基于大语言模型的智能文档分析系统，能够自动处理PDF文档或图片，提取关键信息并生成交互式数据分析报告。系统采用前后端分离架构，集成了DeepSeek-OCR识别、智能文本分析和数据可视化等功能模块。通过云端API调用，大大降低了本地部署的硬件要求。

## 核心功能

### 1. 云端OCR文档解析
- 支持PDF文档和图片格式的文本提取
- **新升级**：集成DeepSeek-OCR云端API，无需本地GPU资源
- 自动将识别结果转换为结构化的Markdown格式
- 支持多页PDF自动分页处理

### 2. 智能信息提取
- 基于文档标题结构的智能文本切分
- 利用LangChain框架进行并发分析
- 支持多种大语言模型（Qwen、GPT等）
- 保留完整的层级结构和上下文信息

### 3. 可视化报告生成
- **架构重构**：采用"Template + Structured JSON"模式
- 自动生成交互式HTML数据分析报告
- 支持KPI指标卡、折线图、柱状图、饼图等多种组件
- 响应式深色霓虹主题设计

### 4. 实时对话助手
- 基于分析结果的智能问答
- 支持上下文追问
- 流式响应，提升用户体验

## 技术栈

### 前端技术
- React 18.2 + TypeScript 5.3
- Vite 5.1 构建工具
- Tailwind CSS 3.4 + Radix UI
- Recharts 2.12 数据可视化库
- React Hook Form + Zod 表单验证

### 后端技术
- Python 3.10+
- FastAPI 0.119 RESTful API框架
- LangChain 大语言模型集成
- Pydantic 2.x 数据验证

### AI/ML技术
- **DeepSeek-OCR API**：文档识别（兼容OpenAI格式）
- Qwen3-Max / GPT-4：文本分析与结构化
- 模板化生成引擎：数据可视化渲染

## 系统架构

```
┌──────────────────────────────────────┐
│  前端层 (React + TypeScript)          │
│  - 文件上传与管理                      │
│  - 实时数据可视化                      │
│  - AI对话交互                         │
└────────────┬─────────────────────────┘
             │ RESTful API
┌────────────▼─────────────────────────┐
│  API层 (FastAPI)                     │
│  - 文件处理                           │
│  - 任务调度                           │
│  - 状态管理                           │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  处理层                               │
│  ┌────────────┐  ┌─────────────┐    │
│  │ OCR云端API  │→│ 信息结构化   │    │
│  │ (DeepSeek) │  │ (LangChain) │    │
│  └────────────┘  └──────┬──────┘    │
│                          │            │
│                  ┌───────▼────────┐  │
│                  │  可视化生成     │  │
│                  │  (HTML模板)    │  │
│                  └────────────────┘  │
└──────────────────────────────────────┘
```

## 快速开始

### 环境要求
- Node.js 18+ 和 npm/pnpm
- Python 3.10+
- 任意普通PC（无需高性能GPU）

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd DataAnalysis
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置以下参数：
# - DEEPSEEK_OCR_BASE_URL: OCR服务地址（如 https://api.siliconflow.cn/v1/chat/completions）
# - DEEPSEEK_OCR_API_KEY: OCR服务密钥
# - ANALYSIS_API_KEY: 分析用大模型API密钥
# - ANALYSIS_API_BASE: 分析用API基础URL
```

3. 安装依赖

前端：
```bash
cd frontend
npm install
```

后端：
```bash
cd backend/Data_analysis
pip install -r requirements.txt
```

### 启动服务

按以下顺序启动各个服务：

```bash
# 1. 启动主API服务（终端1）
cd backend/Data_analysis
python main_api.py

# 2. 启动前端开发服务器（终端2）
cd frontend
npm run dev
```

访问 `http://localhost:5173` 即可使用系统。

## 项目结构

```
DataAnalysis/
├── frontend/                    # 前端项目
│   ├── components/             
│   │   ├── ui/                 # UI组件库
│   │   ├── api.ts              # API客户端
│   │   ├── DataVisualization.tsx        # 数据可视化组件
│   │   └── ChatAssistant.tsx            # AI对话助手
│   ├── App.tsx                 # 应用主组件
│   └── vite.config.ts          # Vite配置
│
├── backend/
│   └── Data_analysis/
│       ├── main_api.py                    # API服务入口（含OCR云端调用）
│       ├── test_ocr_api.py               # OCR API测试脚本
│       ├── backwark/                     # 核心处理模块
│       │   ├── Information_structuring.py # 信息结构化分析
│       │   ├── visualizer.py             # HTML报告生成
│       │   └── pdf_exporter.py           # PDF导出
│       └── DeepSeek-OCR-vllm/           # (已废弃) 本地OCR处理模块
│
└── .env                        # 环境变量配置
```

## 开发说明

### 前端开发

```bash
cd frontend

# 启动开发服务器
npm run dev

# 生产构建
npm run build

# 代码检查
npm run lint
```

### 后端开发

```bash
cd backend/Data_analysis

# 启动API服务
python main_api.py

# 验证OCR配置
python test_ocr_api.py
```

### API接口

主要API端点：

- `POST /upload` - 上传各种格式文档并自动开始处理
- `GET /status/{task_id}` - 查询全流程处理状态
- `GET /results/{task_id}` - 获取JSON分析结果
- `GET /report/{task_id}` - 获取HTML可视化报告
- `GET /health` - 服务健康检查

## 技术亮点

### 1. 轻量化OCR解决方案
从本地重型GPU部署迁移至云端API：
- 兼容OpenAI格式接口
- 支持DeepSeek-OCR、硅基流动等多种后端
- 自动处理PDF转图和分页识别

### 2. 模板化可视化引擎
重构了报告生成逻辑：
- LLM仅负责生成结构化JSON数据
- 使用预设的高质量HTML模板渲染
- 解决了生成HTML不稳定、样式缺失的问题

### 3. 智能文档切分策略
实现了基于标题层级的智能文本切分算法，能够：
- 保留完整的文档结构和上下文信息
- 自动识别和处理多级标题
- 动态调整chunk大小

### 4. 高并发LLM分析
采用多线程并发处理机制：
- 默认10并发workers
- 使用线程池管理，提高处理效率

## 性能指标

- OCR处理速度：取决于云端API响应速度（通常3-5秒/页）
- 文本分析：支持10并发处理

## 部署建议

### 生产环境部署

前端：
```bash
npm run build
# 将dist目录部署到Nginx或其他静态服务器
```

后端：
```bash
gunicorn main_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:18707 \
  --timeout 300
```

### Docker部署

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/Data_analysis /app
# 安装OCR依赖库
RUN apt-get update && apt-get install -y poppler-utils
RUN pip install -r requirements.txt
EXPOSE 18707
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "18707"]
```

## 注意事项

1. PDF处理需要系统安装 `poppler-utils`
2. 即使没有GPU也可以完整运行所有功能
3. OCR API需要配置正确的BASE_URL和API_KEY

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请通过issue或email联系。

### 核心改动
**前端文件**：`frontend/components/ChatAssistant.tsx`、`frontend/components/api.ts`、`frontend/components/DataVisualization.tsx`

**端点调整**：
- 上传端点：`/ocr` 改为 `/upload`（匹配main_api.py）
- 删除 `/analyze` 调用（main_api.py在上传时已自动完成OCR+结构化+可视化全流程）
- 任务列表：`/results` 改为 `/tasks`
- 文件下载：`/download/{filename}` 改为 `/download/{task_id}/{file_type}`

**功能调整**：
- 禁用PDF导出功能（后端未实现`/export_pdf`端点，改为提示使用浏览器打印）
- 删除`callRealOCR()`中的`/ocr/real`调用，统一使用`/upload`端点
- 简化用户提问逻辑，提示文档已完成分析

### 架构说明
main_api.py采用一次性处理架构：
- 文件上传后自动执行：OCR识别 → 信息结构化 → 可视化生成
- 前端通过轮询 `/status/{task_id}` 获取实时进度
- 处理完成后通过 `/results/{task_id}` 获取完整结果
- 不需要额外的 `/analyze` 端点进行二次分析

### 废弃说明
- `DeepSeek-OCR-vllm/backend_integration_api.py` 已不再使用
- 本地OCR服务已迁移至云端API，相关本地部署文件仅供参考

---

## 2026-02-12 - OCR处理迁移至云端API

### 更新背景
因本地部署DeepSeek-OCR需要GPU资源，受硬件限制，迁移至云端API调用（支持硅基流动等兼容OpenAI格式的服务）。

### 核心改动
**文件**：`backend/Data_analysis/main_api.py`

- 移除本地OCR服务调用（multipart/form-data），改为云端API（JSON + base64编码）
- 添加`_image_to_base64()`和`_call_api()`方法，支持5次自动重试
- API响应处理：使用正则提取`<|ref|>标签`中的文本，忽略`<|det|>坐标`信息
- PDF处理：转图片后逐页调用API

### 环境变量配置
```env
DEEPSEEK_OCR_BASE_URL=https://api.siliconflow.cn/v1/chat/completions
DEEPSEEK_OCR_API_KEY=sk-xxxxx
DEEPSEEK_OCR_MODEL_NAME=deepseek-ai/DeepSeek-OCR
```

### 测试验证
- 新增测试脚本：`test_ocr_api.py`、`test_text_extraction.py`
- 测试通过：API调用成功，文本提取正确，向后兼容

---

## 2026-02-11 - 可视化报告生成器重构

### 更新背景
原可视化报告质量差，Prompt过于复杂（4000+ tokens），LLM生成HTML不稳定。采用"模板化 + 结构化数据"架构，职责分离。

### 核心改动
**文件**：`backend/Data_analysis/backwark/visualizer.py`

**架构调整**：
- 旧方案：LLM直接生成完整HTML（10KB+）
- 新方案：LLM仅输出JSON数据（2KB以内），HTML由预设模板渲染

**新增功能**：
- KPI指标卡片（0-6个）、多类型图表（折线/柱状/饼图等）
- 响应式布局、交互动效、一键导出HTML

**Prompt优化**：
- 从4000+ tokens缩减至500 tokens
- 只要求JSON输出，明确提取策略，严禁编造数据

### 技术细节
- 依赖：ECharts 5.4.3、LangChain Core、Pydantic 2.x
- UI风格：深色渐变 + 玻璃拟物 + 电光蓝主色调
- 向后兼容：API签名和返回格式不变
