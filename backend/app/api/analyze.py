from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import sys
from datetime import datetime

# 添加路径以便导入多模态处理模块
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from Multimodal_processing.prompt_config import UserDemographic
from Multimodal_processing.multimodal_processor import multimodal_analyze, analyze_text

from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user, validate_file_upload, pagination_params
from ..security import generate_secure_filename
from ..config import settings

router = APIRouter(prefix="/analyze", tags=["分析"])

def get_demographic_from_user(user: schemas.UserResponse) -> UserDemographic:
    """将用户角色映射到人群枚举"""
    if user.role == 'elderly':
        return UserDemographic.ELDERLY
    elif user.role == 'children':
        return UserDemographic.CHILDREN
    else:
        return UserDemographic.ADULT

# ------------------------------
# 改进的适配函数：使用模型真实输出
# ------------------------------
def get_analysis_result(api_result: dict):
    """
    将多模态模块返回的字典转换为后端统一格式
    """
    # 风险等级映射
    level_map = {
        "high": schemas.RiskLevel.HIGH,
        "medium": schemas.RiskLevel.MEDIUM,
        "low": schemas.RiskLevel.LOW,
        "safe": schemas.RiskLevel.LOW
    }
    risk_level = level_map.get(api_result.get("risk_level", "safe"), schemas.RiskLevel.LOW)

    # 置信度：优先使用模型返回的，否则根据风险等级估算
    confidence = api_result.get("confidence")
    if confidence is None:
        if risk_level == schemas.RiskLevel.HIGH:
            confidence = 0.95
        elif risk_level == schemas.RiskLevel.MEDIUM:
            confidence = 0.70
        else:
            confidence = 0.30

    # 风险分数：可沿用简单映射，也可基于置信度计算
    if risk_level == schemas.RiskLevel.HIGH:
        score = 90.0
    elif risk_level == schemas.RiskLevel.MEDIUM:
        score = 60.0
    else:
        score = 20.0

    # 建议文案：优先使用模型返回的
    advice = api_result.get("advice", "请注意防范诈骗，保护财产安全")

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "fraud_type": api_result.get("fraud_type", "正常"),
        "confidence": confidence,
        "details": api_result.get("reason", "分析完成"),
        "advice": advice,
        "timestamp": datetime.utcnow()
    }

# ------------------------------
# 多模态融合辅助函数：取最高风险和最高置信度
# ------------------------------
def merge_analysis_results(results: List[dict]) -> dict:
    """
    融合多个模态的分析结果
    """
    if not results:
        return get_analysis_result({})
    # 风险等级数值映射
    risk_score_map = {
        schemas.RiskLevel.HIGH: 3,
        schemas.RiskLevel.MEDIUM: 2,
        schemas.RiskLevel.LOW: 1,
    }
    # 找出最高风险
    best = max(results, key=lambda x: risk_score_map[x["risk_level"]])
    # 找出最高置信度
    max_confidence = max(r["confidence"] for r in results)
    # 合并：采用最高风险等级、最高置信度，以及第一个的详情（可自定义）
    best["confidence"] = max_confidence
    return best

# ------------------------------
# 1. 文本分析
# ------------------------------
@router.post("/text")
def analyze_text_api(
    request: schemas.TextAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    demo = get_demographic_from_user(current_user)
    raw = analyze_text(request.text, demographic=demo)
    data = get_analysis_result(raw)

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.TEXT,
        input_text=request.text,
        **data
    )
    crud.create_analysis_record(db, record)
    return data

# ------------------------------
# 2. 音频分析
# ------------------------------
@router.post("/audio")
async def analyze_audio(
    audio_file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    demo = get_demographic_from_user(current_user)
    validate_file_upload(audio_file.filename, audio_file.size, "audio")
    fn = generate_secure_filename(audio_file.filename)
    path = os.path.join(settings.UPLOAD_DIR, "audio", fn)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    content = await audio_file.read()
    with open(path, "wb") as f:
        f.write(content)

    raw = multimodal_analyze(path, "audio", demographic=demo)
    data = get_analysis_result(raw)

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.AUDIO,
        audio_file_path=path,
        **data
    )
    crud.create_analysis_record(db, record)
    return data

# ------------------------------
# 3. 图片分析
# ------------------------------
@router.post("/image")
async def analyze_image(
    image_file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    demo = get_demographic_from_user(current_user)
    validate_file_upload(image_file.filename, image_file.size, "image")
    fn = generate_secure_filename(image_file.filename)
    path = os.path.join(settings.UPLOAD_DIR, "image", fn)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    content = await image_file.read()
    with open(path, "wb") as f:
        f.write(content)

    raw = multimodal_analyze(path, "image", demographic=demo)
    data = get_analysis_result(raw)

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.IMAGE,
        image_file_path=path,
        **data
    )
    crud.create_analysis_record(db, record)
    return data

# ------------------------------
# 4. 多模态分析（融合版）
# ------------------------------
@router.post("/multimodal")
async def analyze_multimodal(
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not text and not audio_file and not image_file:
        raise HTTPException(status_code=400, detail="至少提供一种数据")

    demo = get_demographic_from_user(current_user)
    results = []
    audio_path = None
    image_path = None

    # 文本分析
    if text:
        raw = analyze_text(text, demographic=demo)
        results.append(get_analysis_result(raw))

    # 音频分析
    if audio_file:
        validate_file_upload(audio_file.filename, audio_file.size, "audio")
        fn = generate_secure_filename(audio_file.filename)
        audio_path = os.path.join(settings.UPLOAD_DIR, "audio", fn)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(await audio_file.read())
        raw = multimodal_analyze(audio_path, "audio", demographic=demo)
        results.append(get_analysis_result(raw))

    # 图片分析
    if image_file:
        validate_file_upload(image_file.filename, image_file.size, "image")
        fn = generate_secure_filename(image_file.filename)
        image_path = os.path.join(settings.UPLOAD_DIR, "image", fn)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(await image_file.read())
        raw = multimodal_analyze(image_path, "image", demographic=demo)
        results.append(get_analysis_result(raw))

    # 融合结果
    final_data = merge_analysis_results(results)

    # 保存记录
    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.MULTIMODAL,
        input_text=text,
        audio_file_path=audio_path,
        image_file_path=image_path,
        **final_data
    )
    crud.create_analysis_record(db, record)

    return final_data

# ------------------------------
# 历史记录
# ------------------------------
@router.get("/history")
def get_history(
    pagination: dict = Depends(pagination_params),
    user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = crud.get_analysis_records_by_user(db, user.id, **pagination)
    return {"total": len(records), **pagination, "records": records}