"""
安全相关功能：密码加密、JWT Token 生成与验证
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
import base64
import uuid

from .config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # Bcrypt限制密码长度为72字节
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # Bcrypt限制密码长度为72字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 生成盐并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT Access Token
    
    Args:
        data: 要编码的数据(通常包含 sub: user_id)
        expires_delta: 过期时间
    
    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Access token 15分钟
    
    # 添加唯一的 JTI (JWT ID)
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(), 
        "type": "access",
        "jti": jti
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    生成 JWT Refresh Token
    
    Args:
        data: 要编码的数据(通常包含 sub: user_id)
    
    Returns:
        JWT refresh token 字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh token 7天
    
    # 添加唯一的 JTI (JWT ID)
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(), 
        "type": "refresh",
        "jti": jti
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT Token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


class APIKeyEncryption:
    """API Key 加密工具"""
    
    def __init__(self):
        # 确保密钥是32字节(base64编码后)
        key = settings.ENCRYPTION_KEY.encode()
        if len(key) < 32:
            key = key.ljust(32, b'0')
        elif len(key) > 32:
            key = key[:32]
        
        self.fernet = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, api_key: str) -> str:
        """加密 API Key"""
        return self.fernet.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """解密 API Key"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()


# 全局加密实例
api_key_encryption = APIKeyEncryption()
