"""
LLM反诈分析集成示例
展示如何将LLM分析集成到FastAPI应用中
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app import schemas, crud
from app.database import get_db
from app.dependencies import get_current_user
from app.core.llm_risk_judge import LLMRiskJudge
from app.core.llm_analyzer import PromptVersion

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/analyze-llm", tags=["LLM分析"])

# 创建LLM风险判断器实例
llm_judge = LLMRiskJudge()


class LLMAnalysisRequest(schemas.BaseModel):
    """LLM分析请求"""
    text: str
    enable_examples: bool = True  # 是否使用少样本学习
    include_similar_cases: bool = True  # 是否包含相似案例


class LLMAnalysisResponse(schemas.BaseModel):
    """LLM分析响应"""
    risk_level: str
    fraud_type: str
    risk_score: float
    confidence: float
    reasons: List[str]
    advice: str
    warning_keywords: List[str]


@router.post("/text", response_model=LLMAnalysisResponse)
def analyze_text_with_llm(
    request: LLMAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用LLM进行文本分析
    
    - **text**: 要分析的文本内容
    - **enable_examples**: 是否使用少样本学习（推荐：True）
    - **include_similar_cases**: 是否包含相似案例
    
    返回结果包含：
    - **risk_level**: 风险等级（低/中/高）
    - **fraud_type**: 诈骗类型
    - **risk_score**: 风险分数（0-100）
    - **confidence**: 置信度（0-1）
    - **reasons**: 判断理由
    - **advice**: 建议文案
    - **warning_keywords**: 警告关键词
    """
    try:
        # 选择提示词版本
        prompt_version = (
            PromptVersion.V2_EXAMPLES if request.enable_examples
            else PromptVersion.V1_BASIC
        )
        
        # 获取相似案例（如果需要）
        similar_cases = None
        if request.include_similar_cases:
            # TODO: 从向量数据库或其他来源检索相似案例
            similar_cases = _get_similar_cases(request.text, limit=3)
        
        # 进行LLM分析
        judgment = llm_judge.judge(
            user_content=request.text,
            similar_cases=similar_cases,
            user_role=current_user.role.value,
            prompt_version=prompt_version
        )
        
        # 保存分析记录到数据库
        record_data = schemas.AnalysisRecordCreate(
            user_id=current_user.id,
            analysis_type=schemas.AnalysisType.TEXT,
            input_text=request.text,
            risk_level=judgment.risk_level.value,
            risk_score=judgment.risk_score,
            fraud_type=judgment.fraud_type,
            confidence=judgment.confidence,
            details=str({
                "reasons": judgment.reasons,
                "keywords": judgment.warning_keywords
            }),
            advice=judgment.advice
        )
        
        analysis_record = crud.create_analysis_record(db, record_data)
        
        # 如果风险较高，创建预警
        if judgment.risk_level.value in ["中", "高"]:
            should_notify = (
                current_user.role.value in ["child", "elderly", "high_risk"] and
                judgment.risk_level.value == "高"
            )
            
            alert_data = schemas.AlertCreate(
                user_id=current_user.id,
                analysis_record_id=analysis_record.id,
                alert_level=judgment.risk_level.value,
                action_taken="analyzed",
                notified_guardian=should_notify
            )
            
            crud.create_alert(db, alert_data)
        
        # 返回响应
        return LLMAnalysisResponse(
            risk_level=judgment.risk_level.value,
            fraud_type=judgment.fraud_type,
            risk_score=round(judgment.risk_score, 2),
            confidence=round(judgment.confidence, 3),
            reasons=judgment.reasons,
            advice=judgment.advice,
            warning_keywords=judgment.warning_keywords
        )
        
    except Exception as e:
        logger.error(f"LLM分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


@router.post("/batch", response_model=List[LLMAnalysisResponse])
def batch_analyze_text(
    requests: List[LLMAnalysisRequest],
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量分析多条文本
    
    - **requests**: 分析请求列表（最多50条）
    
    返回结果列表
    """
    if len(requests) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多只能批量分析50条"
        )
    
    results = []
    for request in requests:
        response = analyze_text_with_llm(request, current_user, db)
        results.append(response)
    
    return results


@router.post("/compare-versions/{text_id}")
def compare_prompt_versions(
    text_id: str,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    比较不同提示词版本的效果
    
    - **text_id**: 分析记录ID
    
    用于调试和选择最佳版本
    """
    try:
        # 获取分析记录
        record = crud.get_analysis_record(db, int(text_id), current_user.id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析记录不存在"
            )
        
        # 比较所有版本
        comparison = llm_judge.llm_analyzer.compare_prompt_versions(
            user_content=record.input_text
        )
        
        return {
            "text": record.input_text,
            "versions": comparison["versions"],
            "recommendation": comparison["recommendation"]
        }
    except Exception as e:
        logger.error(f"版本对比失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"比较失败: {str(e)}"
        )


@router.post("/local-fallback")
def analyze_with_local_rules(
    request: LLMAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用本地规则进行分析（当LLM API不可用时）
    
    - **text**: 要分析的文本内容
    
    返回使用本地规则的分析结果
    """
    try:
        # 使用本地规则进行判断
        judgment = llm_judge.judge_with_local_rules(
            user_content=request.text,
            user_role=current_user.role.value
        )
        
        # 保存分析记录
        record_data = schemas.AnalysisRecordCreate(
            user_id=current_user.id,
            analysis_type=schemas.AnalysisType.TEXT,
            input_text=request.text,
            risk_level=judgment.risk_level.value,
            risk_score=judgment.risk_score,
            fraud_type=judgment.fraud_type,
            confidence=judgment.confidence,
            details=str({
                "method": "local_rules",
                "reasons": judgment.reasons
            }),
            advice=judgment.advice
        )
        
        crud.create_analysis_record(db, record_data)
        
        return LLMAnalysisResponse(
            risk_level=judgment.risk_level.value,
            fraud_type=judgment.fraud_type,
            risk_score=round(judgment.risk_score, 2),
            confidence=round(judgment.confidence, 3),
            reasons=judgment.reasons,
            advice=judgment.advice,
            warning_keywords=judgment.warning_keywords
        )
    except Exception as e:
        logger.error(f"本地规则分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


# 辅助函数

def _get_similar_cases(text: str, limit: int = 3) -> Optional[List[dict]]:
    """
    获取相似的诈骗案例
    
    这是一个占位符，实际实现应该从向量数据库检索
    """
    # TODO: 实现向量相似性搜索
    # 示例实现（使用硬编码的案例用于演示）
    
    similar_cases = [
        {
            "description": "诈骗者冒充电信运营商客服，声称有异常消费需要验证",
            "fraud_type": "钓鱼诈骗",
            "risk_level": "高"
        },
        {
            "description": "要求用户点击链接并输入账户和验证码",
            "fraud_type": "钓鱼诈骗",
            "risk_level": "高"
        }
    ]
    
    return similar_cases if text else None


# 扩展现有的分析路由

def extend_existing_router(main_router: APIRouter):
    """
    将LLM分析功能扩展到现有的路由中
    
    Usage:
        from app.api import analyze
        extend_existing_router(analyze.router)
    """
    
    @main_router.post("/text/with-llm", response_model=LLMAnalysisResponse)
    def analyze_text_advanced(
        request: LLMAnalysisRequest,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """
        高级文本分析 - 使用LLM而不是简单的关键词匹配
        """
        return analyze_text_with_llm(request, current_user, db)


# 使用示例

if __name__ == "__main__":
    # 这个脚本展示如何在FastAPI应用中使用LLM分析
    
    print("""
    LLM分析集成示例
    
    要在FastAPI应用中使用这些功能：
    
    1. 在 app/api/analyze.py 中导入本模块的函数
    2. 添加新的路由：
        from app.api.analyze_llm import router as llm_router
        app.include_router(llm_router)
    
    3. 调用API端点：
        POST /analyze-llm/text
        {
            "text": "您的账户异常...",
            "enable_examples": true,
            "include_similar_cases": true
        }
    
    4. 返回结果包含：
        - risk_level: 低/中/高
        - fraud_type: 诈骗类型
        - risk_score: 0-100分数
        - confidence: 0-1置信度
        - reasons: 判断理由列表
        - advice: 针对性建议
        - warning_keywords: 警告关键词
    """)
