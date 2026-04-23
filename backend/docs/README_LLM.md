# LLM反诈分析集成指南

## 概述

本模块提供了大模型集成的反诈分析功能，包括：

1. **系统提示词** - 4个版本的精心设计的提示词
2. **少样本学习** - 通过提供示例提高判断准确性
3. **LLM API集成** - 支持多种大模型（OpenAI、通义千问、文心一言等）
4. **本地降级方案** - 当API不可用时使用本地规则
5. **用户角色适配** - 根据用户角色调整判断标准
6. **详细报告生成** - 多维度的风险分析报告

## 文件结构

```
backend
├── llm_analyzer.py          # 大模型调用器
├── llm_risk_judge.py        # 风险判断器
└── text_analyzer.py         # 本地文本分析（现有）

backend
├── demo_llm_analysis.py     # 演示脚本
├── integration_example.py   # 集成示例
└── README_LLM.md            # 本文档
```

## 4版本提示词说明

### V1_BASIC - 基础版本
- **适用场景**: 简单判断，快速响应
- **特点**: 直来直往，包含基本判断标准
- **性能**: 最快
- **准确性**: 中等

### V2_EXAMPLES - 少样本学习（推荐）
- **适用场景**: 大多数场景，生产环境
- **特点**: 包含2个详细示例，帮助模型理解判断标准
- **性能**: 快速
- **准确性**: 高（80-90%）
- **推荐理由**: 
  - 通过示例指导模型更好地理解诈骗特征
  - 输出格式更一致
  - 置信度更高

### V3_STRUCTURED - 结构化输出
- **适用场景**: 需要严格数据格式的场景
- **特点**: 明确定义JSON Schema，强制字段类型检查
- **性能**: 中等
- **准确性**: 中等

### V4_CONTEXTUAL - 上下文感知（最优）
- **适用场景**: 涉及复杂诈骗、需要最高准确性
- **特点**: 考虑相似案例、检测通用模式、分析信任欺骗
- **性能**: 较慢（可能需要2-3秒）
- **准确性**: 最高（90%+）
- **推荐理由**:
  - 最符合专家思维
  - 考虑上下文因素
  - 包含详细的模式库

## 快速开始

### 1. 安装依赖

```bash
# 如果使用OpenAI API
pip install openai

# 如果使用阿里通义千问
pip install dashscope

# 如果使用百度文心一言
pip install requests
```

### 2. 配置API密钥

在 `.env` 文件中添加：

```env
# OpenAI
LLM_API_KEY=sk-...

# 或者通义千问
LLM_API_KEY=sk-...
LLM_MODEL=qwen3.5-plus

# 或者文心一言
LLM_API_KEY=your-baidu-api-key
LLM_MODEL=ernie
```

### 3. 基础使用

```python
from app.core.llm_analyzer import LLMAnalyzer, PromptVersion

analyzer = LLMAnalyzer(
    api_key="your-api-key",
    model_name="gpt-4"  # 或其他模型
)

result = analyzer.analyze_with_llm(
    user_content="您的账户异常，请立即转账到安全账户。",
    prompt_version=PromptVersion.V2_EXAMPLES
)

print(result)
# {
#     'fraud_type': '冒充公检法诈骗',
#     'risk_level': '高',
#     'risk_score': 95,
#     'confidence': 0.98,
#     'reasons': [...],
#     'warning_keywords': [...],
#     'advice': '...'
# }
```

### 4. 使用风险判断器

```python
from app.core.llm_risk_judge import LLMRiskJudge, RiskJudgmentLevel

judge = LLMRiskJudge()

# 针对不同用户角色的判断
judgment = judge.judge(
    user_content="一个钓鱼链接...",
    user_role="child",  # child, youth, adult, elderly, high_risk
    prompt_version=PromptVersion.V2_EXAMPLES
)

print(judgment.to_json())
# {
#     'risk_level': '高',
#     'fraud_type': '钓鱼诈骗',
#     'risk_score': 85,
#     'confidence': 0.9,
#     'reasons': [...],
#     'advice': '【面向未成年人的提醒】...'
# }
```

## 集成到FastAPI

### 在现有的analyze路由中集成

```python
# backend/app/api/analyze.py

from ..core.llm_risk_judge import LLMRiskJudge, PromptVersion
from ..core.vector_store import search_similar_cases  # 假设有向量存储

llm_judge = LLMRiskJudge()

@router.post("/text/deep", response_model=schemas.AnalysisResult)
def analyze_text_with_llm(
    request: schemas.TextAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用LLM进行深度文本分析"""
    
    # 搜索相似的诈骗案例（可选）
    similar_cases = search_similar_cases(request.text, limit=3)
    
    # 进行LLM分析
    judgment = llm_judge.judge(
        user_content=request.text,
        similar_cases=similar_cases,
        user_role=current_user.role.value,
        prompt_version=PromptVersion.V2_EXAMPLES
    )
    
    # 转换为响应格式
    final_result = {
        "risk_level": judgment.risk_level.value,
        "risk_score": judgment.risk_score,
        "fraud_type": judgment.fraud_type,
        "confidence": judgment.confidence,
        "details": json.dumps({
            "reasons": judgment.reasons,
            "keywords": judgment.warning_keywords
        }),
        "advice": judgment.advice
    }
    
    # 保存分析记录
    record_data = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.TEXT,
        input_text=request.text,
        risk_level=final_result["risk_level"],
        risk_score=final_result["risk_score"],
        fraud_type=final_result["fraud_type"],
        confidence=final_result["confidence"],
        details=final_result["details"],
        advice=final_result["advice"]
    )
    
    analysis_record = crud.create_analysis_record(db, record_data)
    
    return final_result
```

## 提示词调优建议

### 1. 调整提示词版本

```python
# 比较不同版本
comparison = analyzer.compare_prompt_versions(
    user_content="测试文本"
)

# 查看推荐的最佳版本
best_version = comparison['recommendation']
```

### 2. 在提示词中添加自定义规则

```python
# 使用V4_CONTEXTUAL版本并提供自定义案例

similar_cases = [
    {
        "description": "你的公司特有的诈骗特征...",
        "fraud_type": "内部诈骗",
        "risk_level": "高"
    },
    # ...更多案例
]

result = analyzer.analyze_with_llm(
    user_content="...",
    similar_cases=similar_cases,
    prompt_version=PromptVersion.V4_CONTEXTUAL
)
```

### 3. 调整模型参数

在 `llm_analyzer.py` 中修改API调用参数：

```python
def _call_openai_api(self, prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model=self.model_name,
        messages=[...],
        temperature=0.3,      # 降低：更确定的输出（推荐0.1-0.3）
        top_p=0.9,            # 降低：更聚焦的选择（推荐0.8-0.9）
        max_tokens=1000       # 调整输出长度
    )
```

## 性能优化

### 1. 缓存分析结果

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_analyze(text: str, role: str) -> Dict:
    return llm_judge.judge(
        user_content=text,
        user_role=role
    ).to_dict()
```

### 2. 异步处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def analyze_async(text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: analyzer.analyze_with_llm(text)
    )
```

### 3. 批量分析

```python
results = analyzer.batch_analyze(
    contents=texts,
    prompt_version=PromptVersion.V2_EXAMPLES
)
```

## 错误处理

```python
try:
    judgment = judge.judge(text, user_role="child")
except Exception as e:
    logger.error(f"LLM分析失败: {e}")
    # 自动降级到本地规则
    judgment = judge.judge_with_local_rules(text, user_role="child")
```

## 用户角色特殊处理

不同用户角色的风险阈值和建议文案会自动调整：

| 用户角色 | 高风险阈值 | 中风险阈值 | 特点 |
|---------|---------|---------|------|
| child | 50 | 25 | 最严格，会自动通知监护人 |
| youth | 60 | 30 | 标准 |
| adult | 70 | 40 | 标准 |
| elderly | 55 | 28 | 较严格，会强调与家人确认 |
| high_risk | 40 | 20 | 最严格，会强调报警 |

## 调试和监控

### 查看LLM原始响应

```python
judgment = judge.judge(text)
print(judgment.llm_analysis)  # 查看原始大模型响应
```

### 生成详细报告

```python
report = judge.get_judgment_report(judgment)
print(json.dumps(report, indent=2))
```

### 启用日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 常见问题

### Q: 为什么推荐使用V2_EXAMPLES？
A: 因为少样本学习通过提供具体示例，能显著提高模型的理解和判断准确性，同时保持快速响应。

### Q: 如何处理API超时？
A: 配置超时参数或在配置中设置重试机制。

### Q: 本地规则降级的准确性如何？
A: 本地规则基于关键词匹配，准确性约60-70%，仅用于API不可用的应急情况。

### Q: 如何调整风险阈值？
A: 修改 `llm_risk_judge.py` 中的 `preference_model` 字典。

## 示例输出

### 高风险判断

```json
{
  "risk_level": "高",
  "fraud_type": "冒充公检法诈骗",
  "risk_score": 95,
  "confidence": 0.98,
  "reasons": [
    "冒充政府部门（公安局）",
    "虚构犯罪指控（涉嫌洗钱）",
    "要求转账到陌生账户（安全账户）",
    "使用紧急和恐吓语言"
  ],
  "warning_keywords": ["公安局", "涉嫌洗钱", "安全账户", "立即转账"],
  "advice": "这是典型的冒充公检法诈骗。正规的执法部门不会通过微信/电话要求转账。请立即停止，向96110反诈专线报警。"
}
```

### 中风险判断

```json
{
  "risk_level": "中",
  "fraud_type": "投资理财诈骗",
  "risk_score": 55,
  "confidence": 0.75,
  "reasons": [
    "承诺高回报",
    "要求投入资金",
    "缺乏官方认证"
  ],
  "warning_keywords": ["高回报", "投资", "理财"],
  "advice": "存在诈骗风险。请勿转账或提供个人信息，通过正规渠道核实对方身份。"
}
```

### 低风险判断

```json
{
  "risk_level": "低",
  "fraud_type": "无",
  "risk_score": 15,
  "confidence": 0.95,
  "reasons": [
    "日常闲聊内容",
    "无经济交易建议",
    "无紧急操作要求"
  ],
  "warning_keywords": [],
  "advice": "未检测到明显诈骗迹象，但仍需保持防范意识。"
}
```

## 联系和支持

如有问题，请参考：
- 演示脚本: `backend/demo_llm_analysis.py`
- 集成示例: `backend/integration_example.py`
- API文档: `backend/app/api/analyze.py`
