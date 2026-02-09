#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的测试API服务器 - 用于前后端联调测试
不依赖DeepSeek模型，提供基本的文件接收和处理功能
"""
import os
import io
import time
from typing import List
from PIL import Image

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# -----------------------
# FastAPI App
# -----------------------
app = FastAPI(title="Test OCR API", version="1.0.0")
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
def get_image_info(image_bytes: bytes) -> dict:
    """获取图片基本信息"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format,
            "size_bytes": len(image_bytes)
        }
    except Exception as e:
        return {"error": str(e)}

def generate_mock_ocr_result(filename: str, image_info: dict) -> str:
    """生成模拟的OCR结果"""
    mock_content = f"""# 文档分析报告

## 文件信息
- 文件名: {filename}
- 图片尺寸: {image_info.get('width', 'N/A')} x {image_info.get('height', 'N/A')} pixels
- 文件大小: {image_info.get('size_bytes', 0)} bytes

## 模拟OCR内容

### 第一章 概述
这是一个测试文档，用于验证OCR API的基本功能。

### 第二章 数据表格

| 项目 | 数值 | 单位 |
|------|------|------|
| 测试项目A | 100.5 | 万元 |
| 测试项目B | 200.3 | 万元 |
| 测试项目C | 150.8 | 万元 |

### 第三章 关键要点
- 这是一个模拟的OCR结果
- 实际使用时会调用DeepSeek-OCR模型
- 支持图片和PDF文件处理
- 输出标准的Markdown格式

---
*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return mock_content

# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    return {
        "service": "Test OCR API",
        "version": "1.0.0",
        "status": "running",
        "description": "简化版OCR API用于前后端联调测试"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model_ready": False, "mode": "test"}

@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    enable_description: bool = Form(False),
):
    """
    测试OCR接口

    参数:
        file: 图片文件 (jpg/png) 或 PDF 文件
        enable_description: 是否生成图片描述

    返回:
        {
            "markdown": "...",  # Markdown 内容
            "page_count": 1,     # 页数
            "file_info": {...}   # 文件信息
        }
    """
    try:
        # 读取文件内容
        contents = await file.read()
        file_size = len(contents)

        print(f"📄 接收到文件: {file.filename}, 大小: {file_size} bytes")

        # 检查文件类型
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            raise HTTPException(400, "不支持的文件格式。请上传 jpg, png, 或 pdf 文件。")

        # 获取图片信息
        if file.filename.lower().endswith('.pdf'):
            image_info = {"error": "PDF文件处理需要PyMuPDF库", "size_bytes": file_size}
        else:
            image_info = get_image_info(contents)

        # 生成模拟OCR结果
        mock_markdown = generate_mock_ocr_result(file.filename, image_info)

        # 模拟处理时间
        time.sleep(1)  # 模拟1秒处理时间

        result = {
            "markdown": mock_markdown,
            "page_count": 1,
            "file_info": {
                "filename": file.filename,
                "size_bytes": file_size,
                "type": "image" if file.filename.lower().endswith(('.jpg', '.jpeg', '.png')) else "pdf"
            },
            "image_info": image_info,
            "processing_time": 1.0,
            "mock_mode": True  # 标识这是模拟结果
        }

        print(f"✅ 文件处理完成: {file.filename}")

        return JSONResponse(result)

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
            "content_type": file.content_type,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(500, f"上传失败: {str(e)}")

# -----------------------
# 启动
# -----------------------
if __name__ == "__main__":
    print("🚀 启动测试OCR API服务器...")
    print("📖 接口文档: http://0.0.0.0:8707/docs")
    print("🔍 测试接口: http://0.0.0.0:8707/")
    print("📝 OCR接口: http://0.0.0.0:8707/ocr")

    uvicorn.run(app, host="0.0.0.0", port=8707, workers=1)