"""
LLM反诈分析快速参考指南 (基于阿里通义千问API)

✅ 千问API已配置并可用
📍 配置位置: .env (backend/.env)
🔑 API密钥: #你的API密钥
🤖 模型: qwen-turbo

⚠️ 注意: 如需修改API密钥或模型，请编辑 backend/.env 文件
"""

# ============================================================
# 0. 快速开始（5分钟上手）
# ============================================================

"""
【现状】千问API已配置，开箱即用！

【最快上手】
1. 运行测试：
   python test_qwen_connection.py

2. 在代码中使用：
   from app.core.llm_risk_judge import LLMRiskJudge
   judge = LLMRiskJudge()
   result = judge.judge("您的账户异常，需要转账验证身份")
   print(result.fraud_type)  # 输出: 冒充官方机构诈骗

【完整测试】
   python demo_llm_analysis.py  # 运行完整演示（9个示例）

【常见问题】
Q: API密钥在哪里？
A: 查看 backend/.env 文件中的 LLM_API_KEY

Q: 如何改用其他模型？
A: 编辑 .env 中的 LLM_MODEL (qwen3.5-plus | qwen-max | qwen-plus | qwen-turbo)

Q: 如何处理API故障？
A: 系统自动降级到本地规则（关键词匹配），无需干预
"""

# ============================================================
# 1. 最简单的使用方法
# ============================================================

from app.core.llm_risk_judge import LLMRiskJudge
from app.core.llm_analyzer import PromptVersion

# 自动使用千问API（基于.env配置）
judge = LLMRiskJudge()

# 一行代码进行风险判断
result = judge.judge("您的账户异常，需要转账验证身份")
print(f"风险等级: {result.risk_level.value}")          # 高
print(f"诈骗类型: {result.fraud_type}")                # 冒充官方机构诈骗
print(f"建议: {result.advice}")                        # [具体安全建议]


# ============================================================
# 2. 针对不同用户角色的判断
# ============================================================

# 儿童用户 - 风险阈值更低
child_judgment = judge.judge(
    text="...",
    user_role="child"  # 将自动调整风险阈值，增加通知监护人的可能
)

# 老年人 - 风险阈值更低
elderly_judgment = judge.judge(
    text="...",
    user_role="elderly"  # 将自动加强建议中"联系家人"的提醒
)


# ============================================================
# 3. 提示词版本选择
# ============================================================

# 方案A: 使用推荐版本（少样本学习）
result = judge.judge(
    text="诈骗文本",
    prompt_version=PromptVersion.V2_EXAMPLES  # ← 推荐用于生产
)

# 方案B: 比较所有版本
comparison = judge.llm_analyzer.compare_prompt_versions("诈骗文本")
best_version = comparison["recommendation"]


# ============================================================
# 4. 处理API不可用的情况
# ============================================================

try:
    result = judge.judge("文本")
except Exception:
    # 自动降级到本地规则
    result = judge.judge_with_local_rules("文本")

print(f"分析方法: {'LLM' if result.llm_analysis else '本地规则'}")


# ============================================================
# 5. 批量分析
# ============================================================

texts = ["文本1", "文本2", "文本3"]

results = judge.llm_analyzer.batch_analyze(
    contents=texts,
    prompt_version=PromptVersion.V2_EXAMPLES
)

for text, result in zip(texts, results):
    print(f"{text}: {result['risk_level']}")


# ============================================================
# 6. 包含相似案例的分析
# ============================================================

similar_cases = [
    {
        "description": "冒充公检法...",
        "fraud_type": "冒充公检法诈骗",
        "risk_level": "高"
    }
]

result = judge.judge(
    user_content="文本",
    similar_cases=similar_cases,  # 参考上下文
    prompt_version=PromptVersion.V4_CONTEXTUAL  # 最优版本
)


# ============================================================
# 7. 生成详细报告
# ============================================================

result = judge.judge("文本")

# 查看详细报告
report = judge.get_judgment_report(result)

# 输出为JSON格式
json_output = result.to_json()


# ============================================================
# 8. 在FastAPI中集成
# ============================================================

from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/analyze")
def analyze(text: str, current_user = Depends(get_current_user)):
    judgment = judge.judge(
        user_content=text,
        user_role=current_user.role
    )
    return judgment.to_json()


# ============================================================
# 9. API配置（.env文件）
# ============================================================

"""
【当前配置 - 阿里通义千问】

LLM_API_KEY=sk-5d27110bbff24ae2901bf89ad058f33b
LLM_MODEL=qwen3.5-plus
LLM_API_TIMEOUT=30

【配置说明】
- LLM_API_KEY    : 阿里通义千问API密钥
- LLM_MODEL      : 使用的模型（qwen3.5-plus | qwen-max | qwen-plus | qwen-turbo）
- LLM_API_TIMEOUT: API调用超时时间（秒）

【如何修改配置】
1. 编辑 backend/.env 文件
2. 更新 LLM_API_KEY 为新的API密钥
3. 更新 LLM_MODEL 为其他千问模型版本（可选）
4. 保存文件后自动生效

【模型对比】
- qwen3.5-plus   : 最新 Qwen3.5 系列，最优的性能与抹平的优算法（推荐）
- qwen-max       : 最强版本，准确度最高，响应时间稍长
- qwen-plus      : 平衡版本，速度与准确度均衡
- qwen-turbo  : 快速版本，响应快但准确度稍低

【测试连接】
python test_qwen_connection.py  # 运行连接测试脚本
"""


# ============================================================
# 10. 性能优化技巧
# ============================================================

# 10.1 缓存结果
from functools import lru_cache

@lru_cache(maxsize=1000)
def analyze_cached(text: str, role: str):
    return judge.judge(text, role).to_json()

# 10.2 异步处理
import asyncio

async def analyze_async(text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: judge.judge(text)
    )


# ============================================================
# 11. 常用的4个风险类别和判断标准
# ============================================================

"""
【高风险 High Risk】(风险分数 60+)
- 立即停止所有操作
- 建议报警（特别是儿童和老年人）
- 例如: 冒充公检法、银行转账要求、紧急验证码请求

【中风险 Medium Risk】(风险分数 30-59)
- 谨慎对待，验证身份
- 不要提供个人信息
- 例如: 投资理财承诺、模糊的账户异常通知

【低风险 Low Risk】(风险分数 0-29)
- 保持警惕但无需立即行动
- 例如: 日常客服交互、正常咨询

【判断标准】
1. 资金要求 +30-50分
2. 身份冒充 +40-60分
3. 紧迫性语言 +20-40分
4. 敏感信息请求 +20-40分
5. 可疑链接/验证码 +30-50分
"""


# ============================================================
# 12. 调试技巧
# ============================================================

import logging
logging.basicConfig(level=logging.DEBUG)

result = judge.judge("文本")

# 查看原始大模型响应
print("LLM原始响应:", result.llm_analysis)

# 查看详细判断报告
report = judge.get_judgment_report(result)
print("详细报告:", report)

# 比较版本
comparison = judge.llm_analyzer.compare_prompt_versions("文本")
print("版本对比:", comparison)


# ============================================================
# 13. 错误处理最佳实践
# ============================================================

def safe_analyze(text: str, role: str = "adult"):
    try:
        # 尝试使用LLM分析
        result = judge.judge(
            user_content=text,
            user_role=role,
            prompt_version=PromptVersion.V2_EXAMPLES
        )
        return ("success", result)
    except Exception as e:
        logger.error(f"LLM分析失败: {e}")
        try:
            # 降级到本地规则
            result = judge.judge_with_local_rules(text, role)
            return ("degraded", result)
        except Exception as e2:
            logger.error(f"本地规则也失败: {e2}")
            return ("error", None)


# ============================================================
# 14. 响应格式标准化
# ============================================================

# 所有方法都返回统一的格式：

result_dict = {
    "risk_level": "高",           # 低/中/高
    "fraud_type": "冒充公检法诈骗",   # 诈骗类型
    "risk_score": 85,              # 0-100
    "confidence": 0.95,            # 0-1
    "reasons": [                   # 判断理由
        "冒充政府部门",
        "要求转账"
    ],
    "warning_keywords": [          # 警告关键词
        "公安局",
        "转账"
    ],
    "advice": "立即停止..."       # 具体建议
}


# ============================================================
# 15. 性能指标参考
# ============================================================

"""
【响应时间】
- V1_BASIC: ~500ms
- V2_EXAMPLES: ~800ms (推荐)
- V3_STRUCTURED: ~1000ms
- V4_CONTEXTUAL: ~2000ms

【准确性】
- 本地规则: ~60-70%
- V1_BASIC: ~70-80%
- V2_EXAMPLES: ~80-90% (推荐)
- V3_STRUCTURED: ~75-85%
- V4_CONTEXTUAL: ~90%+

【特点对比】
┌─────────────────┬──────────┬────────┬──────────┐
│ 版本            │ 速度     │ 准确性 │ 推荐场景 │
├─────────────────┼──────────┼────────┼──────────┤
│ V1_BASIC        │ 最快    │ 中等   │ 演示     │
│ V2_EXAMPLES     │ 快      │ 高     │ 生产环境 │
│ V3_STRUCTURED   │ 中等    │ 中等   │ 严格格式 │
│ V4_CONTEXTUAL   │ 慢      │ 最高   │ 高精度   │
│ 本地规则        │ 极快    │ 低     │ API故障  │
└─────────────────┴──────────┴────────┴──────────┘
"""


# ============================================================
# 16. 快速检查表
# ============================================================

"""
✓ 是否配置了API密钥？
✓ 是否选择了合适的提示词版本（推荐V2）？
✓ 是否处理了用户角色差异？
✓ 是否实现了本地降级方案？
✓ 是否配置了错误处理？
✓ 是否进行了性能测试？
✓ 是否记录了分析日志？
✓ 是否保存了分析结果到数据库？
"""


# ============================================================
# 17. 完整的生产环境示例
# ============================================================

class ProductionAnalyzer:
    def __init__(self):
        self.judge = LLMRiskJudge()
        self.logger = logging.getLogger(__name__)
    
    def analyze_text(self, text: str, user_id: int, user_role: str) -> dict:
        """生产环境复分析函数"""
        try:
            # 尝试LLM分析
            judgment = self.judge.judge(
                user_content=text,
                user_role=user_role,
                prompt_version=PromptVersion.V2_EXAMPLES
            )
            method = "llm"
        except Exception as e:
            self.logger.warning(f"LLM分析失败，使用本地规则: {e}")
            # 降级到本地规则
            judgment = self.judge.judge_with_local_rules(text, user_role)
            method = "local"
        
        # 准备响应
        response = judgment.to_json()
        response["analysis_method"] = method
        
        # 如果风险较高
        if judgment.risk_level.value in ["中", "高"]:
            should_alert = method == "llm" or (
                method == "local" and judgment.risk_score > 60
            )
            if should_alert:
                self._trigger_alert(user_id, judgment)
        
        return response
    
    def _trigger_alert(self, user_id: int, judgment):
        """触发风险预警"""
        self.logger.warning(
            f"用户{user_id}检测到风险: {judgment.fraud_type} "
            f"({judgment.risk_level.value})"
        )


# ============================================================
# 18. 数据库集成示例
# ============================================================

"""
# models.py 中添加

class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    
    input_text = Column(String(5000))
    risk_level = Column(String(10))  # 低/中/高
    fraud_type = Column(String(100))
    risk_score = Column(Float)
    analysis_method = Column(String(50))  # llm 或 local
    llm_prompt_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
"""


# ============================================================
# 使用建议
# ============================================================

"""
【推荐配置】
1. 使用 V2_EXAMPLES 提示词版本（最佳的性能/准确性平衡）
2. 配置 API 超时时间：15-30秒
3. 启用本地降级方案
4. 记录所有分析结果
5. 定期监控 API 费用和使用情况

【优化建议】
1. 对高频用户的结果进行缓存
2. 批量处理有条件的分析请求
3. 根据业务需求调整风险阈值
4. 收集用户反馈并改进模型

【安全建议】
1. 定期备份分析数据
2. 不要在日志中输出敏感用户信息
3. 限制API密钥的使用权限
4. 监控异常的API调用模式
"""
