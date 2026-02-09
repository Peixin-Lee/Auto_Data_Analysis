"""
simple_ocr_client.py - 测试客户端
"""
import json
import requests

def test_ocr(file_path: str, enable_desc: bool = False):
    """测试 OCR 接口"""
    url = "http://192.168.110.131:8707/ocr"
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"enable_description": "true" if enable_desc else "false"}
        
        print(f"📤 上传: {file_path}")
        resp = requests.post(url, files=files, data=data, timeout=300)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ 成功! 页数: {result['page_count']}")
        print(f"\n{'='*60}")
        # print(result['markdown'])
        print(f"{'='*60}\n")

        #添加文件名
        result['file_name'] = file_path.split('/')[-1]
        # 保存 JSON
        json_file = file_path.rsplit('.', 1)[0] + '.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"💾 已保存: {json_file}")
        
        # 保存 Markdown
        md_file = file_path.rsplit('.', 1)[0] + '.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(result['markdown'])
        print(f"💾 已保存: {md_file}")
    else:
        print(f"❌ 失败: {resp.status_code}")
        print(resp.text)


if __name__ == "__main__":
    # 测试图片
    # test_ocr("/home/data/nongwa/workspace/data/图片3.jpg", enable_desc=False)
    
    # 测试 PDF (带图片描述)
    test_ocr("/home/data/nongwa/workspace/data/10华夏收入混合型证券投资基金2024年年度报告.pdf", enable_desc=True)