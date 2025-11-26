"""
应用管理 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationPublish
)
from app.schemas.common import PaginatedResponse
from app.services.app_service import ApplicationService


class ApplicationListResponse(BaseModel):
    """应用列表响应"""
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


router = APIRouter(prefix="/applications", tags=["应用管理"])


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建应用配置模板
    """
    app = await ApplicationService.create_application(db, current_user.id, app_data)
    await db.commit()
    return app


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(draft|published)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用列表
    """
    skip = (page - 1) * page_size
    apps, total = await ApplicationService.get_user_applications(
        db, current_user.id, skip, page_size, status
    )
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    items = [ApplicationResponse.model_validate(app) for app in apps]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用详情
    """
    app = await ApplicationService.get_application_by_id(db, app_id, current_user.id)
    if not app:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("应用不存在")
    return app


@router.get("/{app_id}/config")
async def get_application_config(
    app_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用的模型配置
    """
    config = await ApplicationService.get_application_config(db, app_id)
    if not config:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("应用不存在")
    return config


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: UUID,
    app_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新应用
    """
    app = await ApplicationService.update_application(db, app_id, current_user.id, app_data)
    await db.commit()
    return app


@router.delete("/{app_id}")
async def delete_application(
    app_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除应用
    """
    await ApplicationService.delete_application(db, app_id, current_user.id)
    await db.commit()
    return {"message": "应用已删除"}


@router.post("/{app_id}/publish", response_model=ApplicationResponse)
async def publish_application(
    app_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发布应用
    """
    app = await ApplicationService.publish_application(db, app_id, current_user.id)
    await db.commit()
    return app
