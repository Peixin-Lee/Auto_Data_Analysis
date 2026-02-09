#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek OCR API Server (vLLM) - 极简版
只返回 Markdown 内容
"""
import os
import io
import re
import argparse
from io import BytesIO
from typing import List

import torch
from PIL import Image

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor

# -----------------------
# FastAPI App
# -----------------------
app = FastAPI(title="DeepSeek OCR API (vLLM) - Simple", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# -----------------------
# 全局变量
# -----------------------
llm = None

# 固定 Prompt
PROMPT_OCR = "<image>\n<|grounding|>Convert the document to markdown."
PROMPT_DESC = "<image>\nDescribe this image in detail."

# -----------------------
# 模块级 Monkey Patch
# -----------------------
_original_tokenize = DeepseekOCRProcessor.tokenize_with_images

def _patched_tokenize(self, images, bos=True, eos=True, cropping=True, prompt=None):
    if prompt is not None:
        import config
        old = config.PROMPT
        config.PROMPT = prompt
        try:
            return _original_tokenize(self, images, bos, eos, cropping)
        finally:
            config.PROMPT = old
    return _original_tokenize(self, images, bos, eos, cropping)

DeepseekOCRProcessor.tokenize_with_images = _patched_tokenize

# -----------------------
# 工具函数
# -----------------------
def pdf_to_images(pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
    """PDF 转图片"""
    if fitz is None:
        raise RuntimeError("未安装 PyMuPDF,请执行: pip install PyMuPDF")
    
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    
    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")
        
        images.append(img)
    
    doc.close()
    return images


def clear_vllm_cache():
    """清理 vLLM 缓存"""
    if llm is None:
        return
    try:
        if hasattr(llm.llm_engine, 'input_preprocessor'):
            prep = llm.llm_engine.input_preprocessor
            if hasattr(prep, '_mm_processor_cache'):
                prep._mm_processor_cache.clear()
    except:
        pass


def vllm_generate(image: Image.Image, prompt: str) -> str:
    """vLLM 推理"""
    clear_vllm_cache()
    
    processor = DeepseekOCRProcessor()
    tokenized = processor.tokenize_with_images(images=[image], prompt=prompt)
    
    batch_inputs = [{
        "prompt": prompt,
        "multi_modal_data": {"image": tokenized}
    }]
    
    
    if prompt == PROMPT_OCR:
        logits_proc = [NoRepeatNGramLogitsProcessor(20, 50, {128821, 128822})]
        params = SamplingParams(
            temperature=0.0,
            max_tokens=4096,
            skip_special_tokens=False,
            logits_processors=logits_proc,
            repetition_penalty=1.05,
        )
    else:
        params = SamplingParams(
            temperature=0.0,
            max_tokens=512,
            skip_special_tokens=False,
        )
    
    outputs = llm.generate(batch_inputs, params)
    return outputs[0].outputs[0].text


def clean_markdown(text: str) -> str:
    """清理 Markdown (移除特殊标记)"""
    # 移除 <|ref|> <|det|> 等标记
    text = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', text)
    text = re.sub(r'<\|det\|>.*?<\|/det\|>', '', text)
    text = re.sub(r'<\|.*?\|>', '', text)
    text = re.sub(r'\[\[.*?\]\]', '', text)
    
    # 移除长分隔线
    text = re.sub(r'={50,}.*?={50,}', '', text, flags=re.DOTALL)
    
    # 规范化空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def generate_image_description(image: Image.Image) -> str:
    """生成图片描述"""
    try:
        result = vllm_generate(image, PROMPT_DESC)
        
        # 清理特殊标记
        desc = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', result)
        desc = re.sub(r'<\|det\|>.*?<\|/det\|>', '', desc)
        desc = re.sub(r'<\|.*?\|>', '', desc)
        desc = re.sub(r'\[\[.*?\]\]', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # 截断到200字符
        if len(desc) > 200:
            cutoff = desc[:200].rfind('.')
            if cutoff > 100:
                desc = desc[:cutoff + 1]
            else:
                desc = desc[:200].rsplit(' ', 1)[0] + '...'
        
        return desc
    except Exception as e:
        print(f"⚠️ 图片描述失败: {e}")
        return ""


# -----------------------
# 模型初始化
# -----------------------
def initialize_model(model_path: str, gpu_id: int = 0):
    global llm
    
    ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
    
    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    os.environ['VLLM_USE_V1'] = '0'
    
    print(f"🔄 加载模型: {model_path}")
    
    llm = LLM(
        model=model_path,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        block_size=256,
        enforce_eager=False,
        trust_remote_code=True,
        max_model_len=8192,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.9,
        max_num_seqs=100,
        disable_mm_preprocessor_cache=True,
    )
    
    print("✅ 模型加载完成")


# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    return {
        "service": "DeepSeek OCR (vLLM) - Simple",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "model_ready": llm is not None}


@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    enable_description: bool = Form(False),
):
    """
    OCR 接口 (图片或 PDF)
    
    参数:
        file: 图片文件 (jpg/png) 或 PDF 文件
        enable_description: 是否生成图片描述
    
    返回:
        {
            "markdown": "...",  # Markdown 内容
            "page_count": 1     # 页数
        }
    """
    if llm is None:
        raise HTTPException(503, "模型未加载")
    
    try:
        contents = await file.read()
        
        # 判断文件类型
        if file.filename.lower().endswith('.pdf'):
            images = pdf_to_images(contents)
        else:
            images = [Image.open(BytesIO(contents)).convert("RGB")]
        
        print(f"处理 {len(images)} 页...")
        
        # 处理每一页
        md_parts = []
        for idx, img in enumerate(images):
            print(f"   页 {idx + 1}/{len(images)}")
            
            # OCR
            raw = vllm_generate(img, PROMPT_OCR)
            
            # 如果启用图片描述,替换图片标记
            if enable_description:
                # 查找所有 <|ref|>image<|/ref|> 标记
                img_pattern = r'<\|ref\|>image<\|/ref\|><\|det\|>\[\[.*?\]\]<\|/det\|>'
                
                def replace_with_desc(match):
                    # 提取 bbox
                    det_match = re.search(r'\[\[(.*?)\]\]', match.group(0))
                    if det_match:
                        # 生成描述
                        desc = generate_image_description(img)
                        return f"[图片: {desc}]" if desc else "[图片]"
                    return "[图片]"
                
                raw = re.sub(img_pattern, replace_with_desc, raw)
            
            # 清理并添加
            cleaned = clean_markdown(raw)
            if cleaned:
                md_parts.append(cleaned)
        
        # 合并所有页
        final_md = "\n\n".join(md_parts)
        
        return JSONResponse({
            "markdown": final_md,
            "page_count": len(images)
        })
    
    except Exception as e:
        import traceback
        raise HTTPException(500, f"处理失败: {e}\n{traceback.format_exc()}")


# -----------------------
# 启动
# -----------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="模型路径")
    parser.add_argument("--gpu-id", type=int, default=0, help="GPU ID")
    parser.add_argument("--port", type=int, default=8707, help="端口")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    
    args = parser.parse_args()
    
    initialize_model(args.model_path, args.gpu_id)
    
    print(f"\n🚀 服务启动: http://{args.host}:{args.port}")
    print(f"📖 接口文档: http://{args.host}:{args.port}/docs\n")
    
    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()