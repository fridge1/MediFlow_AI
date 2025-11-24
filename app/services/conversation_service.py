"""
会话服务
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
import json

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.core.redis_client import redis_client
from app.services.cache_service import ConversationCache
from app.utils.exceptions import NotFoundException
from app.utils.logger import logger


class ConversationService:
    """会话服务"""
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession, 
        user_id: UUID, 
        conv_data: ConversationCreate
    ) -> Conversation:
        """创建会话"""
        db_conv = Conversation(
            user_id=user_id,
            title=conv_data.title or "新对话",
            conv_metadata=conv_data.conv_metadata
        )
        db.add(db_conv)
        await db.flush()
        await db.refresh(db_conv)
        
        logger.info(f"创建会话: {db_conv.id}, 用户: {user_id}")
        
        return db_conv
    
    @staticmethod
    async def get_conversation_by_id(
        db: AsyncSession, 
        conv_id: UUID, 
        user_id: UUID
    ) -> Optional[Conversation]:
        """获取会话详情"""
        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_conversations(
        db: AsyncSession, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: str = "active"
    ) -> tuple[List[Conversation], int]:
        """获取用户的会话列表"""
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.status == status
            )
        )
        
        # 获取总数
        count_result = await db.execute(
            select(func.count()).select_from(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.status == status
                )
            )
        )
        total = count_result.scalar()
        
        # 分页查询
        query = query.order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return list(conversations), total
    
    @staticmethod
    async def update_conversation(
        db: AsyncSession, 
        conv_id: UUID, 
        user_id: UUID, 
        conv_data: ConversationUpdate
    ) -> Conversation:
        """更新会话"""
        conv = await ConversationService.get_conversation_by_id(db, conv_id, user_id)
        if not conv:
            raise NotFoundException("会话不存在或无权访问")
        
        update_data = conv_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(conv, key, value)
        
        await db.flush()
        await db.refresh(conv)
        
        return conv
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession, 
        conv_id: UUID, 
        user_id: UUID
    ) -> bool:
        """删除会话(软删除)"""
        conv = await ConversationService.get_conversation_by_id(db, conv_id, user_id)
        if not conv:
            raise NotFoundException("会话不存在或无权访问")
        
        conv.status = "deleted"
        await db.flush()
        
        # 清除 Redis 缓存
        await ConversationCache.clear_conversation_cache(conv_id)
        
        logger.info(f"删除会话: {conv_id}")
        
        return True
    
    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession, 
        conv_id: UUID, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """获取会话的消息列表"""
        # 验证会话权限
        conv = await ConversationService.get_conversation_by_id(db, conv_id, user_id)
        if not conv:
            raise NotFoundException("会话不存在或无权访问")
        
        query = select(Message).where(Message.conversation_id == conv_id)
        query = query.order_by(Message.created_at.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all())
    
    @staticmethod
    async def update_message_count(db: AsyncSession, conv_id: UUID):
        """更新会话消息计数"""
        result = await db.execute(
            select(func.count()).select_from(Message).where(Message.conversation_id == conv_id)
        )
        count = result.scalar()
        
        conv_result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = conv_result.scalar_one_or_none()
        if conv:
            conv.message_count = count
            conv.last_message_at = datetime.utcnow()
            await db.flush()
    
    @staticmethod
    async def cache_messages_to_redis(conv_id: UUID, messages: List[dict], max_count: int = 20):
        """缓存消息到 Redis（使用统一缓存服务）"""
        await ConversationCache.set_messages(conv_id, messages, max_count)
    
    @staticmethod
    async def get_cached_messages(conv_id: UUID) -> Optional[List[dict]]:
        """从 Redis 获取缓存的消息（使用统一缓存服务）"""
        return await ConversationCache.get_messages(conv_id)

