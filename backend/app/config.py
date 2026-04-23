from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 应用配置
    PROJECT_NAME: str = "反诈智能助手后端"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # 邮箱预警功能（注意：字段名与 email_service 中使用的保持一致）
    QQ_EMAIL: str = os.getenv("QQ_EMAIL", "")
    QQ_AUTHORIZATION_CODE: str = os.getenv("QQ_AUTHORIZATION_CODE", "")   # 修改为 QQ_AUTHORIZATION_CODE，与 email_service 匹配
    
    # API 文档配置
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./antifraud.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif"]
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["mp3", "wav", "m4a"]
    UPLOAD_DIR: str = "uploads"
    
    # AI模型配置
    TEXT_MODEL_NAME: str = "bert-base-chinese"
    USE_GPU: bool = False
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 风险评估配置
    RISK_THRESHOLD_HIGH: float = 60.0
    RISK_THRESHOLD_MEDIUM: float = 30.0
    
    # 监护人通知配置
    ENABLE_GUARDIAN_NOTIFICATION: bool = True
    
    # LLM API 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-turbo")
    LLM_API_TIMEOUT: int = 30
    LLM_CACHE_ENABLED: bool = True
    
    # 阿里云百炼 API 配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            # 处理逗号分隔的字符串转换为列表
            if field_name in ["ALLOWED_IMAGE_EXTENSIONS", "ALLOWED_AUDIO_EXTENSIONS"]:
                if raw_val:
                    return [ext.strip() for ext in raw_val.split(",")]
                return []
            return raw_val


# 创建设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)