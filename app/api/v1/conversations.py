"""
会话管理 API
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse
)
from app.schemas.common import PaginatedResponse
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_user
from app.models.user import User


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    items: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


router = APIRouter(prefix="/conversations", tags=["会话管理"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建会话
    
    会话是独立的对话容器，不强制关联应用
    """
    conv = await ConversationService.create_conversation(db, current_user.id, conv_data)
    await db.commit()
    return conv


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query("active", regex="^(active|archived|deleted)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话列表
    """
    skip = (page - 1) * page_size
    conversations, total = await ConversationService.get_user_conversations(
        db, current_user.id, skip, page_size, status
    )
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    items = [ConversationResponse.model_validate(conv) for conv in conversations]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{conv_id}", response_model=ConversationResponse)
async def get_conversation(
    conv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话详情
    """
    conv = await ConversationService.get_conversation_by_id(db, conv_id, current_user.id)
    if not conv:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("会话不存在")
    return conv


@router.put("/{conv_id}", response_model=ConversationResponse)
async def update_conversation(
    conv_id: UUID,
    conv_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新会话
    """
    conv = await ConversationService.update_conversation(
        db, conv_id, current_user.id, conv_data
    )
    await db.commit()
    return conv


@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除会话(软删除)
    """
    await ConversationService.delete_conversation(db, conv_id, current_user.id)
    await db.commit()
    return {"message": "会话已删除"}


@router.get("/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话的消息列表
    """
    messages = await ConversationService.get_conversation_messages(
        db, conv_id, current_user.id, skip, limit
    )
    return {
        "items": messages,
        "total": len(messages)
    }

