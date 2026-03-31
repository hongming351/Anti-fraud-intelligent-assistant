from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
from Multimodal_processing.multimodal_processor import multimodal_analyze, analyze_text

from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user, validate_file_upload, pagination_params
from ..security import generate_secure_filename
from ..config import settings

router = APIRouter(prefix="/analyze", tags=["分析"])

# ------------------------------
# 万能适配函数：100%匹配模型
# ------------------------------
def get_analysis_result(api_result):
    # 风险等级映射
    level_map = {
        "high": schemas.RiskLevel.HIGH,
        "medium": schemas.RiskLevel.MEDIUM,
        "low": schemas.RiskLevel.LOW,
        "safe": schemas.RiskLevel.LOW
    }
    risk_level = level_map.get(api_result.get("risk_level"), schemas.RiskLevel.LOW)

    # 分数
    if risk_level == schemas.RiskLevel.HIGH:
        score = 90.0
    elif risk_level == schemas.RiskLevel.MEDIUM:
        score = 60.0
    else:
        score = 20.0

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "fraud_type": api_result.get("fraud_type", "正常"),
        "confidence": 0.95,
        "details": api_result.get("reason", "分析完成"),
        "advice": "请注意防范诈骗，保护财产安全",
        "timestamp": datetime.utcnow()
    }

# ------------------------------
# 1. 文本分析
# ------------------------------
@router.post("/text")
def analyze_text_api(
    request: schemas.TextAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    raw = analyze_text(request.text)
    data = get_analysis_result(raw)

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.TEXT,
        input_text=request.text,** data
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
    validate_file_upload(audio_file.filename, audio_file.size, "audio")
    fn = generate_secure_filename(audio_file.filename)
    path = os.path.join(settings.UPLOAD_DIR, "audio", fn)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    content = await audio_file.read()
    with open(path, "wb") as f:
        f.write(content)

    raw = multimodal_analyze(path, "audio")
    data = get_analysis_result(raw)

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.AUDIO,
        audio_file_path=path,** data
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
    validate_file_upload(image_file.filename, image_file.size, "image")
    fn = generate_secure_filename(image_file.filename)
    path = os.path.join(settings.UPLOAD_DIR, "image", fn)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    content = await image_file.read()
    with open(path, "wb") as f:
        f.write(content)

    raw = multimodal_analyze(path, "image")
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
# 4. 多模态分析（核心修复）
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

    res = None
    audio_path = None
    image_path = None

    # 文本
    if text:
        res = get_analysis_result(analyze_text(text))
    # 音频
    if audio_file:
        validate_file_upload(audio_file.filename, audio_file.size, "audio")
        fn = generate_secure_filename(audio_file.filename)
        audio_path = os.path.join(settings.UPLOAD_DIR, "audio", fn)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(await audio_file.read())
        res = get_analysis_result(multimodal_analyze(audio_path, "audio"))
    # 图片
    if image_file:
        validate_file_upload(image_file.filename, image_file.size, "image")
        fn = generate_secure_filename(image_file.filename)
        image_path = os.path.join(settings.UPLOAD_DIR, "image", fn)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(await image_file.read())
        res = get_analysis_result(multimodal_analyze(image_path, "image"))

    # 保存
    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.MULTIMODAL,
        input_text=text,
        audio_file_path=audio_path,
        image_file_path=image_path,** res
    )
    crud.create_analysis_record(db, record)

    return res

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