from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from .config import settings
from . import schemas

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[schemas.TokenData]:
    """验证JWT令牌"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    return token_data


def get_current_user_from_token(token: str, db):
    """从令牌获取当前用户"""
    from .crud import get_user_by_username
    
    token_data = verify_token(token)
    if token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    return user


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """验证文件扩展名"""
    if not filename:
        return False
    
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    return extension in allowed_extensions


def validate_file_size(file_size: int, max_size: int) -> bool:
    """验证文件大小"""
    return file_size <= max_size


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除潜在危险字符"""
    import re
    # 移除非字母数字、点、下划线、连字符
    filename = re.sub(r'[^\w\.\-]', '_', filename)
    # 防止目录遍历攻击
    filename = filename.replace('..', '_')
    return filename


def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    import uuid
    from datetime import datetime
    
    # 获取文件扩展名
    extension = original_filename.split(".")[-1].lower() if "." in original_filename else ""
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    if extension:
        return f"{timestamp}_{unique_id}.{extension}"
    else:
        return f"{timestamp}_{unique_id}"