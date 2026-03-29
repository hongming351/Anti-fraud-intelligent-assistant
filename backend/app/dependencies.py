from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .security import get_current_user_from_token
from . import models, schemas

# HTTP Bearer认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """获取当前认证用户"""
    token = credentials.credentials
    user = get_current_user_from_token(token, db)
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """获取当前活跃用户"""
    # 这里可以添加用户状态检查，例如是否被禁用等
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """可选获取当前用户（用于公开和需要认证的混合端点）"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user = get_current_user_from_token(token, db)
        return user
    except HTTPException:
        return None


def require_admin(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    """要求管理员权限"""
    # 这里可以根据需要添加管理员检查逻辑
    # 例如：if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def validate_file_upload(
    filename: str,
    file_size: int,
    file_type: str = "image"  # "image" 或 "audio"
) -> bool:
    """验证文件上传"""
    from .config import settings
    
    # 验证文件大小
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB)"
        )
    
    # 验证文件扩展名
    if file_type == "image":
        allowed_extensions = settings.ALLOWED_IMAGE_EXTENSIONS
        error_msg = "不支持的文件类型，请上传图片文件 (jpg, jpeg, png, gif)"
    elif file_type == "audio":
        allowed_extensions = settings.ALLOWED_AUDIO_EXTENSIONS
        error_msg = "不支持的文件类型，请上传音频文件 (mp3, wav, m4a)"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文件类型参数"
        )
    
    from .security import validate_file_extension
    if not validate_file_extension(filename, allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    return True


def pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """分页参数"""
    if limit > 200:
        limit = 200
    if skip < 0:
        skip = 0
    return {"skip": skip, "limit": limit}


def date_range_params(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """日期范围参数"""
    from datetime import datetime
    
    date_range = {}
    
    if start_date:
        try:
            date_range["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的开始日期格式，请使用ISO格式 (YYYY-MM-DD)"
            )
    
    if end_date:
        try:
            date_range["end_date"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的结束日期格式，请使用ISO格式 (YYYY-MM-DD)"
            )
    
    # 验证日期范围
    if "start_date" in date_range and "end_date" in date_range:
        if date_range["start_date"] > date_range["end_date"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期不能晚于结束日期"
            )
    
    return date_range