"""
API 依赖项
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.utils.exceptions import UnauthorizedException


# HTTP Bearer Token 认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前认证用户
    """
    token = credentials.credentials
    
    # 检查 token 是否在黑名单中
    if await TokenService.is_token_blacklisted(token):
        raise UnauthorizedException("Token 已失效，请重新登录")
    
    # 解码 Token
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("无效的认证令牌")
    
    # 验证 token 类型
    if payload.get("type") != "access":
        raise UnauthorizedException("Token 类型错误")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("无效的认证令牌")
    
    # 获取用户
    user = await UserService.get_user_by_id(db, UUID(user_id))
    if not user:
        raise UnauthorizedException("用户不存在")
    
    if not user.is_active:
        raise UnauthorizedException("用户已被禁用")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    """
    if not current_user.is_active:
        raise UnauthorizedException("用户已被禁用")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前超级用户
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

