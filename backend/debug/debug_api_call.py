#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试API调用问题"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 API调用调试")
print("=" * 60)

# 检查环境变量
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL", "qwen3.5-plus")

print(f"\n【环境变量】")
print(f"  API密钥: {api_key[:30] if api_key else '未设置'}...")
print(f"  模型: {model}")
print(f"  API密钥内容长度: {len(api_key) if api_key else 0}")

# 直接测试DashScope
print(f"\n【直接调用DashScope兼容模式】")
try:
    import openai
    print(f"  ✓ OpenAI SDK已安装")
    
    # 使用兼容模式
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    print(f"  ✓ 客户端已配置")
    
    # 调用API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "你好，请简短回复"
            }
        ]
    )
    
    print(f"  ✓ API调用成功！")
    print(f"  响应: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"  ✗ 错误: {e}")
    import traceback
    traceback.print_exc()
