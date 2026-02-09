# AGENTS.md

> **AI全自动数据分析系统** - 基于LLM的智能文档分析与可视化平台

---

## 📋 项目概述

### 核心功能
1. **OCR文档解析** - DeepSeek-OCR处理PDF/图片 → Markdown
2. **智能信息提取** - 基于标题的智能切片 + LLM并发分析
3. **可视化报告生成** - 自动生成交互式HTML数据分析报告

### 技术架构
```
┌─────────────────────────────────────────────────────────┐
│  前端层 (React + TypeScript + Vite)                      │
│  - 文件上传与预览                                         │
│  - 实时数据可视化 (Recharts)                             │
│  - AI对话助手                                            │
└──────────────────┬──────────────────────────────────────┘
                   │ RESTful API
┌──────────────────▼──────────────────────────────────────┐
│  API层 (FastAPI)                                        │
│  - 文件上传处理                                          │
│  - 任务状态管理                                          │
│  - 结果查询与导出                                        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  处理层 (Python)                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ OCR处理         │  │ 信息结构化       │              │
│  │ (CUDA加速)      │→│ (LangChain)     │              │
│  └─────────────────┘  └────────┬────────┘              │
│                                 │                        │
│                       ┌─────────▼────────┐              │
│                       │ 可视化生成        │              │
│                       │ (HTML报告)       │              │
│                       └──────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 技术栈
**前端**
- React 18.2 + TypeScript 5.3
- Vite 5.1 (构建工具)
- Tailwind CSS 3.4 + Radix UI (UI框架)
- Recharts 2.12 (数据可视化)
- React Hook Form + Zod (表单验证)

**后端**
- Python 3.10+
- FastAPI 0.119 (API框架)
- LangChain + Transformers (LLM集成)
- Pydantic 2.x (数据验证)
- CUDA 12.x (GPU加速)

**AI/ML**
- DeepSeek-OCR (vLLM后端)
- Qwen3-Max / GPT-4 (文本分析)
- Flash-Attention 2.7 (推理加速)

---

## 🚀 快速开始

### 前置要求
- Node.js 18+ 和 npm/pnpm
- Python 3.10+
- CUDA 12.x (可选，用于OCR加速)
- 至少 16GB RAM

### 环境配置

**1. 克隆项目**
```bash
git clone <repository-url>
cd DataAnalysis
```

**2. 配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置以下关键项：
# - DEEPSEEK_OCR_URL: OCR服务地址
# - ANALYSIS_API_KEY: LLM API密钥
# - ANALYSIS_API_BASE: LLM API基础URL
# - ANALYSIS_MODEL_NAME: 使用的模型名称
```

**3. 安装依赖**

前端：
```bash
cd frontend
npm install
```

后端：
```bash
cd backend/Data_analysis
pip install -r requirements.txt

# 如需OCR功能，额外安装：
cd DeepSeek-OCR-vllm
pip install -r requirements.txt
```

---

## 💻 开发命令

### 前端开发

```bash
cd frontend

# 启动开发服务器 (端口: 5173)
npm run dev

# 类型检查 + 生产构建
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

### 后端开发

```bash
cd backend/Data_analysis

# 启动主API服务 (端口: 18707)
python main_api.py

# 或使用 uvicorn (推荐开发模式)
uvicorn main_api:app --reload --host 0.0.0.0 --port 18707
```

**OCR服务 (可选)**
```bash
cd backend/Data_analysis/DeepSeek-OCR-vllm

# 启动OCR API服务 (端口: 8707)
python test_api_server.py

# 测试OCR客户端
python simple_test_server.py
```

### 完整启动流程

⚠️ **按以下顺序启动服务**：

```bash
# 1. 启动OCR服务 (终端1)
cd backend/Data_analysis/DeepSeek-OCR-vllm
python test_api_server.py

# 2. 启动主API服务 (终端2)  
cd backend/Data_analysis
python main_api.py

# 3. 启动前端开发服务器 (终端3)
cd frontend
npm run dev
```

访问 `http://localhost:5173` 即可使用系统

---

## 📁 项目结构

```
DataAnalysis/
├── frontend/                    # 前端项目
│   ├── components/             
│   │   ├── ui/                 # Radix UI组件封装
│   │   ├── api.ts              # API客户端
│   │   ├── advanced_api.ts     # 高级API功能
│   │   ├── DataVisualization.tsx        # 数据可视化主组件
│   │   ├── DataVisualizationUpdated.tsx # 可视化增强版
│   │   └── ChatAssistant.tsx            # AI对话助手
│   ├── styles/
│   │   └── globals.css         # 全局样式 + Tailwind配置
│   ├── App.tsx                 # 根组件
│   ├── main.tsx               # 入口文件
│   ├── package.json           # 依赖与脚本
│   └── vite.config.ts         # Vite配置
│
├── backend/
│   └── Data_analysis/
│       ├── main_api.py                    # ⭐ 主API服务入口
│       ├── mock_visualizer.py             # 可视化Mock测试
│       │
│       ├── backwark/                     # 核心处理模块
│       │   ├── Information_structuring.py # ⭐ 信息结构化分析
│       │   ├── visualizer.py             # ⭐ HTML报告生成
│       │   ├── pdf_exporter.py           # PDF导出
│       │   └── analyzed_result.json      # 分析结果缓存
│       │
│       └── DeepSeek-OCR-vllm/           # OCR处理模块
│           ├── deepseek_ocr.py          # OCR核心逻辑
│           ├── backend_integration_api.py # 后端集成接口
│           ├── test_api_server.py       # OCR API服务器
│           ├── config.py                # OCR配置
│           └── requirements.txt         # OCR依赖
│
├── .env                        # ⚠️ 环境变量 (不提交)
└── readme.md                   # 项目说明
```

### 核心模块说明

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| **Frontend/UI** | 用户界面、文件上传、结果展示 | `App.tsx`, `DataVisualization.tsx` |
| **API层** | 请求路由、状态管理、错误处理 | `main_api.py` |
| **OCR处理** | 文档解析、图片识别 | `deepseek_ocr.py`, `test_api_server.py` |
| **信息结构化** | Markdown切分、LLM并发分析 | `Information_structuring.py` |
| **可视化生成** | HTML报告、图表生成 | `visualizer.py` |

---

## 📐 代码规范

### 命名约定

**Python后端**
```python
# 文件名：snake_case
# information_structuring.py ✅
# InformationStructuring.py ❌

# 类名：PascalCase
class ChunkAnalysis:          # ✅
class chunk_analysis:         # ❌

# 函数/变量：snake_case
def split_markdown_text():    # ✅
def splitMarkdownText():      # ❌

# 常量：UPPER_SNAKE_CASE
CHUNK_SIZE = 1500            # ✅
chunkSize = 1500             # ❌

# 环境变量前缀
ANALYSIS_API_KEY             # 分析相关
DEEPSEEK_OCR_URL            # OCR相关
```

**TypeScript前端**
```typescript
// 文件名：PascalCase (组件), camelCase (工具)
DataVisualization.tsx        // ✅
api.ts                      // ✅

// 组件名：PascalCase
export function ChatAssistant() { }  // ✅
export function chatAssistant() { }  // ❌

// 函数/变量：camelCase
const fetchAnalysisResult = async () => { }  // ✅
const FetchAnalysisResult = async () => { }  // ❌

// 类型/接口：PascalCase
interface AnalysisResult { }  // ✅
interface analysisResult { }  // ❌

// 常量：UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 10485760;  // ✅
```

### 代码风格

**Python**
- 使用 **4空格缩进**（不使用Tab）
- 遵循 PEP 8 规范
- 类型提示：`from typing import List, Dict, Any`
- 文档字符串：使用 `"""docstring"""`

```python
def analyze_chunk(chunk: str, llm: ChatOpenAI) -> ChunkAnalysis:
    """
    分析单个文本块
    
    Args:
        chunk: 待分析的文本
        llm: LLM实例
        
    Returns:
        ChunkAnalysis: 分析结果
    """
    # 实现...
```

**TypeScript**
- 使用 **2空格缩进**
- 使用分号结尾
- 优先使用 `const` / `let`，避免 `var`
- 接口优先于类型别名（除非需要Union/Intersection）

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

const handleUpload = async (file: File): Promise<ApiResponse<string>> => {
  // 实现...
};
```

### 项目特有规范

⚠️ **关键约定** - 与其他项目不同的地方

1. **API端点命名**
   ```python
   # 使用下划线分隔，不使用连字符
   @app.post("/upload_pdf")            # ✅
   @app.post("/upload-pdf")            # ❌
   ```

2. **LLM配置管理**
   - 所有LLM配置必须通过环境变量
   - 不允许硬编码API密钥
   ```python
   # ✅ 正确
   API_KEY = os.getenv("ANALYSIS_API_KEY")
   
   # ❌ 错误
   API_KEY = "sk-xxxxxx"
   ```

3. **Markdown切分策略**
   - **必须**保留完整标题层级路径
   - 使用`Header_1`, `Header_2`而非`h1`, `h2`
   ```python
   metadata["Header_1"] = "第一章"    # ✅
   metadata["h1"] = "第一章"         # ❌
   ```

4. **并发处理**
   - 默认并发数：`MAX_WORKERS = 10`
   - 修改需同步更新 `.env` 文件
   ```python
   MAX_WORKERS = int(os.getenv("ANALYSIS_MAX_WORKERS", "10"))
   ```

5. **前端状态管理**
   - 使用React Hooks，不使用Redux/Zustand
   - 异步状态使用 `useState` + `useEffect`
   ```typescript
   const [isLoading, setIsLoading] = useState(false);
   const [result, setResult] = useState<AnalysisResult | null>(null);
   ```

6. **错误处理模式**
   ```python
   # 后端统一返回格式
   return JSONResponse({
       "success": False,
       "error": "错误描述",
       "code": "ERROR_CODE"
   })
   ```

---

## 🧪 测试策略

### 后端测试

**测试框架**: `pytest`

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_information_structuring.py

# 生成覆盖率报告
pytest --cov=backend --cov-report=html tests/
```

**测试文件结构**
```
backend/Data_analysis/
├── tests/
│   ├── test_main_api.py              # API端点测试
│   ├── test_information_structuring.py  # 结构化逻辑测试
│   └── test_visualizer.py            # 可视化生成测试
```

**测试用例示例**
```python
# tests/test_information_structuring.py
import pytest
from backwark.Information_structuring import TitleBasedMarkdownSplitter

def test_markdown_split():
    """测试Markdown切分功能"""
    splitter = TitleBasedMarkdownSplitter(chunk_size=1500)
    markdown = "# Title 1\nContent..."
    
    chunks = splitter.split_text(markdown)
    
    assert len(chunks) > 0
    assert chunks[0].metadata["Header_1"] == "Title 1"
```

### 前端测试

**测试框架**: 建议使用 `Vitest` + `React Testing Library`

```bash
# 安装测试依赖
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom

# 运行测试
npm run test

# 覆盖率报告
npm run test:coverage
```

**OCR集成测试**
```bash
cd backend/Data_analysis/DeepSeek-OCR-vllm

# 测试OCR客户端
python test_simple_ocr_client.py

# 测试单张图片OCR
python run_dpsk_ocr_image.py --image path/to/image.jpg

# 测试PDF批量OCR
python run_dpsk_ocr_pdf.py --pdf path/to/document.pdf
```

### 覆盖率要求

- **核心模块** (Information_structuring, visualizer): **≥80%**
- **API端点**: **≥70%**
- **UI组件**: **≥60%**

---

## 🔧 常见任务

### 添加新的LLM模型

1. 在 `.env` 中配置模型：
   ```env
   ANALYSIS_MODEL_NAME=gpt-5
   ANALYSIS_API_BASE=https://api.example.com/v1
   ANALYSIS_API_KEY=sk-xxxxxx
   ```

2. 更新 `Information_structuring.py`：
   ```python
   MODEL_NAME = os.getenv("ANALYSIS_MODEL_NAME", "qwen3-max")
   
   llm = ChatOpenAI(
       model=MODEL_NAME,
       api_key=API_KEY,
       base_url=API_BASE
   )
   ```

### 修改Chunk大小

编辑 `.env`：
```env
# 单位：tokens
ANALYSIS_CHUNK_SIZE=2000  # 默认1500
```

### 自定义HTML报告样式

编辑 `backwark/visualizer.py` 中的 Prompt模板：
```python
html_generation_prompt = PromptTemplate(
    template="""
    你是一个数据可视化专家，根据以下数据生成HTML报告。
    
    样式要求:
    - 使用现代化的卡片布局
    - 颜色主题: #2563eb (蓝色)
    - 响应式设计
    ...
    """
)
```

### 部署到生产环境

**前端构建**
```bash
cd frontend
npm run build
# 产物在 frontend/dist/
```

**后端部署 (使用 Gunicorn)**
```bash
cd backend/Data_analysis

# 安装 Gunicorn
pip install gunicorn

# 启动服务 (4个worker进程)
gunicorn main_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:18707 \
  --timeout 300
```

**使用 Docker 部署**
```dockerfile
# Dockerfile示例
FROM python:3.10-slim

WORKDIR /app
COPY backend/Data_analysis /app
RUN pip install -r requirements.txt

EXPOSE 18707
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "18707"]
```

---

## 🐛 调试技巧

### 启用详细日志

**后端**
```python
# main_api.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**前端**
```typescript
// 在 api.ts 中添加
console.log('Request:', method, url, data);
console.log('Response:', response);
```

### 常见问题排查

**OCR服务连接失败**
```bash
# 检查OCR服务是否运行
curl http://192.168.110.131:8707/health

# 检查环境变量
echo $DEEPSEEK_OCR_URL
```

**LLM API超时**
- 增加超时时间：`timeout=300`
- 检查网络连接和API密钥
- 降低并发数：`MAX_WORKERS=5`

**Chunk切分异常**
- 检查Tokenizer路径：`QWEN_TOKENIZER_PATH`
- 确认Markdown格式正确（标题层级完整）

---

## 📚 关键依赖版本

### 后端核心依赖
```
fastapi==0.119.1
langchain-core>=0.3.0
langchain-openai>=0.2.0
transformers>=4.40.0
pydantic>=2.0.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
```

### 前端核心依赖
```json
"react": "^18.2.0",
"typescript": "^5.3.3",
"vite": "^5.1.0",
"tailwindcss": "^3.4.1",
"recharts": "^2.12.0"
```
