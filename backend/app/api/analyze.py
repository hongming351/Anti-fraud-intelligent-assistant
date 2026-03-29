from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os

from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user, validate_file_upload, pagination_params
from ..core.text_analyzer import text_analyzer
from ..core.risk_assessor import risk_assessor
from ..security import generate_secure_filename, sanitize_filename
from ..config import settings

router = APIRouter(prefix="/analyze", tags=["分析"])


@router.post("/text", response_model=schemas.AnalysisResult)
def analyze_text(
    request: schemas.TextAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """文本分析"""
    # 使用文本分析器进行分析
    analysis_result = text_analyzer.analyze_text(
        text=request.text,
        enable_deep_analysis=request.enable_deep_analysis
    )
    
    # 使用风险评估器生成完整结果
    final_result = risk_assessor.generate_analysis_result(
        risk_score=analysis_result["risk_score"],
        fraud_type=analysis_result["fraud_type"],
        confidence=analysis_result["confidence"],
        details=analysis_result["details"],
        user_role=current_user.role.value,
        risk_sensitivity=current_user.risk_sensitivity.value,
        analysis_type="text"
    )
    
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
    
    # 检查是否需要创建预警
    if final_result["risk_level"] in [schemas.RiskLevel.HIGH, schemas.RiskLevel.MEDIUM]:
        alert_data = schemas.AlertCreate(
            user_id=current_user.id,
            analysis_record_id=analysis_record.id,
            alert_level=final_result["risk_level"],
            action_taken="analyzed",
            notified_guardian=risk_assessor.should_notify_guardian(
                final_result["risk_level"],
                bool(current_user.guardian_name),
                current_user.risk_sensitivity.value
            )
        )
        crud.create_alert(db, alert_data)
    
    return final_result


@router.post("/audio", response_model=schemas.AnalysisResult)
async def analyze_audio(
    request: schemas.AudioAnalysisRequest,
    audio_file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """音频分析"""
    # 验证文件
    validate_file_upload(
        filename=audio_file.filename,
        file_size=audio_file.size,
        file_type="audio"
    )
    
    # 生成安全文件名并保存文件
    safe_filename = generate_secure_filename(audio_file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, "audio", safe_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存文件
    content = await audio_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 模拟音频分析结果（实际应调用语音识别和音频分析）
    # 这里使用文本分析器的结果作为模拟
    simulated_text = f"音频文件分析: {audio_file.filename} (模拟结果)"
    
    analysis_result = text_analyzer.analyze_text(
        text=simulated_text,
        enable_deep_analysis=request.enable_deep_audio
    )
    
    # 调整分数以反映音频分析
    audio_adjusted_score = analysis_result["risk_score"] * 1.1
    
    # 使用风险评估器生成完整结果
    final_result = risk_assessor.generate_analysis_result(
        risk_score=audio_adjusted_score,
        fraud_type=f"音频{analysis_result['fraud_type']}",
        confidence=analysis_result["confidence"] * 0.9,  # 音频分析置信度稍低
        details=f"音频分析: {analysis_result['details']}",
        user_role=current_user.role.value,
        risk_sensitivity=current_user.risk_sensitivity.value,
        analysis_type="audio"
    )
    
    # 保存分析记录
    record_data = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.AUDIO,
        audio_file_path=file_path,
        risk_level=final_result["risk_level"],
        risk_score=final_result["risk_score"],
        fraud_type=final_result["fraud_type"],
        confidence=final_result["confidence"],
        details=final_result["details"],
        advice=final_result["advice"]
    )
    
    analysis_record = crud.create_analysis_record(db, record_data)
    
    # 检查是否需要创建预警
    if final_result["risk_level"] in [schemas.RiskLevel.HIGH, schemas.RiskLevel.MEDIUM]:
        alert_data = schemas.AlertCreate(
            user_id=current_user.id,
            analysis_record_id=analysis_record.id,
            alert_level=final_result["risk_level"],
            action_taken="analyzed",
            notified_guardian=risk_assessor.should_notify_guardian(
                final_result["risk_level"],
                bool(current_user.guardian_name),
                current_user.risk_sensitivity.value
            )
        )
        crud.create_alert(db, alert_data)
    
    return final_result


@router.post("/image", response_model=schemas.AnalysisResult)
async def analyze_image(
    request: schemas.ImageAnalysisRequest,
    image_file: UploadFile = File(...),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """图像分析"""
    # 验证文件
    validate_file_upload(
        filename=image_file.filename,
        file_size=image_file.size,
        file_type="image"
    )
    
    # 生成安全文件名并保存文件
    safe_filename = generate_secure_filename(image_file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, "image", safe_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存文件
    content = await image_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 模拟图像分析结果（实际应调用OCR和图像分析）
    # 这里使用文本分析器的结果作为模拟
    simulated_text = f"图像文件分析: {image_file.filename} (模拟结果)"
    
    analysis_result = text_analyzer.analyze_text(
        text=simulated_text,
        enable_deep_analysis=request.enable_ocr
    )
    
    # 调整分数以反映图像分析
    image_adjusted_score = analysis_result["risk_score"] * 1.05
    
    # 使用风险评估器生成完整结果
    final_result = risk_assessor.generate_analysis_result(
        risk_score=image_adjusted_score,
        fraud_type=f"图像{analysis_result['fraud_type']}",
        confidence=analysis_result["confidence"] * 0.85,  # 图像分析置信度较低
        details=f"图像分析: {analysis_result['details']}",
        user_role=current_user.role.value,
        risk_sensitivity=current_user.risk_sensitivity.value,
        analysis_type="image"
    )
    
    # 保存分析记录
    record_data = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.IMAGE,
        image_file_path=file_path,
        risk_level=final_result["risk_level"],
        risk_score=final_result["risk_score"],
        fraud_type=final_result["fraud_type"],
        confidence=final_result["confidence"],
        details=final_result["details"],
        advice=final_result["advice"]
    )
    
    analysis_record = crud.create_analysis_record(db, record_data)
    
    # 检查是否需要创建预警
    if final_result["risk_level"] in [schemas.RiskLevel.HIGH, schemas.RiskLevel.MEDIUM]:
        alert_data = schemas.AlertCreate(
            user_id=current_user.id,
            analysis_record_id=analysis_record.id,
            alert_level=final_result["risk_level"],
            action_taken="analyzed",
            notified_guardian=risk_assessor.should_notify_guardian(
                final_result["risk_level"],
                bool(current_user.guardian_name),
                current_user.risk_sensitivity.value
            )
        )
        crud.create_alert(db, alert_data)
    
    return final_result


@router.post("/multimodal", response_model=schemas.AnalysisResult)
async def analyze_multimodal(
    request: schemas.MultimodalAnalysisRequest,
    text: Optional[str] = None,
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """多模态融合分析"""
    if not text and not audio_file and not image_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供文本、音频或图像其中一种数据"
        )
    
    analysis_results = []
    file_paths = {"audio": None, "image": None}
    
    # 文本分析
    if text:
        text_result = text_analyzer.analyze_text(
            text=text,
            enable_deep_analysis=request.enable_deep_analysis
        )
        analysis_results.append({
            "type": "text",
            "score": text_result["risk_score"],
            "confidence": text_result["confidence"],
            "details": text_result["details"]
        })
    
    # 音频分析
    if audio_file:
        # 验证文件
        validate_file_upload(
            filename=audio_file.filename,
            file_size=audio_file.size,
            file_type="audio"
        )
        
        # 保存文件
        safe_filename = generate_secure_filename(audio_file.filename)
        audio_path = os.path.join(settings.UPLOAD_DIR, "audio", safe_filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        content = await audio_file.read()
        with open(audio_path, "wb") as f:
            f.write(content)
        
        file_paths["audio"] = audio_path
        
        # 模拟音频分析
        audio_result = text_analyzer.analyze_text(
            text=f"音频分析: {audio_file.filename}",
            enable_deep_analysis=request.enable_deep_audio
        )
        analysis_results.append({
            "type": "audio",
            "score": audio_result["risk_score"] * 1.1,
            "confidence": audio_result["confidence"] * 0.9,
            "details": f"音频分析: {audio_result['details']}"
        })
    
    # 图像分析
    if image_file:
        # 验证文件
        validate_file_upload(
            filename=image_file.filename,
            file_size=image_file.size,
            file_type="image"
        )
        
        # 保存文件
        safe_filename = generate_secure_filename(image_file.filename)
        image_path = os.path.join(settings.UPLOAD_DIR, "image", safe_filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        content = await image_file.read()
        with open(image_path, "wb") as f:
            f.write(content)
        
        file_paths["image"] = image_path
        
        # 模拟图像分析
        image_result = text_analyzer.analyze_text(
            text=f"图像分析: {image_file.filename}",
            enable_deep_analysis=request.enable_ocr
        )
        analysis_results.append({
            "type": "image",
            "score": image_result["risk_score"] * 1.05,
            "confidence": image_result["confidence"] * 0.85,
            "details": f"图像分析: {image_result['details']}"
        })
    
    # 融合分析结果
    if not analysis_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分析失败，未获取到有效结果"
        )
    
    # 计算加权平均分数
    total_weight = 0
    weighted_score = 0
    weighted_confidence = 0
    details_parts = []
    
    for result in analysis_results:
        weight = 1.0
        if result["type"] == "text":
            weight = 1.2 if request.enable_deep_analysis else 1.0
        elif result["type"] == "audio":
            weight = 1.1 if request.enable_deep_audio else 1.0
        elif result["type"] == "image":
            weight = 1.05 if request.enable_ocr else 1.0
        
        weighted_score += result["score"] * weight
        weighted_confidence += result["confidence"] * weight
        details_parts.append(result["details"])
        total_weight += weight
    
    avg_score = weighted_score / total_weight
    avg_confidence = weighted_confidence / total_weight
    combined_details = " | ".join(details_parts)
    
    # 多模态分析通常更准确，提高置信度
    if len(analysis_results) > 1:
        avg_confidence = min(avg_confidence * 1.1, 0.98)
    
    # 确定主要诈骗类型（使用文本分析的结果如果有）
    fraud_type = "多模态诈骗"
    if text and "text" in [r["type"] for r in analysis_results]:
        text_result = text_analyzer.analyze_text(text, False)
        fraud_type = f"多模态{text_result['fraud_type']}"
    
    # 使用风险评估器生成完整结果
    final_result = risk_assessor.generate_analysis_result(
        risk_score=avg_score,
        fraud_type=fraud_type,
        confidence=avg_confidence,
        details=f"多模态融合分析: {combined_details}",
        user_role=current_user.role.value,
        risk_sensitivity=current_user.risk_sensitivity.value,
        analysis_type="multimodal"
    )
    
    # 保存分析记录
    record_data = schemas.AnalysisRecordCreate(
        user_id=current_user.id,
        analysis_type=schemas.AnalysisType.MULTIMODAL,
        input_text=text,
        audio_file_path=file_paths["audio"],
        image_file_path=file_paths["image"],
        risk_level=final_result["risk_level"],
        risk_score=final_result["risk_score"],
        fraud_type=final_result["fraud_type"],
        confidence=final_result["confidence"],
        details=final_result["details"],
        advice=final_result["advice"]
    )
    
    analysis_record = crud.create_analysis_record(db, record_data)
    
    # 检查是否需要创建预警
    if final_result["risk_level"] in [schemas.RiskLevel.HIGH, schemas.RiskLevel.MEDIUM]:
        alert_data = schemas.AlertCreate(
            user_id=current_user.id,
            analysis_record_id=analysis_record.id,
            alert_level=final_result["risk_level"],
            action_taken="analyzed",
            notified_guardian=risk_assessor.should_notify_guardian(
                final_result["risk_level"],
                bool(current_user.guardian_name),
                current_user.risk_sensitivity.value
            )
        )
        crud.create_alert(db, alert_data)
    
    return final_result


@router.get("/history")
def get_analysis_history(
    pagination: dict = Depends(pagination_params),
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分析历史"""
    records = crud.get_analysis_records_by_user(
        db, current_user.id, 
        skip=pagination["skip"], 
        limit=pagination["limit"]
    )
    
    return {
        "total": len(records),
        "skip": pagination["skip"],
        "limit": pagination["limit"],
        "records": records
    }