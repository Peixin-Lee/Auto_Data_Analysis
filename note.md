# 文档处理流程说明

本文档记录了系统从文件上传到报告生成的完整处理流程。

## 处理架构

系统采用异步后台任务架构，文件上传后立即返回task_id，实际处理在后台进行。前端通过轮询 `/status/{task_id}` 获取实时进度。

## 完整流程

### 1. 文件上传 (同步)

**端点**: `POST /upload`

**操作**:
- 验证文件格式 (.jpg, .png, .pdf, .txt, .md)
- 检查文件大小 (最大100MB)
- 保存至临时目录
- 生成task_id
- 启动后台任务

**返回**: `{task_id, status: "processing", file_info}`

### 2. 后台处理 (异步)

#### 步骤1: OCR识别 (进度10%)

**处理器**: `OCRProcessor`

**流程**:
- PDF文件: 使用pdf2image转换为图片，逐页处理
- 图片文件: 直接处理
- 转换为base64编码
- 调用云端OCR API (SiliconFlow)
- 提取`<|ref|>`标签中的文本内容
- 组合为Markdown格式

**输出**:
```python
OCRResult(
    markdown: str,           # 识别的文本
    page_count: int,         # 页数
    file_name: str,          # 文件名
    file_info: dict,         # 元信息
    processing_time: float   # 耗时
)
```

#### 步骤2: 信息结构化 (进度50%)

**处理器**: `InformationProcessor`

**流程**:
- 加载 `Information_structuring.DataAnalyzer`
- 使用Qwen Tokenizer按标题层级智能切分
- 每块约1500 tokens，保留完整标题路径
- 并发调用LLM分析 (默认10并发)
- 使用LangChain + ChatOpenAI提取结构化数据
- 合并所有chunk的分析结果

**输出**:
```python
AnalysisResult(
    source: dict,                # OCR原始数据
    total_chunks: int,           # 总块数
    analyzed_chunks: list,       # 分析结果数组
    metadata: dict               # 元数据
)
```

**analyzed_chunks结构**:
```python
{
    "chunk_index": int,          # 序号
    "section": str,              # 所属章节
    "summary": str,              # 内容摘要
    "entities": list,            # 实体识别
    "data_points": list,         # 数据点
    "key_findings": list         # 关键发现
}
```

#### 步骤3: 可视化生成 (进度80%)

**处理器**: `VisualizationProcessor`

**流程**:
- 加载 `visualizer.ReportGenerator`
- 失败则降级使用 `mock_visualizer.MockReportGenerator`
- 调用LLM生成JSON数据结构
- 使用预设HTML模板渲染
- 集成ECharts图表库
- 生成响应式HTML报告

**输出**:
```python
VisualizationResult(
    html: str,       # 完整HTML内容
    title: str,      # 报告标题
    summary: str     # 分析摘要
)
```

#### 步骤4: 结果保存 (进度100%)

**操作**:
- 保存JSON: `{task_id}_results.json`
- 保存HTML: `{task_id}_report.html`
- 更新任务状态为completed
- 清理临时文件

### 3. 结果查询

**状态查询**: `GET /status/{task_id}`
```json
{
    "status": "completed",
    "current_step": "处理完成",
    "progress": 100,
    "message": "文档处理完成",
    "result": {...}
}
```

**完整结果**: `GET /results/{task_id}`
返回包含ocr_result、analysis_result、visualization_result的完整数据。

**报告预览**: `GET /report/{task_id}`
返回HTML报告页面。

**文件下载**: `GET /download/{task_id}/{file_type}`
支持下载json、html、markdown格式。

## 性能指标

- 小文件 (< 5页): 30-60秒
  - OCR: 10-20秒
  - 结构化: 10-20秒
  - 可视化: 10-20秒

- 大文件 (20+页): 2-5分钟
  - OCR: 每页5-10秒
  - 结构化: 根据chunks数量 (并发)
  - 可视化: 15-30秒

## 前端轮询机制

前端使用 `pollTaskUntilComplete()` 函数：
- 每2秒查询一次状态
- 实时更新进度条和状态消息
- 状态变为completed时停止轮询
- 调用 `/results/{task_id}` 获取完整数据
- 更新左侧可视化面板

## 错误处理

- OCR失败: 自动重试5次，间隔1秒
- 结构化失败: 返回错误信息，保留OCR结果
- 可视化失败: 降级使用模拟服务
- 任务超时: 状态标记为error，保留临时数据

## 技术栈

- OCR: SiliconFlow API (DeepSeek-OCR模型)
- 结构化: LangChain + ChatOpenAI (Qwen/GPT)
- 可视化: ECharts 5.4.3 + 自定义模板
- 异步: FastAPI BackgroundTasks
- 并发: ThreadPoolExecutor (10 workers)
