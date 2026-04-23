#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""详细调试JSON解析问题"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.llm_analyzer import LLMAnalyzer, PromptVersion

def debug_json_parsing():
    """调试JSON解析"""
    print("=" * 60)
    print("🐛 JSON解析调试")
    print("=" * 60)
    
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    print(f"\n配置: {model}")
    
    analyzer = LLMAnalyzer(api_key=api_key, model_name=model)
    
    # 直接调用API获取原始响应
    print("\n【步骤1】调用API...")
    prompt = analyzer.prompt_templates[PromptVersion.V2_EXAMPLES]
    test_text = "您的账户异常，需要立即转账验证身份。"
    message_content = prompt.format(
        user_content=test_text,
        similar_cases=analyzer._format_similar_cases(None)
    )
    
    print(f"发送的prompt：")
    print(f"  长度: {len(message_content)}")
    
    # 获取原始响应
    raw_response = analyzer._call_llm_api(message_content)
    
    print(f"\n【步骤2】原始响应:")
    print(f"  类型: {type(raw_response)}")
    print(f"  长度: {len(raw_response)}")
    print(f"\n完整内容:")
    print("-" * 60)
    print(raw_response)
    print("-" * 60)
    
    # 尝试提取JSON
    print(f"\n【步骤3】JSON提取:")
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if json_match:
        json_str = json_match.group()
        print(f"✓ 找到JSON")
        print(f"  长度: {len(json_str)}")
        print(f"\nJSON内容:")
        print("-" * 60)
        print(json_str)
        print("-" * 60)
        
        # 尝试解析JSON
        print(f"\n【步骤4】JSON解析:")
        try:
            data = json.loads(json_str)
            print(f"✓ 解析成功!")
            print(f"  字段: {list(data.keys())}")
            print(f"\n解析后的数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except json.JSONDecodeError as e:
            print(f"✗ 解析失败: {e}")
            print(f"  错误位置: {e.pos}")
            print(f"  错误行列: {e.lineno}:{e.colno}")
            print(f"\n尝试显示错误附近的文本:")
            start = max(0, e.pos - 50)
            end = min(len(json_str), e.pos + 50)
            print(f"  ...{json_str[start:end]}...")
    else:
        print(f"✗ 未找到JSON")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_json_parsing()
