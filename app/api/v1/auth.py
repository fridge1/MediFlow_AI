"""
认证相关 API
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.exceptions import UnauthorizedException


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    """
    user = await UserService.create_user(db, user_data)
    await db.commit()
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    """
    # 验证用户
    user = await UserService.authenticate_user(
        db, 
        login_data.username, 
        login_data.password
    )
    
    if not user:
        raise UnauthorizedException("用户名或密码错误")
    
    # 生成 Access Token (15分钟)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=15)
    )
    
    # 生成 Refresh Token (7天)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    # 保存 Refresh Token 到 Redis
    await TokenService.save_refresh_token(user.id, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900  # 15分钟 = 900秒
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Header(..., alias="X-Refresh-Token"),
    db: AsyncSession = Depends(get_db)
):
    """
    刷新 Access Token
    
    Headers:
        X-Refresh-Token: Refresh token
    """
    # 解码 refresh token
    payload = decode_access_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("无效的 Refresh Token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("无效的 Refresh Token")
    
    # 验证用户存在
    user = await UserService.get_user_by_id(db, UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedException("用户不存在或已被禁用")
    
    # 验证 refresh token 是否在 Redis 中
    saved_token = await TokenService.get_refresh_token(user.id)
    if not saved_token or saved_token != refresh_token:
        raise UnauthorizedException("Refresh Token 已失效")
    
    # 生成新的 Access Token
    new_access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=15)
    )
    
    # 可选：生成新的 Refresh Token（刷新链）
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    await TokenService.save_refresh_token(user.id, new_refresh_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 900
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(...)
):
    """
    用户登出
    
    将当前 token 加入黑名单，并删除 refresh token
    """
    # 提取 token
    token = authorization.replace("Bearer ", "")
    
    # 添加到黑名单（15分钟过期）
    await TokenService.add_token_to_blacklist(token, current_user.id, expire_seconds=900)
    
    # 删除 refresh token
    await TokenService.delete_refresh_token(current_user.id)
    
    return {"message": "登出成功"}

