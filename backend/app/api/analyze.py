from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import time
from datetime import datetime
from app.services.email_service import send_guardian_alert_email
from app.crud import get_user_behavior_profile
from app.models import AnalysisRecord

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
    if user.role == 'elderly':
        return UserDemographic.ELDERLY
    elif user.role == 'children':
        return UserDemographic.CHILDREN
    else:
        return UserDemographic.ADULT

# ------------------------------
# 改进的适配函数：使用模型真实输出 + 矛盾修正
# ------------------------------
def get_analysis_result(api_result: dict):
    """
    将多模态模块返回的字典转换为后端统一格式，并修正“无诈骗但高危”的矛盾
    """
    raw_risk = api_result.get("risk_level", "safe")
    fraud_type = api_result.get("fraud_type", "正常")
    
    # 如果 fraud_type 表示无诈骗，但 risk_level 不是 low/safe，则强制降级
    if fraud_type in ["无诈骗", "正常", "安全"] and raw_risk not in ["low", "safe"]:
        raw_risk = "safe"
        # 同时降低置信度
        api_result["confidence"] = min(api_result.get("confidence", 0.5), 0.3)
    
    level_map = {
        "high": schemas.RiskLevel.HIGH,
        "medium": schemas.RiskLevel.MEDIUM,
        "low": schemas.RiskLevel.LOW,
        "safe": schemas.RiskLevel.LOW
    }
    risk_level = level_map.get(raw_risk, schemas.RiskLevel.LOW)

    confidence = api_result.get("confidence")
    if confidence is None:
        if risk_level == schemas.RiskLevel.HIGH:
            confidence = 0.95
        elif risk_level == schemas.RiskLevel.MEDIUM:
            confidence = 0.70
        else:
            confidence = 0.30

    # 再次确保：如果风险等级为高危但置信度极低（<0.6），且 fraud_type 非明显诈骗，降级为中危
    if risk_level == schemas.RiskLevel.HIGH and confidence < 0.6 and fraud_type not in ["刷单诈骗", "冒充公检法", "冒充客服退款", "投资理财诈骗", "杀猪盘", "虚假贷款"]:
        risk_level = schemas.RiskLevel.MEDIUM
        confidence = 0.6

    if risk_level == schemas.RiskLevel.HIGH:
        score = 90.0
    elif risk_level == schemas.RiskLevel.MEDIUM:
        score = 60.0
    else:
        score = 20.0

    advice = api_result.get("advice", "请注意防范诈骗，保护财产安全")

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "fraud_type": fraud_type,
        "confidence": confidence,
        "details": api_result.get("reason", "分析完成"),
        "advice": advice,
        "timestamp": datetime.utcnow()
    }

# ------------------------------
# 多模态融合辅助函数：取最高风险和最高置信度 + 矛盾修正
# ------------------------------
def merge_analysis_results(results: List[dict]) -> dict:
    if not results:
        return get_analysis_result({})
    risk_score_map = {
        schemas.RiskLevel.HIGH: 3,
        schemas.RiskLevel.MEDIUM: 2,
        schemas.RiskLevel.LOW: 1,
    }
    best = max(results, key=lambda x: risk_score_map[x["risk_level"]])
    max_confidence = max(r["confidence"] for r in results)
    best["confidence"] = max_confidence

    # 矛盾修正：如果最佳结果的风险等级为高危但诈骗类型为“无诈骗”或“正常”，则降级为中危
    if best["risk_level"] == schemas.RiskLevel.HIGH and best.get("fraud_type") in ["无诈骗", "正常", "安全"]:
        best["risk_level"] = schemas.RiskLevel.MEDIUM
        best["confidence"] = min(best["confidence"], 0.65)
        best["details"] = "（模型判断存在矛盾，已自动降级）" + best.get("details", "")
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
    background_tasks: BackgroundTasks,
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not text and not audio_file and not image_file:
        raise HTTPException(status_code=400, detail="至少提供一种数据")
    start_time = time.time()
    demo = get_demographic_from_user(current_user)
    results = []
    audio_path = None
    image_path = None

    if text:
        raw = analyze_text(text, demographic=demo)
        results.append(get_analysis_result(raw))

    if audio_file:
        validate_file_upload(audio_file.filename, audio_file.size, "audio")
        fn = generate_secure_filename(audio_file.filename)
        audio_path = os.path.join(settings.UPLOAD_DIR, "audio", fn)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(await audio_file.read())
        raw = multimodal_analyze(audio_path, "audio", demographic=demo)
        results.append(get_analysis_result(raw))

    if image_file:
        validate_file_upload(image_file.filename, image_file.size, "image")
        fn = generate_secure_filename(image_file.filename)
        image_path = os.path.join(settings.UPLOAD_DIR, "image", fn)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(await image_file.read())
        raw = multimodal_analyze(image_path, "image", demographic=demo)
        results.append(get_analysis_result(raw))

    final_data = merge_analysis_results(results)

    # ========== 用户行为画像动态调整 ==========
    profile = get_user_behavior_profile(db, current_user.id, recent_limit=5)
    original_risk_level = final_data["risk_level"]
    original_confidence = final_data.get("confidence", 0.5)

    if profile["high_risk_count"] >= 3 and original_risk_level == schemas.RiskLevel.MEDIUM:
        final_data["risk_level"] = schemas.RiskLevel.HIGH
        final_data["confidence"] = min(original_confidence + 0.1, 0.99)
        final_data["details"] += "；用户近期多次遭遇高危风险，已加强预警"

    if profile["avg_risk_score"] > 70 and original_risk_level == schemas.RiskLevel.MEDIUM:
        final_data["risk_level"] = schemas.RiskLevel.HIGH
        final_data["confidence"] = min(original_confidence + 0.1, 0.99)
        final_data["details"] += "；用户历史风险较高，已提高敏感度"

    fraud_type = final_data.get("fraud_type")
    if fraud_type and fraud_type in profile["fraud_type_counts"]:
        count = profile["fraud_type_counts"][fraud_type]
        if count >= 2:
            final_data["confidence"] = min(original_confidence + 0.05 * count, 0.99)
            final_data["details"] += f"；用户曾{count}次遭遇{ fraud_type }，已加强关注"

    from sqlalchemy import func
    recent_count = db.query(func.count(AnalysisRecord.id)).filter(
        AnalysisRecord.user_id == current_user.id
    ).scalar() or 0

    final_data["behavior_profile"] = {
        "avg_risk_score": round(profile["avg_risk_score"], 2),
        "high_risk_count": profile["high_risk_count"],
        "recent_analysis_count": min(recent_count, 5)
    }

    # ========== 监护人联动 ==========
    if final_data["risk_level"] == schemas.RiskLevel.HIGH and current_user.guardian_email:
        background_tasks.add_task(
            send_guardian_alert_email,
            guardian_email=current_user.guardian_email,
            user_name=current_user.username,
            risk_level=final_data["risk_level"].value,
            fraud_type=final_data.get("fraud_type", "未知"),
            user_input=text or "音频或图片内容",
            details=final_data.get("details", ""),
            advice=final_data.get("advice", "")
        )
        final_data["guardian_notified"] = True
    else:
        final_data["guardian_notified"] = False

    record = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.MULTIMODAL,
        input_text=text,
        audio_file_path=audio_path,
        image_file_path=image_path,
        **final_data
    )
    crud.create_analysis_record(db, record)
    
    # 计算总耗时（秒）
    processing_time = time.time() - start_time
    final_data["processing_time"] = round(processing_time, 2)
    
    return final_data

# 添加请求模型
class NotifyRequest(BaseModel):
    analysis_id: int

# 添加一键通报路由
@router.post("/notify-guardian")
def notify_guardian(
    req: NotifyRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = crud.get_analysis_record(db, req.analysis_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="记录不存在")
    if not current_user.guardian_email:
        raise HTTPException(status_code=400, detail="未设置监护人邮箱")
    
    # 复用邮件发送函数
    from app.services.email_service import send_guardian_alert_email
    send_guardian_alert_email(
        guardian_email=current_user.guardian_email,
        user_name=current_user.username,
        risk_level=record.risk_level,
        fraud_type=record.fraud_type,
        user_input=record.input_text or "查看详细报告",
        details=record.details,
        advice=record.advice
    )
    return {"message": "已通知监护人"}

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