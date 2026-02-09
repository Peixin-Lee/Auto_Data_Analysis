#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简化的测试API服务器 - 仅用于前后端联调测试
不依赖任何第三方库，只使用标准库
"""
import os
import time
import json
from typing import Optional

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, Form
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请安装: pip install fastapi uvicorn python-multipart")
    exit(1)

# -----------------------
# FastAPI App
# -----------------------
app = FastAPI(title="Simple Test API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# 工具函数
# -----------------------
def generate_mock_ocr_result(filename: str, file_size: int) -> str:
    """生成模拟的OCR结果"""
    mock_content = f"""# 文档分析报告

## 文件信息
- 文件名: {filename}
- 文件大小: {file_size} bytes
- 处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 模拟OCR内容

### 第一章 概述
这是一个测试文档，用于验证OCR API的基本功能。

### 第二章 数据表格

| 项目 | 数值 | 单位 | 同比增长 |
|------|------|------|----------|
| 营业收入 | 1,234.56 | 万元 | +15.2% |
| 净利润 | 456.78 | 万元 | +8.7% |
| 总资产 | 5,678.90 | 万元 | +12.3% |
| 负债总额 | 2,345.67 | 万元 | -5.4% |

### 第三章 关键要点
- 📈 **业绩表现良好**: 营业收入同比增长15.2%，净利润增长8.7%
- 💰 **盈利能力提升**: 净利润率达到37.0%，较去年提升2.1个百分点
- 📊 **资产结构优化**: 总资产增长12.3%，负债增长控制在5.4%以内
- 🎯 **未来发展**: 预计下一年度将继续保持稳定增长态势

### 第四章 风险提示
1. 市场竞争加剧可能影响利润率
2. 原材料价格波动需要重点关注
3. 宏观经济环境变化带来的不确定性

---
*本报告由DeepSeek-OCR自动生成，仅供测试使用*
"""
    return mock_content

# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    return {
        "service": "Simple Test OCR API",
        "version": "1.0.0",
        "status": "running",
        "description": "最简化测试API用于前后端联调",
        "endpoints": {
            "health": "/health",
            "ocr": "/ocr",
            "test_upload": "/test/upload",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_ready": False,
        "mode": "test",
        "dependencies": {
            "fastapi": "✅",
            "uvicorn": "✅",
            "pillow": "❌ (安装中)",
            "torch": "❌ (安装中)",
            "vllm": "❌ (需要安装)"
        }
    }

@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    enable_description: bool = Form(False),
):
    """
    测试OCR接口

    参数:
        file: 上传的文件
        enable_description: 是否生成图片描述

    返回:
        {
            "markdown": "Markdown内容",
            "page_count": 1,
            "file_info": {...},
            "mock_mode": True
        }
    """
    try:
        # 读取文件内容
        contents = await file.read()
        file_size = len(contents)

        print(f"📄 接收到文件: {file.filename}")
        print(f"📏 文件大小: {file_size} bytes")
        print(f"📋 文件类型: {file.content_type}")
        print(f"🔧 启用描述: {enable_description}")

        # 检查文件大小限制 (50MB)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(400, "文件大小超过50MB限制")

        # 检查文件类型
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.txt', '.md']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                400,
                f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
            )

        # 生成模拟OCR结果
        mock_markdown = generate_mock_ocr_result(file.filename, file_size)

        # 模拟处理时间 (0.5-2秒)
        processing_time = 0.5 + (file_size / (10 * 1024 * 1024))  # 根据文件大小调整
        time.sleep(min(processing_time, 2.0))

        result = {
            "markdown": mock_markdown,
            "page_count": 1,
            "file_info": {
                "filename": file.filename,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "type": file_ext,
                "content_type": file.content_type
            },
            "processing_time": round(processing_time, 2),
            "enable_description": enable_description,
            "mock_mode": True,
            "status": "success"
        }

        print(f"✅ 文件处理完成: {file.filename} ({processing_time:.2f}s)")

        return JSONResponse(result)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"处理失败: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(500, error_msg)

@app.post("/test/upload")
async def test_upload(file: UploadFile = File(...)):
    """简单的文件上传测试接口"""
    try:
        contents = await file.read()
        return {
            "filename": file.filename,
            "size": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "content_type": file.content_type,
            "status": "success",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        raise HTTPException(500, f"上传失败: {str(e)}")

@app.get("/test/status")
async def test_status():
    """测试状态接口"""
    return {
        "server_status": "running",
        "uptime": "1 minute",
        "memory_usage": "low",
        "cpu_usage": "low",
        "ready_for_testing": True
    }

# -----------------------
# 启动
# -----------------------
if __name__ == "__main__":
    print("🚀 启动最简化测试API服务器...")
    print("=" * 50)
    print("📖 API文档: http://0.0.0.0:8707/docs")
    print("🔍 根路径: http://0.0.0.0:8707/")
    print("📝 OCR接口: http://0.0.0.0:8707/ocr")
    print("📤 测试上传: http://0.0.0.0:8707/test/upload")
    print("💚 健康检查: http://0.0.0.0:8707/health")
    print("=" * 50)
    print("✅ 服务器已启动，可以开始测试!")

    uvicorn.run(app, host="0.0.0.0", port=8707, log_level="info")