from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from . import models, schemas
from .security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


# 用户相关CRUD操作
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role.value,
        gender=user.gender,
        risk_sensitivity=user.risk_sensitivity.value,
        guardian_name=user.guardian_name,
        guardian_phone=user.guardian_phone,
        guardian_email=user.guardian_email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"创建用户: {user.username}")
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # 处理枚举类型
    if "role" in update_data and update_data["role"]:
        update_data["role"] = update_data["role"].value
    if "risk_sensitivity" in update_data and update_data["risk_sensitivity"]:
        update_data["risk_sensitivity"] = update_data["risk_sensitivity"].value
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    logger.info(f"更新用户: {db_user.username}")
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    logger.info(f"删除用户: {db_user.username}")
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# 分析记录相关CRUD操作
def get_analysis_record(db: Session, record_id: int) -> Optional[models.AnalysisRecord]:
    return db.query(models.AnalysisRecord).filter(models.AnalysisRecord.id == record_id).first()


def get_analysis_records_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.AnalysisRecord]:
    return (
        db.query(models.AnalysisRecord)
        .filter(models.AnalysisRecord.user_id == user_id)
        .order_by(desc(models.AnalysisRecord.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_analysis_records(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.AnalysisRecord]:
    return (
        db.query(models.AnalysisRecord)
        .order_by(desc(models.AnalysisRecord.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_analysis_record(
    db: Session, 
    record: schemas.AnalysisRecordCreate
) -> models.AnalysisRecord:
    db_record = models.AnalysisRecord(
        user_id=record.user_id,
        analysis_type=record.analysis_type.value,
        input_text=record.input_text,
        audio_file_path=record.audio_file_path,
        image_file_path=record.image_file_path,
        risk_level=record.risk_level.value,
        risk_score=record.risk_score,
        fraud_type=record.fraud_type,
        confidence=record.confidence,
        details=record.details,
        advice=record.advice
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    logger.info(f"创建分析记录: ID={db_record.id}, 用户ID={record.user_id}")
    return db_record


def get_analysis_statistics(db: Session, user_id: Optional[int] = None) -> dict:
    """获取分析统计信息"""
    query = db.query(models.AnalysisRecord)
    
    if user_id:
        query = query.filter(models.AnalysisRecord.user_id == user_id)
    
    total_analyses = query.count()
    
    # 按风险等级统计
    high_risk_count = query.filter(models.AnalysisRecord.risk_level == "high").count()
    medium_risk_count = query.filter(models.AnalysisRecord.risk_level == "medium").count()
    low_risk_count = query.filter(models.AnalysisRecord.risk_level == "low").count()
    
    # 平均风险分数
    avg_risk_score = query.with_entities(func.avg(models.AnalysisRecord.risk_score)).scalar() or 0
    
    # 最常见的诈骗类型
    most_common_fraud_type = (
        query.with_entities(
            models.AnalysisRecord.fraud_type,
            func.count(models.AnalysisRecord.fraud_type).label("count")
        )
        .group_by(models.AnalysisRecord.fraud_type)
        .order_by(desc("count"))
        .first()
    )
    
    # 按分析类型统计
    analysis_by_type = {}
    for analysis_type in ["text", "audio", "image", "multimodal"]:
        count = query.filter(models.AnalysisRecord.analysis_type == analysis_type).count()
        analysis_by_type[analysis_type] = count
    
    return {
        "total_analyses": total_analyses,
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_count": low_risk_count,
        "average_risk_score": float(avg_risk_score),
        "most_common_fraud_type": most_common_fraud_type[0] if most_common_fraud_type else "无",
        "analysis_by_type": analysis_by_type
    }


# 诈骗模式相关CRUD操作
def get_fraud_pattern(db: Session, pattern_id: int) -> Optional[models.FraudPattern]:
    return db.query(models.FraudPattern).filter(models.FraudPattern.id == pattern_id).first()


def get_fraud_patterns(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.FraudPattern]:
    return db.query(models.FraudPattern).offset(skip).limit(limit).all()


def create_fraud_pattern(
    db: Session, 
    pattern: schemas.FraudPatternCreate
) -> models.FraudPattern:
    db_pattern = models.FraudPattern(
        pattern_type=pattern.pattern_type,
        keywords=pattern.keywords,
        description=pattern.description,
        risk_weight=pattern.risk_weight
    )
    db.add(db_pattern)
    db.commit()
    db.refresh(db_pattern)
    logger.info(f"创建诈骗模式: {pattern.pattern_type}")
    return db_pattern


def update_fraud_pattern(
    db: Session, 
    pattern_id: int, 
    pattern_update: schemas.FraudPatternUpdate
) -> Optional[models.FraudPattern]:
    db_pattern = get_fraud_pattern(db, pattern_id)
    if not db_pattern:
        return None
    
    update_data = pattern_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pattern, field, value)
    
    db.commit()
    db.refresh(db_pattern)
    logger.info(f"更新诈骗模式: ID={pattern_id}")
    return db_pattern


def delete_fraud_pattern(db: Session, pattern_id: int) -> bool:
    db_pattern = get_fraud_pattern(db, pattern_id)
    if not db_pattern:
        return False
    
    db.delete(db_pattern)
    db.commit()
    logger.info(f"删除诈骗模式: ID={pattern_id}")
    return True


# 预警相关CRUD操作
def get_alert(db: Session, alert_id: int) -> Optional[models.Alert]:
    return db.query(models.Alert).filter(models.Alert.id == alert_id).first()


def get_alerts_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Alert]:
    return (
        db.query(models.Alert)
        .filter(models.Alert.user_id == user_id)
        .order_by(desc(models.Alert.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_alert(db: Session, alert: schemas.AlertCreate) -> models.Alert:
    db_alert = models.Alert(
        user_id=alert.user_id,
        analysis_record_id=alert.analysis_record_id,
        alert_level=alert.alert_level.value,
        action_taken=alert.action_taken,
        notified_guardian=alert.notified_guardian
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    logger.info(f"创建预警: 用户ID={alert.user_id}, 记录ID={alert.analysis_record_id}")
    return db_alert


def update_alert_notification(
    db: Session, 
    alert_id: int, 
    notified: bool = True
) -> Optional[models.Alert]:
    db_alert = get_alert(db, alert_id)
    if not db_alert:
        return None
    
    db_alert.notified_guardian = notified
    db.commit()
    db.refresh(db_alert)
    logger.info(f"更新预警通知状态: ID={alert_id}, notified={notified}")
    return db_alert


# 系统日志相关CRUD操作
def create_system_log(
    db: Session,
    level: str,
    message: str,
    module: Optional[str] = None,
    details: Optional[str] = None
) -> models.SystemLog:
    log = models.SystemLog(
        level=level,
        module=module,
        message=message,
        details=details
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log