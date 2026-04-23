from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# 枚举类型
class UserRole(str, Enum):
    CHILD = "child"
    YOUTH = "youth"
    ADULT = "adult"
    ELDERLY = "elderly"
    HIGH_RISK = "high_risk"


class RiskSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnalysisType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SAFE = "safe"  # 👈 补上你缺失的 safe，防止报错


# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole
    gender: Optional[str] = None
    risk_sensitivity: RiskSensitivity = RiskSensitivity.MEDIUM
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    gender: Optional[str] = None
    risk_sensitivity: Optional[RiskSensitivity] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[EmailStr] = None


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass


# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# 分析相关模型
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1)
    enable_deep_analysis: bool = True


class AudioAnalysisRequest(BaseModel):
    enable_deep_audio: bool = True


class ImageAnalysisRequest(BaseModel):
    enable_ocr: bool = True


class MultimodalAnalysisRequest(BaseModel):
    text: Optional[str] = None
    enable_deep_analysis: bool = True
    enable_deep_audio: bool = True
    enable_ocr: bool = True
    enable_behavior_profile: bool = True


# 🔥🔥🔥 核心修复：宽松校验，允许额外字段，永不报错
class AnalysisResult(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0, le=100)
    fraud_type: str
    confidence: float = Field(..., ge=0, le=1)
    details: str
    advice: str
    timestamp: datetime

    # ✅ 宽松校验：允许额外字段，不严格检查
    model_config = ConfigDict(
        extra="allow",
        from_attributes=True
    )


class AnalysisRecordBase(BaseModel):
    analysis_type: AnalysisType
    input_text: Optional[str] = None
    risk_level: RiskLevel
    risk_score: float
    fraud_type: str
    confidence: float
    details: str
    advice: str


class AnalysisRecordCreate(AnalysisRecordBase):
    user_id: int
    audio_file_path: Optional[str] = None
    image_file_path: Optional[str] = None


class AnalysisRecordResponse(AnalysisRecordBase):
    id: int
    user_id: int
    audio_file_path: Optional[str] = None
    image_file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# 诈骗模式相关模型
class FraudPatternBase(BaseModel):
    pattern_type: str = Field(..., min_length=1)
    keywords: str = Field(..., min_length=1)
    description: Optional[str] = None
    risk_weight: float = Field(1.0, ge=0.1, le=5.0)


class FraudPatternCreate(FraudPatternBase):
    pass


class FraudPatternUpdate(BaseModel):
    pattern_type: Optional[str] = None
    keywords: Optional[str] = None
    description: Optional[str] = None
    risk_weight: Optional[float] = None


class FraudPatternResponse(FraudPatternBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 预警相关模型
class AlertBase(BaseModel):
    alert_level: RiskLevel
    action_taken: Optional[str] = None
    notified_guardian: bool = False


class AlertCreate(AlertBase):
    user_id: int
    analysis_record_id: int


class AlertResponse(AlertBase):
    id: int
    user_id: int
    analysis_record_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# 报告相关模型
class ReportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    risk_level: Optional[RiskLevel] = None


class StatisticsResponse(BaseModel):
    total_analyses: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
    most_common_fraud_type: str
    analysis_by_type: dict


# 文件上传相关模型
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    content_type: str