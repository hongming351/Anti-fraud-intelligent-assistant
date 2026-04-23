#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证 DashScope 响应格式"""

import os
import json
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()

api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL", "qwen-turbo")

print("=" * 60)
print("🔍 验证 DashScope 响应格式")
print("=" * 60)

response = Generation.call(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "你好，请简短回复"
        }
    ],
    api_key=api_key
)

print(f"\n【响应对象类型】")
print(f"  - response: {type(response)}")
print(f"  - response.output: {type(response.output)}")
print(f"  - response.output.text: {type(response.output.text)}")

print(f"\n【响应内容】")
print(f"  - status_code: {response.status_code}")
print(f"  - 文本内容: {response.output.text}")

print(f"\n【如何访问文本内容】")
print(f"  正确方式: response.output.text")
print(f"  访问结果: {response.output.text[:100]}...")

print(f"\n✅ 正确的响应访问方式已确认")
