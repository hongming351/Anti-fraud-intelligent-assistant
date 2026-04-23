#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断千问API响应"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def diagnose_qwen_api():
    """诊断千问API响应"""
    print("=" * 60)
    print("🔍 千问API响应诊断")
    print("=" * 60)
    
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    print(f"\n📝 配置信息:")
    print(f"  - API密钥: {api_key[:20] if api_key else '未设置'}...")
    print(f"  - 模型: {model}")
    
    try:
        import dashscope
        print(f"\n✓ dashscope版本: {dashscope.__version__ if hasattr(dashscope, '__version__') else '已安装'}")
        
        # 直接调用API测试
        print("\n【测试】 直接调用DashScope API...")
        
        from dashscope import Generation
        
        prompt = """请分析以下文本的诈骗风险，并返回JSON格式的结果：

文本内容: "您的账户异常，需要立即转账验证身份。"

请返回以下JSON格式，不要添加任何其他文字：
{
    "fraud_type": "诈骗类型",
    "risk_level": "高/中/低",
    "risk_score": 数字（0-100），
    "confidence": 数字（0-1），
    "reasons": ["原因1", "原因2"],
    "warning_keywords": ["关键词1", "关键词2"]
}
"""
        
        response = Generation.call(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位资深的反诈专家。请只返回有效的JSON，不要添加任何其他文字。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            api_key=api_key
        )
        
        print(f"\n✓ API调用成功")
        print(f"  - 状态码: {response.status_code}")
        
        # 获取文本内容
        if hasattr(response, 'output') and hasattr(response.output, 'text'):
            text_content = response.output.text
            print(f"\n📨 API返回的原始文本:")
            print("-" * 60)
            print(text_content)
            print("-" * 60)
            
            # 解析JSON
            print(f"\n【JSON 解析】")
            try:
                # 清理文本，移除可能的空格
                cleaned_text = text_content.strip()
                json_obj = json.loads(cleaned_text)
                print(f"✓ JSON 解析成功")
                print(f"\n解析后的对象:")
                print(json.dumps(json_obj, ensure_ascii=False, indent=2))
                
                # 检查每个字段
                print(f"\n【字段检查】")
                for key, value in json_obj.items():
                    # 如果是字符串，检查是否有多余的空格
                    if isinstance(value, str):
                        value_repr = repr(value)
                        has_space = value != value.strip()
                        space_warning = " ⚠️ (含空格)" if has_space else ""
                        print(f"  - {key}: {value_repr}{space_warning} (类型: {type(value).__name__}, 长度: {len(value)})")
                    else:
                        print(f"  - {key}: {repr(value)} (类型: {type(value).__name__})")
                    
            except json.JSONDecodeError as e:
                print(f"✗ JSON 解析失败: {e}")
                print(f"  位置: {e.pos}, 行: {e.lineno}, 列: {e.colno}")
                print(f"  错误内容: {text_content[max(0, e.pos-20):e.pos+20]}")
        else:
            print(f"✗ 无法获取响应文本内容")
            print(f"  响应对象: {response}")
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    diagnose_qwen_api()
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
