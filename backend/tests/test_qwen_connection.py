#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试千问API连接"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径（父目录backend/）以支持导入app模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.llm_analyzer import LLMAnalyzer, PromptVersion
from app.core.llm_risk_judge import LLMRiskJudge

def test_qwen_api():
    """测试千问API连接"""
    print("=" * 60)
    print("🔗 千问API连接测试")
    print("=" * 60)
    
    # 获取API配置
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    print(f"\n✓ API密钥: {api_key[:10]}...")
    print(f"✓ 模型: {model}")
    
    if not api_key:
        print("\n❌ 错误：LLM_API_KEY 未设置")
        return False
    
    try:
        print("\n【测试1】 初始化LLMAnalyzer...")
        analyzer = LLMAnalyzer(api_key=api_key, model_name=model)
        print("✓ 初始化成功")
        
        print("\n【测试2】 测试基础分析...")
        test_text = "您的账户异常，需要立即转账验证身份。"
        result = analyzer.analyze_with_llm(
            user_content=test_text,
            prompt_version=PromptVersion.V2_EXAMPLES
        )
        
        if "error" not in result:
            print(f"✓ 分析成功")
            print(f"  - 风险等级: {result.get('risk_level', 'N/A')}")
            print(f"  - 诈骗类型: {result.get('fraud_type', 'N/A')}")
            print(f"  - 风险分数: {result.get('risk_score', 'N/A')}")
        else:
            print(f"⚠ 分析返回错误: {result.get('error')}")
        
        print("\n【测试3】 使用LLMRiskJudge进行完整判断...")
        judge = LLMRiskJudge(llm_analyzer=analyzer)
        judgment = judge.judge(test_text)
        
        print(f"✓ 判断完成")
        print(f"  - 风险等级: {judgment.risk_level.value}")
        print(f"  - 诈骗类型: {judgment.fraud_type}")
        print(f"  - 风险分数: {judgment.risk_score}")
        print(f"  - 置信度: {judgment.confidence}")
        print(f"  - 建议: {judgment.advice}")
        
        print("\n" + "=" * 60)
        print("✅ 千问API连接测试通过！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qwen_api()
    sys.exit(0 if success else 1)
