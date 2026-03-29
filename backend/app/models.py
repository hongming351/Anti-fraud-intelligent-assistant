from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    role = Column(String(20), nullable=False)  # child, youth, adult, elderly, high_risk
    gender = Column(String(10))
    risk_sensitivity = Column(String(10), default="medium")  # low, medium, high
    
    # 监护人信息
    guardian_name = Column(String(100))
    guardian_phone = Column(String(20))
    guardian_email = Column(String(100))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    analysis_records = relationship("AnalysisRecord", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class AnalysisRecord(Base):
    """分析记录表"""
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 分析类型
    analysis_type = Column(String(20), nullable=False)  # text, audio, image, multimodal
    
    # 输入数据
    input_text = Column(Text)
    audio_file_path = Column(String(255))
    image_file_path = Column(String(255))
    
    # 分析结果
    risk_level = Column(String(10), nullable=False)  # low, medium, high
    risk_score = Column(Float, nullable=False)
    fraud_type = Column(String(100))
    confidence = Column(Float, nullable=False)
    details = Column(Text)
    advice = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="analysis_records")
    alerts = relationship("Alert", back_populates="analysis_record")


class FraudPattern(Base):
    """诈骗模式表"""
    __tablename__ = "fraud_patterns"

    id = Column(Integer, primary_key=True, index=True)
    
    # 模式信息
    pattern_type = Column(String(50), nullable=False)  # impersonation, investment, phishing, etc.
    keywords = Column(Text, nullable=False)
    description = Column(Text)
    risk_weight = Column(Float, default=1.0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Alert(Base):
    """预警记录表"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_record_id = Column(Integer, ForeignKey("analysis_records.id"), nullable=False)
    
    # 预警信息
    alert_level = Column(String(10), nullable=False)  # low, medium, high
    action_taken = Column(String(100))  # blocked, notified, reported
    notified_guardian = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="alerts")
    analysis_record = relationship("AnalysisRecord", back_populates="alerts")


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 日志信息
    level = Column(String(10), nullable=False)  # info, warning, error
    module = Column(String(50))
    message = Column(Text, nullable=False)
    details = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())