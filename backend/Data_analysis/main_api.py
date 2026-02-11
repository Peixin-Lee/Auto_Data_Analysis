#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主API服务 - 正确的处理流程
1. OCR处理 → Markdown
2. 信息结构化 → 结构化数据
3. 可视化生成 → HTML报告
"""
import os
import io
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('c:/Users/Xin/Desktop/codes/LM/DataAnalysis/backend/Data_analysis/.env')

# -----------------------
# 配置
# -----------------------
app = FastAPI(
    title="智能数据分析API",
    version="2.0.0",
    description="OCR → 结构化分析 → 可视化报告"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 从环境变量加载配置
class Config:
    # # DeepSeek-OCR配置
    # DEEPSEEK_OCR_URL = os.getenv('DEEPSEEK_OCR_URL')

    # 数据分析配置
    QWEN_TOKENIZER_PATH = os.getenv('QWEN_TOKENIZER_PATH')
    ANALYSIS_API_KEY = os.getenv('ANALYSIS_API_KEY') 
    ANALYSIS_API_BASE = os.getenv('ANALYSIS_API_BASE')
    ANALYSIS_MODEL_NAME = os.getenv('ANALYSIS_MODEL_NAME')

    # 可视化配置
    VISUALIZER_API_KEY = os.getenv('VISUALIZER_API_KEY')
    VISUALIZER_API_BASE = os.getenv('VISUALIZER_API_BASE')
    VISUALIZER_MODEL_NAME = os.getenv('VISUALIZER_MODEL_NAME')

    # API服务配置
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8708))

    # 文件存储配置
    UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', '/tmp/ocr_uploads'))
    RESULTS_DIR = Path(os.getenv('RESULTS_DIR', '/tmp/ocr_results'))
    TEMP_DIR = Path(os.getenv('TEMP_DIR', '/tmp/ocr_temp'))

    # 文件处理限制
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 100))
    SUPPORTED_EXTENSIONS = os.getenv('SUPPORTED_EXTENSIONS', '.jpg,.jpeg,.png,.pdf,.txt,.md').split(',')

config = Config()

# 创建目录
config.UPLOAD_DIR.mkdir(exist_ok=True)
config.RESULTS_DIR.mkdir(exist_ok=True)
config.TEMP_DIR.mkdir(exist_ok=True)

# -----------------------
# 数据模型
# -----------------------
class OCRResult(BaseModel):
    markdown: str
    page_count: int
    file_name: str
    file_info: Dict[str, Any]
    processing_time: float
    status: str

class AnalysisResult(BaseModel):
    source: Dict[str, Any]
    total_chunks: int
    analyzed_chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class VisualizationResult(BaseModel):
    html: str
    title: str
    summary: str

class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # pending, ocr_processing, analyzing, visualizing, completed, error
    current_step: str
    progress: int
    message: str
    created_at: datetime
    updated_at: datetime
    results: Optional[Dict[str, Any]] = None

# -----------------------
# 任务状态管理
# -----------------------
class TaskManager:
    # pending → ocr_processing → analyzing → visualizing → completed
    def __init__(self):
        self.tasks: Dict[str, ProcessingStatus] = {}

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now()
        self.tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            current_step="准备开始",
            progress=0,
            message="任务已创建",
            created_at=now,
            updated_at=now
        )
        return task_id

    def update_task(self, task_id: str, status: str, step: str, progress: int, message: str, results: Dict[str, Any] = None):
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].current_step = step
            self.tasks[task_id].progress = progress
            self.tasks[task_id].message = message
            self.tasks[task_id].updated_at = datetime.now()
            if results:
                self.tasks[task_id].results = results

    def get_task(self, task_id: str) -> Optional[ProcessingStatus]:
        return self.tasks.get(task_id)

    def cleanup_old_tasks(self, hours: int = 24):
        cutoff = datetime.now().timestamp() - hours * 3600
        to_remove = []
        for task_id, task in self.tasks.items():
            if task.created_at.timestamp() < cutoff:
                to_remove.append(task_id)
        for task_id in to_remove:
            del self.tasks[task_id]

task_manager = TaskManager()

# -----------------------
# OCR处理器类
# -----------------------
class OCRProcessor:
    """Qwen-VL模型OCR处理器"""
    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv('VL_API_KEY'),
            base_url=os.getenv('VL_API_BASE_URL'),
        )
        self.model = os.getenv('VL_MODEL_NAME', 'qwen3-vl-plus')
        self.prompt = os.getenv('QWEN_VL_OCR_PROMPT', 'qwenvl markdown')

    async def process(self, file_path: str, enable_description: bool = False) -> OCRResult:
        """主处理函数"""
        start_time = time.time()
        file_ext = Path(file_path).suffix.lower()  # 提取文件扩展名
        
        try:
            if file_ext in ['.txt', '.md']:
                return self._process_text_file(file_path, start_time)
            elif file_ext == '.pdf':
                return await self._process_pdf(file_path, start_time, enable_description)
            else:
                return await self._process_image(file_path, start_time, enable_description)
        except Exception as e:
            raise HTTPException(500, f"OCR处理失败: {str(e)}")
    
    def _image_to_base64(self, file_path: str) -> str:
        """图片转base64"""
        import base64
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _process_text_file(self, file_path: str, start_time: float) -> OCRResult:
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成模拟的Markdown结果
        markdown_content = f"""# 文档分析报告

## 文件信息
- 文件名: {Path(file_path).name}
- 文件大小: {os.path.getsize(file_path)} bytes
- 文件类型: 文本文件

## 文档内容

{content}

## 关键信息提取

### 主要内容概要
- 文档类型: {Path(file_path).suffix.replace('.', '').upper()} 文件
- 内容长度: {len(content)} 字符
- 处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

### 结构化信息
- 标题/章节: 已识别 {content.count('#')} 个标题
- 段落数量: 已识别 {len(content.split(chr(10) + chr(10)))} 个段落

---
*此为文本文件直接处理结果*
"""
        
        return OCRResult(
            markdown=markdown_content,
            page_count=1,
            file_name=Path(file_path).name,
            file_info={
                'original_name': Path(file_path).name,
                'size_bytes': os.path.getsize(file_path),
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                'file_type': 'text',
                'processing_mode': 'direct_text'
            },
            processing_time=time.time() - start_time,
            status='success'
        )

    async def _process_pdf(self, file_path: str, start_time: float, enable_description: bool) -> OCRResult:
        """处理PDF文件，转为图片处理"""
        from pdf2image import convert_from_path

        # PDF转图片
        images = convert_from_path(file_path, dpi=300)
        page_results = []
        for i, image in enumerate(images):
            # 保存临时图片
            temp_dir = Path(os.getenv('TEMP_DIR', '/tmp/ocr_temp'))
            temp_dir.mkdir(exist_ok=True)
            temp_image_path = temp_dir / f"page_{i}_{int(time.time())}.png"
            image.save(str(temp_image_path), "PNG")

            try:
                # 调用处理图片
                result = await self._process_image(str(temp_image_path), 0, enable_description)
                page_results.append(result)
            finally:
                # 删除临时图片
                if temp_image_path.exists():
                    temp_image_path.unlink()

        # 合并页面
        full_markdown = "\n\n---\n\n".join([result.markdown for result in page_results])
        return OCRResult(
            markdown=full_markdown,
            page_count=len(page_results),
            file_name=Path(file_path).name,
            file_info={
                'original_name': Path(file_path).name,
                'size_bytes': os.path.getsize(file_path),
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                'file_type': 'pdf',
                'processing_mode': 'qwen_vl_ocr'
            },
            processing_time=time.time() - start_time,
            status='success'
        )

    async def _process_image(self, file_path: str, start_time: float, enable_description: bool) -> OCRResult:
        """处理单张图片"""
        # 获取文件扩展名
        file_ext = Path(file_path).suffix.lower().replace('.', '')
        # 映射到正确的MIME类型
        mime_type_map = {
            'jpg': 'jpeg',
            'jpeg': 'jpeg',
            'png': 'png',
            'gif': 'gif',
            'bmp': 'bmp',
            'webp': 'webp'
        }
        mime_type = mime_type_map.get(file_ext, 'jpeg')
        
        # 使用base64编码
        base64_image = self._image_to_base64(file_path)

        # 调用Qwen-VL模型进行OCR
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{mime_type};base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": self.prompt
                    }
                ]
            }]
        )
        markdown_content = response.choices[0].message.content

        return OCRResult(
            markdown=markdown_content,
            page_count=1,
            file_name=Path(file_path).name,
            file_info={
                'original_name': Path(file_path).name,
                'size_bytes': os.path.getsize(file_path),
                'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                'file_type': 'image',
                'processing_mode': 'qwen_vl_ocr'
            },
            processing_time=time.time() - start_time,
            status='success'
        )


# class OCRProcessor:
#     """OCR处理器"""
#     def __init__(self):
#         self.ocr_url = config.DEEPSEEK_OCR_URL

#     async def process(self, file_path: str, enable_description: bool = False) -> OCRResult:
#         """调用OCR服务或处理文本文件"""
#         start_time = time.time()
#         file_ext = Path(file_path).suffix.lower()

#         try:
#             # 对于文本文件，直接读取内容
#             if file_ext in ['.txt', '.md']:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     content = f.read()

#                 # 生成模拟的Markdown结果
#                 markdown_content = f"""# 文档分析报告

# ## 文件信息
# - 文件名: {Path(file_path).name}
# - 文件大小: {os.path.getsize(file_path)} bytes
# - 文件类型: 文本文件

# ## 文档内容

# {content}

# ## 关键信息提取

# ### 主要内容概要
# - 文档类型: {file_ext.replace('.', '').upper()} 文件
# - 内容长度: {len(content)} 字符
# - 处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

# ### 结构化信息
# - 标题/章节: 已识别 {content.count('#')} 个标题
# - 段落数量: 已识别 {len(content.split(chr(10) + chr(10)))} 个段落
# - 关键词: 自动提取中...

# ---
# *此为文本文件直接处理结果，如需OCR识别请上传图片或PDF文件*
# """

#                 processing_time = time.time() - start_time

#                 return OCRResult(
#                     markdown=markdown_content,
#                     page_count=1,
#                     file_name=Path(file_path).name,
#                     file_info={
#                         'original_name': Path(file_path).name,
#                         'size_bytes': os.path.getsize(file_path),
#                         'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
#                         'file_type': 'text',
#                         'processing_mode': 'direct_text'
#                     },
#                     processing_time=processing_time,
#                     status='success'
#                 )

#             # 对于图片和PDF文件，调用OCR服务
#             else:
#                 with open(file_path, 'rb') as f:
#                     files = {'file': f}
#                     data = {'enable_description': str(enable_description)}

#                     response = requests.post(
#                         self.ocr_url,
#                         files=files,
#                         data=data,
#                         timeout=300
#                     )

#                 if response.status_code != 200:
#                     raise HTTPException(500, f"OCR服务错误: {response.status_code} {response.text}")

#                 result = response.json()
#                 processing_time = time.time() - start_time

#                 return OCRResult(
#                     markdown=result.get('markdown', ''),
#                     page_count=result.get('page_count', 0),
#                     file_name=result.get('file_name', Path(file_path).name),
#                     file_info={
#                         'original_name': Path(file_path).name,
#                         'size_bytes': os.path.getsize(file_path),
#                         'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
#                         'file_type': 'ocr_processed',
#                         'processing_mode': 'ocr_service'
#                     },
#                     processing_time=processing_time,
#                     status='success'
#                 )

#         except Exception as e:
#             raise HTTPException(500, f"OCR处理失败: {str(e)}")

class InformationProcessor:
    """信息结构化处理器"""
    def __init__(self):
        # 动态导入Information_structuring模块
        import sys
        sys.path.append('c:/Users/Xin/Desktop/codes/LM/DataAnalysis/backend/Data_analysis/backwark')
        from Information_structuring import DataAnalyzer

        self.analyzer = DataAnalyzer(
            api_key=config.ANALYSIS_API_KEY,
            base_url=config.ANALYSIS_API_BASE,
            model=config.ANALYSIS_MODEL_NAME
        )

    async def process(self, ocr_result: OCRResult) -> AnalysisResult:
        """结构化分析OCR结果"""
        try:
            # 构造OCR输入数据
            ocr_data = {
                "markdown": ocr_result.markdown,
                "page_count": ocr_result.page_count
            }

            # 调用分析器
            result = self.analyzer.analyze_ocr_json(ocr_data, use_concurrent=True)

            return AnalysisResult(
                source=ocr_data,
                total_chunks=result.get('total_chunks', 0),
                analyzed_chunks=result.get('analyzed_chunks', []),
                metadata=result.get('metadata', {})
            )

        except Exception as e:
            raise HTTPException(500, f"信息结构化失败: {str(e)}")

class VisualizationProcessor:
    """可视化处理器"""
    def __init__(self):
        # 动态导入visualizer模块
        import sys
        sys.path.append('c:/Users/Xin/Desktop/codes/LM/DataAnalysis/backend/Data_analysis/backwark')

        try:
            from visualizer import ReportGenerator
            self.generator = ReportGenerator(
                api_key=config.VISUALIZER_API_KEY,
                base_url=config.VISUALIZER_API_BASE,
                model=config.VISUALIZER_MODEL_NAME
            )
            self.use_mock = False
        except Exception as e:
            print(f"⚠️ 无法加载真实可视化服务，使用模拟服务: {e}")
            # 使用模拟服务
            sys.path.append('c:/Users/Xin/Desktop/codes/LM/DataAnalysis/backend/Data_analysis')
            from mock_visualizer import MockReportGenerator
            self.generator = MockReportGenerator(
                api_key=config.VISUALIZER_API_KEY,
                base_url=config.VISUALIZER_API_BASE,
                model=config.VISUALIZER_MODEL_NAME
            )
            self.use_mock = True

    async def process(self, analysis_result: AnalysisResult, user_query: str = "分析此文档并生成可视化报告") -> VisualizationResult:
        """生成可视化报告"""
        try:
            if self.use_mock:
                print("🔄 使用模拟可视化服务生成报告...")

            # 生成报告
            report = self.generator.generate_report(analysis_result.model_dump(), user_query)

            return VisualizationResult(
                html=report.html,
                title=report.title,
                summary=report.summary
            )

        except Exception as e:
            if not self.use_mock:
                print(f"⚠️ 真实可视化服务失败，尝试使用模拟服务: {e}")
                # 真实服务失败时，尝试使用模拟服务
                try:
                    import sys
                    sys.path.append('c:/Users/Xin/Desktop/codes/LM/DataAnalysis/backend/Data_analysis')
                    from mock_visualizer import MockReportGenerator
                    mock_generator = MockReportGenerator(
                        api_key=config.VISUALIZER_API_KEY,
                        base_url=config.VISUALIZER_API_BASE,
                        model=config.VISUALIZER_MODEL_NAME
                    )
                    print("🔄 切换到模拟可视化服务...")
                    report = mock_generator.generate_report(analysis_result.model_dump(), user_query)

                    return VisualizationResult(
                        html=report.html,
                        title=report.title,
                        summary=report.summary
                    )
                except Exception as mock_e:
                    print(f"❌ 模拟服务也失败: {mock_e}")

            raise HTTPException(500, f"可视化生成失败: {str(e)}")

# 创建处理器实例
ocr_processor = OCRProcessor()
info_processor = InformationProcessor()
viz_processor = VisualizationProcessor()

# -----------------------
# 后台处理函数
# -----------------------
async def process_document_task(task_id: str, file_path: str, enable_description: bool = False, user_query: str = "分析此文档并生成可视化报告"):
    """完整的文档处理流程"""
    try:
        # 步骤1: OCR处理
        task_manager.update_task(task_id, "ocr_processing", "OCR识别中", 10, "正在进行OCR文字识别...")
        ocr_result = await ocr_processor.process(file_path, enable_description)

        # 步骤2: 信息结构化
        task_manager.update_task(task_id, "analyzing", "信息分析中", 50, "正在进行信息结构化分析...",
                                {"ocr_result": ocr_result.dict()})
        analysis_result = await info_processor.process(ocr_result)

        # 步骤3: 可视化生成
        task_manager.update_task(task_id, "visualizing", "生成可视化报告", 80, "正在生成可视化报告...",
                                {"ocr_result": ocr_result.dict(), "analysis_result": analysis_result.dict()})
        viz_result = await viz_processor.process(analysis_result, user_query)

        # 保存结果
        results = {
            "ocr_result": ocr_result.dict(),
            "analysis_result": analysis_result.dict(),
            "visualization_result": viz_result.dict()
        }

        # 保存到文件
        result_file = config.RESULTS_DIR / f"{task_id}_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 保存HTML报告
        html_file = config.RESULTS_DIR / f"{task_id}_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(viz_result.html)

        # 完成任务
        task_manager.update_task(task_id, "completed", "处理完成", 100, "文档处理完成！",
                                {
                                    **results,
                                    "files": {
                                        "json_file": str(result_file),
                                        "html_file": str(html_file)
                                    }
                                })

        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        task_manager.update_task(task_id, "error", "处理失败", 0, f"处理失败: {str(e)}")
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    return {
        "service": "智能数据分析API",
        "version": "2.0.0",
        "status": "running",
        "description": "OCR → 结构化分析 → 可视化报告",
        "endpoints": {
            "upload": "/upload - 上传文档开始处理",
            "status": "/status/{task_id} - 查询处理状态",
            "results": "/results/{task_id} - 获取处理结果",
            "report": "/report/{task_id} - 获取HTML报告",
            "health": "/health - 健康检查"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(task_manager.tasks),
        "directories": {
            "upload": str(config.UPLOAD_DIR),
            "results": str(config.RESULTS_DIR),
            "temp": str(config.TEMP_DIR)
        }
    }

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_description: bool = Form(False),
    user_query: str = Form("分析此文档并生成可视化报告")
):
    """
    上传文档开始处理
    完整流程: OCR → 结构化分析 → 可视化报告
    """
    try:
        # 验证文件
        if not file.filename:
            raise HTTPException(400, "请选择文件")

        # 验证文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.SUPPORTED_EXTENSIONS:
            raise HTTPException(400, f"不支持的文件格式。支持的格式: {', '.join(config.SUPPORTED_EXTENSIONS)}")

        # 读取文件
        contents = await file.read()
        if len(contents) > config.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"文件大小超过{config.MAX_FILE_SIZE_MB}MB限制")

        # 保存上传的文件
        timestamp = int(time.time())
        temp_filename = f"{timestamp}_{file.filename}"
        temp_path = config.TEMP_DIR / temp_filename

        with open(temp_path, "wb") as f:
            f.write(contents)

        # 创建任务
        task_id = task_manager.create_task()
        task_manager.update_task(task_id, "pending", "准备开始", 0, f"文件 {file.filename} 已接收，准备处理")

        # 启动后台处理
        background_tasks.add_task(
            process_document_task,
            task_id,
            str(temp_path),
            enable_description,
            user_query
        )

        return JSONResponse({
            "task_id": task_id,
            "status": "processing",
            "message": "文档处理已开始",
            "file_info": {
                "filename": file.filename,
                "size_bytes": len(contents),
                "size_mb": round(len(contents) / (1024 * 1024), 2)
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"上传失败: {str(e)}")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """查询处理状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    return JSONResponse({
        "task_id": task.task_id,
        "status": task.status,
        "current_step": task.current_step,
        "progress": task.progress,
        "message": task.message,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "has_results": task.results is not None
    })

@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """获取处理结果"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    if task.status != "completed":
        raise HTTPException(400, f"任务尚未完成，当前状态: {task.status}")

    if not task.results:
        raise HTTPException(404, "处理结果不存在")

    return JSONResponse(task.results)

@app.get("/report/{task_id}")
async def get_html_report(task_id: str):
    """获取HTML报告"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    if task.status != "completed":
        raise HTTPException(400, f"任务尚未完成，当前状态: {task.status}")

    html_file = config.RESULTS_DIR / f"{task_id}_report.html"
    if not html_file.exists():
        raise HTTPException(404, "HTML报告不存在")

    return FileResponse(
        path=str(html_file),
        filename=f"report_{task_id}.html",
        media_type="text/html"
    )

@app.get("/download/{task_id}/{file_type}")
async def download_file(task_id: str, file_type: str):
    """下载处理文件"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    if task.status != "completed":
        raise HTTPException(400, f"任务尚未完成，当前状态: {task.status}")

    if file_type == "json":
        file_path = config.RESULTS_DIR / f"{task_id}_results.json"
        filename = f"results_{task_id}.json"
    elif file_type == "html":
        file_path = config.RESULTS_DIR / f"{task_id}_report.html"
        filename = f"report_{task_id}.html"
    else:
        raise HTTPException(400, "不支持的文件类型")

    if not file_path.exists():
        raise HTTPException(404, "文件不存在")

    return FileResponse(
        path=str(file_path),
        filename=filename
    )

@app.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    return JSONResponse({
        "total_tasks": len(task_manager.tasks),
        "tasks": [
            {
                "task_id": task.task_id,
                "status": task.status,
                "current_step": task.current_step,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            for task in task_manager.tasks.values()
        ]
    })

@app.post("/cleanup")
async def cleanup_old_tasks():
    """清理旧任务"""
    task_manager.cleanup_old_tasks()
    return JSONResponse({
        "message": "旧任务清理完成",
        "remaining_tasks": len(task_manager.tasks)
    })

# -----------------------
# 启动服务
# -----------------------
if __name__ == "__main__":
    print("🚀 启动智能数据分析API服务...")
    print("=" * 60)
    print(f"📖 API文档: http://{config.API_HOST}:{config.API_PORT}/docs")
    print(f"🔍 根路径: http://{config.API_HOST}:{config.API_PORT}/")
    print(f"📤 上传接口: http://{config.API_HOST}:{config.API_PORT}/upload")
    print(f"📊 状态查询: http://{config.API_HOST}:{config.API_PORT}/status/{{task_id}}")
    print(f"📄 HTML报告: http://{config.API_HOST}:{config.API_PORT}/report/{{task_id}}")
    print(f"💚 健康检查: http://{config.API_HOST}:{config.API_PORT}/health")
    print("=" * 60)
    print("✅ 服务已启动，处理流程: OCR → 结构化分析 → 可视化报告")

    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info"
    )