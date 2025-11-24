"""
用户管理 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.common import PaginatedResponse
from app.services.user_service import UserService
from app.api.deps import get_current_user, get_current_superuser
from app.models.user import User


router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息
    """
    user = await UserService.update_user(db, current_user.id, user_data)
    await db.commit()
    return user


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（仅管理员）
    """
    skip = (page - 1) * page_size
    users, total = await UserService.get_users(db, skip, page_size)
    
    return {
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户详情（仅管理员）
    """
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（仅管理员）
    """
    user = await UserService.update_user(db, user_id, user_data)
    await db.commit()
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（仅管理员，软删除）
    """
    await UserService.deactivate_user(db, user_id)
    await db.commit()
    return {"message": "用户已禁用"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    激活用户（仅管理员）
    """
    await UserService.activate_user(db, user_id)
    await db.commit()
    return {"message": "用户已激活"}

