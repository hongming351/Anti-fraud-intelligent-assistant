from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
import sys
from datetime import datetime
from pydantic import BaseModel, Field
from app.services.auto_updater import update_knowledge_base_job
from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user

# 添加项目根目录到路径，以便导入 Multimodal_processing 模块
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from Multimodal_processing.vector_store import collection, search_similar_cases

router = APIRouter(prefix="/admin", tags=["管理员"])

# 管理员权限检查装饰器
def require_admin(current_user: schemas.UserResponse = Depends(get_current_user)):
    """检查用户是否为管理员"""
    # 这里可以根据实际需求扩展管理员角色检查
    # 暂时假设所有用户都可以访问管理员接口（开发阶段）
    return current_user


# 知识库案例模型
class FraudCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    fraud_type: str = Field(..., min_length=1, max_length=50)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    source: Optional[str] = "manual"
    tags: Optional[List[str]] = []


class FraudCaseResponse(BaseModel):
    id: str
    title: str
    content: str
    fraud_type: str
    risk_level: str
    source: str
    tags: List[str]
    created_at: datetime
    similarity_score: Optional[float] = None


class KnowledgeBaseStats(BaseModel):
    total_cases: int
    last_updated: datetime
    cases_by_type: dict
    cases_by_risk_level: dict
    vector_db_count: int


class BatchImportRequest(BaseModel):
    json_data: List[dict]
    source: str = "batch_import"


# 1. 添加单个诈骗案例到知识库
@router.post("/knowledge/cases", response_model=FraudCaseResponse)
def add_fraud_case(
    case: FraudCaseCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """添加单个诈骗案例到知识库"""
    try:
        # 生成唯一ID
        case_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # 准备向量数据库记录
        text_content = f"【{case.title}】\n{case.content}"
        
        # 插入到向量数据库
        collection.upsert(
            ids=[case_id],
            documents=[text_content],
            metadatas=[{
                "title": case.title,
                "content": case.content,
                "type": case.fraud_type,
                "source": case.source,
                "risk_level": case.risk_level,
                "tags": json.dumps(case.tags, ensure_ascii=False),
                "created_by": current_user.username,
                "created_at": datetime.now().isoformat()
            }]
        )
        
        return FraudCaseResponse(
            id=case_id,
            title=case.title,
            content=case.content,
            fraud_type=case.fraud_type,
            risk_level=case.risk_level,
            source=case.source,
            tags=case.tags,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加案例失败: {str(e)}"
        )


# 2. 批量导入JSON格式的诈骗案例
@router.post("/knowledge/batch-import")
def batch_import_cases(
    import_request: BatchImportRequest,
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """批量导入JSON格式的诈骗案例"""
    try:
        records = []
        for idx, item in enumerate(import_request.json_data):
            title = item.get("title", "")
            content = item.get("content", "")
            fraud_type = item.get("fraud_type", "unknown")
            risk_level = item.get("risk_level", "medium")
            
            if not title or not content:
                continue
                
            text_content = f"【{title}】\n{content}"
            case_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}"
            
            records.append({
                "id": case_id,
                "text": text_content,
                "title": title,
                "content": content,
                "type": fraud_type,
                "source": import_request.source,
                "risk_level": risk_level,
                "created_by": current_user.username,
                "created_at": datetime.now().isoformat()
            })
        
        if records:
            ids = [r["id"] for r in records]
            texts = [r["text"] for r in records]
            metadatas = [
                {
                    "title": r["title"],
                    "content": r["content"],
                    "type": r["type"],
                    "source": r["source"],
                    "risk_level": r["risk_level"],
                    "created_by": r["created_by"],
                    "created_at": r["created_at"]
                }
                for r in records
            ]
            
            collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
            
            return {
                "message": "批量导入成功",
                "imported_count": len(records),
                "total_count": collection.count()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有有效的案例数据"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量导入失败: {str(e)}"
        )


# 3. 获取知识库统计信息（优化版，避免全量加载）
@router.get("/knowledge/stats", response_model=KnowledgeBaseStats)
def get_knowledge_base_stats(
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """获取知识库统计信息"""
    try:
        # 仅获取总数，避免加载全部数据导致性能问题
        total_count = collection.count()
        
        # 注意：cases_by_type 和 cases_by_risk_level 如需详细统计，可后续实现
        # 这里返回空字典，不影响前端显示
        cases_by_type = {}
        cases_by_risk_level = {"low": 0, "medium": 0, "high": 0}
        
        # 读取真实的最后更新时间（由 auto_updater 写入）
        last_update_file = os.path.join(os.path.dirname(__file__), "../services/last_update.txt")
        if os.path.exists(last_update_file):
            try:
                with open(last_update_file, "r") as f:
                    last_updated_str = f.read().strip()
                    last_updated = datetime.fromisoformat(last_updated_str)
            except Exception:
                last_updated = datetime.now()
        else:
            last_updated = datetime.now()
        
        return KnowledgeBaseStats(
            total_cases=total_count,
            last_updated=last_updated,
            cases_by_type=cases_by_type,
            cases_by_risk_level=cases_by_risk_level,
            vector_db_count=total_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


# 4. 搜索知识库中的案例
@router.get("/knowledge/search", response_model=List[FraudCaseResponse])
def search_knowledge_base(
    query: str,
    limit: int = 10,
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """搜索知识库中的诈骗案例"""
    try:
        similar_cases = search_similar_cases(query, top_k=limit)
        
        results = []
        for case in similar_cases:
            # 提取内容（去除标题前缀）
            full_text = case.get("text", "")
            content = full_text.split("\n", 1)[-1] if "\n" in full_text else full_text
            
            results.append(FraudCaseResponse(
                id=case.get("id", ""),
                title=case.get("title", ""),
                content=content,
                fraud_type=case.get("type", "unknown"),
                risk_level=case.get("risk_level", "medium"),
                source=case.get("source", "unknown"),
                tags=json.loads(case.get("tags", "[]")) if case.get("tags") else [],
                created_at=datetime.now(),
                similarity_score=case.get("similarity_score")
            ))
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


# 5. 获取系统状态和自学习进度
@router.get("/system/status")
def get_system_status(
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """获取系统状态和自学习进度"""
    try:
        stats = get_knowledge_base_stats(current_user)
        
        # 模拟自学习进度（实际可从数据库获取分析记录数量计算）
        total_analysis_records = 0  # TODO: 从数据库获取实际值
        
        learning_progress = min(0.85 + (total_analysis_records / 1000) * 0.15, 0.99)
        
        return {
            "knowledge_base": {
                "total_cases": stats.total_cases,
                "last_updated": stats.last_updated,
                "cases_by_type": stats.cases_by_type,
                "cases_by_risk_level": stats.cases_by_risk_level
            },
            "learning_status": {
                "progress": learning_progress,
                "last_training": datetime.now().isoformat(),
                "total_training_samples": total_analysis_records,
                "next_scheduled_training": "每日 03:00"
            },
            "system_health": {
                "vector_db": "healthy" if stats.vector_db_count > 0 else "warning",
                "api_server": "healthy",
                "last_health_check": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )


# 6. 手动触发知识库更新
@router.post("/knowledge/update")
def manual_update_knowledge_base(
    current_user: schemas.UserResponse = Depends(require_admin)
):
    """手动触发知识库更新（调用自动化爬虫与入库任务）"""
    try:
        # 调用真正的更新任务
        result = update_knowledge_base_job()
        
        # 获取更新后的统计信息
        stats = get_knowledge_base_stats(current_user)
        
        return {
            "message": "知识库更新成功",
            "updated_at": datetime.now().isoformat(),
            "total_cases": stats.total_cases,
            "details": result.get("details", "已同步最新诈骗案例库"),
            "new_cases": result.get("new_count", 0)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识库更新失败: {str(e)}"
        )