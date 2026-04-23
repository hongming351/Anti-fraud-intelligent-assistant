"""
LLM反诈分析演示脚本
展示大模型集成的各种功能和用法
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.llm_analyzer import LLMAnalyzer, PromptVersion
from app.core.llm_risk_judge import LLMRiskJudge, RiskJudgmentLevel


def demo_basic_analysis():
    """演示基础分析功能"""
    print("\n" + "="*60)
    print("演示1: 基础分析功能")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    # 示例1: 高风险 - 冒充公检法诈骗
    text1 = """
    你好，我是市公安局的。我们发现你的银行卡涉嫌洗钱，
    需要立即停用。请把你的存款转到安全账户进行冻结，
    完成后会立即解冻。需要你提供银行卡号和验证码。
    """
    
    print("\n示例1: 高风险内容")
    print("-" * 40)
    print("输入文本:", text1.strip()[:100] + "...")
    
    try:
        result = analyzer.analyze_with_llm(
            user_content=text1,
            prompt_version=PromptVersion.V1_BASIC
        )
    except Exception as e:
        print(f"调用接口发生异常: {e}")
        return
    
    print("分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_examples_prompt():
    """演示带少样本学习的提示词"""
    print("\n" + "="*60)
    print("演示2: 少样本学习提示词（推荐）")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    texts = [
        # 高风险
        "亲爱的用户，我们检测到您的账户有异常登录。请立即点击以下链接验证身份：http://verify.com。需要输入验证码。",
        # 中风险
        "嗨，今天有个投资机会，朋友圈一个群的人都参与了，月收益10%，要不要加入？",
        # 低风险
        "你好，这是平台客服，有什么我可以帮助你的吗？"
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\n示例{i}:")
        print("-" * 40)
        print("文本:", text[:60] + "...")
        
        result = analyzer.analyze_with_llm(
            user_content=text,
            prompt_version=PromptVersion.V2_EXAMPLES
        )
        
        print(f"风险等级: {result['risk_level']}")
        print(f"诈骗类型: {result['fraud_type']}")
        print(f"风险分数: {result['risk_score']}")
        print(f"置信度: {result['confidence']:.2%}")


def demo_structured_output():
    """演示结构化输出"""
    print("\n" + "="*60)
    print("演示3: 结构化输出")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    text = "我是交易所客服，您的账户需要升级到VIP，需要先充值2000元。"
    
    print("\n输入:", text)
    print("-" * 40)
    
    result = analyzer.analyze_with_llm(
        user_content=text,
        prompt_version=PromptVersion.V3_STRUCTURED
    )
    
    print("结构化结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_contextual_analysis():
    """演示上下文感知分析"""
    print("\n" + "="*60)
    print("演示4: 上下文感知分析（最优版本）")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    # 提供相似案例作为上下文
    similar_cases = [
        {
            "description": "诈骗者声称用户账户被异常登录，要求立即进行身份验证",
            "fraud_type": "钓鱼诈骗",
            "risk_level": "高"
        },
        {
            "description": "要求提供验证码和登录信息以解决账户问题",
            "fraud_type": "钓鱼诈骗",
            "risk_level": "高"
        }
    ]
    
    user_text = "警告：检测到您的Apple ID在异地登录，请立即验证。点击链接确认身份。"
    
    print("\n用户文本:", user_text)
    print("\n相似案例:")
    for i, case in enumerate(similar_cases, 1):
        print(f"  案例{i}: {case['description']}")
    print("-" * 40)
    
    result = analyzer.analyze_with_llm(
        user_content=user_text,
        similar_cases=similar_cases,
        prompt_version=PromptVersion.V4_CONTEXTUAL
    )
    
    print("分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_risk_judgment():
    """演示风险判断器"""
    print("\n" + "="*60)
    print("演示5: 完整风险判断（带用户角色）")
    print("="*60)
    
    judge = LLMRiskJudge()
    
    # 不同用户角色的测试
    test_cases = [
        {
            "text": "你好，我是你的班主任。我们班组织了一个投资理财项目，年收益30%，需要你和家长参加。",
            "role": "child",
            "description": "儿童用户 - 投资诈骗"
        },
        {
            "text": "恭喜您中奖！需要支付0.99元手续费领取100万大奖，请扫码支付。",
            "role": "elderly",
            "description": "老年用户 - 中奖诈骗"
        },
        {
            "text": "成功贷款需要先支付评估费2000元，否则无法放款。",
            "role": "high_risk",
            "description": "高危用户 - 贷款诈骗"
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['description']}")
        print("-" * 40)
        print("文本:", case['text'][:50] + "...")
        
        judgment = judge.judge(
            user_content=case['text'],
            user_role=case['role'],
            prompt_version=PromptVersion.V2_EXAMPLES
        )
        
        print(f"风险等级: {judgment.risk_level.value}")
        print(f"诈骗类型: {judgment.fraud_type}")
        print(f"风险分数: {judgment.risk_score:.1f}")
        print(f"置信度: {judgment.confidence:.2%}")
        print(f"建议: {judgment.advice[:80]}...")


def demo_compare_versions():
    """演示比较不同提示词版本"""
    print("\n" + "="*60)
    print("演示6: 提示词版本对比")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    text = "您好，您的账户异常。请提供验证码以保护您的账户安全。"
    
    print(f"\n测试文本: {text}")
    print("-" * 40)
    
    comparison = analyzer.compare_prompt_versions(user_content=text)
    
    print("\n各版本分析结果对比:")
    print("=" * 60)
    
    for version, result in comparison['versions'].items():
        if 'error' not in result:
            print(f"\n{version}:")
            print(f"  风险等级: {result['risk_level']}")
            print(f"  风险分数: {result['risk_score']}")
            print(f"  置信度: {result['confidence']:.2%}")
        else:
            print(f"\n{version}: 分析失败 - {result['error']}")
    
    print(f"\n推荐版本: {comparison['recommendation']}")


def demo_batch_analysis():
    """演示批量分析"""
    print("\n" + "="*60)
    print("演示7: 批量分析功能")
    print("="*60)
    
    analyzer = LLMAnalyzer()
    
    texts = [
        "快买这个虚拟币，已经翻倍了，还要继续涨！",
        "你好，有什么我可以帮你的吗？",
        "您的账户已被冻结，需要立即转账到安全账户。"
    ]
    
    print(f"\n批量分析{len(texts)}条内容...")
    print("-" * 40)
    
    results = analyzer.batch_analyze(
        contents=texts,
        prompt_version=PromptVersion.V2_EXAMPLES
    )
    
    for i, (text, result) in enumerate(zip(texts, results), 1):
        print(f"\n条目{i}: {text[:40]}...")
        print(f"  风险: {result['risk_level']} | 类型: {result['fraud_type']}")


def demo_local_fallback():
    """演示本地降级方案"""
    print("\n" + "="*60)
    print("演示8: 本地规则判断（API不可用时）")
    print("="*60)
    
    judge = LLMRiskJudge()
    
    text = "朋友，我在电子钱包平台赚了不少钱，你也来试试？"
    
    print(f"\n文本: {text}")
    print("-" * 40)
    
    # 使用本地规则进行判断
    judgment = judge.judge_with_local_rules(
        user_content=text,
        user_role="adult"
    )
    
    print("本地规则判断结果:")
    print(f"风险等级: {judgment.risk_level.value}")
    print(f"诈骗类型: {judgment.fraud_type}")
    print(f"风险分数: {judgment.risk_score:.1f}")
    print(f"理由: {judgment.reasons}")


def demo_detailed_report():
    """演示详细报告"""
    print("\n" + "="*60)
    print("演示9: 详细风险报告")
    print("="*60)
    
    judge = LLMRiskJudge()
    
    text = "您的信用卡将被冻结，请输入你的卡号和CVC以迅速解决this问题。"
    
    print(f"\n分析文本: {text}")
    print("-" * 40)
    
    judgment = judge.judge(
        user_content=text,
        user_role="adult",
        prompt_version=PromptVersion.V2_EXAMPLES
    )
    
    # 生成详细报告
    report = judge.get_judgment_report(judgment)
    
    print("\n详细报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    print("\n" + "="*60)
    print("LLM反诈分析演示程序")
    print("="*60)
    
    demos = [
        ("1", "基础分析功能", demo_basic_analysis),
        ("2", "少样本学习提示词", demo_examples_prompt),
        ("3", "结构化输出", demo_structured_output),
        ("4", "上下文感知分析", demo_contextual_analysis),
        ("5", "完整风险判断", demo_risk_judgment),
        ("6", "提示词版本对比", demo_compare_versions),
        ("7", "批量分析", demo_batch_analysis),
        ("8", "本地规则降级", demo_local_fallback),
        ("9", "详细报告生成", demo_detailed_report),
    ]
    
    print("\n可用的演示:")
    for key, name, _ in demos:
        print(f"  {key}. {name}")
    
    print("\n提示:")
    print("- 如果API密钥未配置，将使用本地模拟结果")
    print("- 推荐使用V2_EXAMPLES（少样本学习）版本")
    print("- 高危用户（儿童、老年人）的风险阈值会自动调整")
    
    # 运行所有演示
    print("\n" + "="*60)
    print("运行所有演示...")
    print("="*60)
    
    try:
        for _, name, demo_func in demos:
            try:
                demo_func()
            except Exception as e:
                print(f"\n演示失败: {e}")
                print("(这可能是因为API未配置，程序将继续...)")
    except KeyboardInterrupt:
        print("\n演示被中断")
    
    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)


if __name__ == "__main__":
    main()
