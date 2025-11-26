"""
消息服务
"""
from typing import Optional, AsyncIterator, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json

from app.models.message import Message
from app.models.conversation import Conversation
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.ai_service import AIModelService
from app.services.model_config_service import ModelConfigService
from app.services.app_service import ApplicationService
from app.services.conversation_service import ConversationService
from app.utils.exceptions import NotFoundException, BadRequestException
from app.utils.logger import logger
from app.utils.distributed_lock import ConversationLock
from app.services.cache_service import ConversationCache


class MessageService:
    """消息服务"""
    
    @staticmethod
    async def create_message(
        db: AsyncSession,
        conv_id: UUID,
        user_id: UUID,
        message_data: MessageCreate
    ) -> Message:
        """创建消息（仅保存到数据库）"""
        # 验证会话
        conv = await ConversationService.get_conversation_by_id(db, conv_id, user_id)
        if not conv:
            raise NotFoundException("会话不存在或无权访问")
        
        # 创建消息
        db_message = Message(
            conversation_id=conv_id,
            role=message_data.role,
            content=message_data.content,
            model_provider=message_data.model_provider,
            model_name=message_data.model_name,
            model_config=message_data.model_config or {}
        )
        db.add(db_message)
        await db.flush()
        await db.refresh(db_message)

        # 更新会话消息计数
        await ConversationService.update_message_count(db, conv_id)
        try:
            await ConversationCache.append_message(conv_id, {"role": db_message.role, "content": db_message.content})
        except Exception:
            pass
        
        return db_message
    
    @staticmethod
    async def get_message_by_id(
        db: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> Optional[Message]:
        """获取消息详情"""
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(
                Message.id == message_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_message_feedback(
        db: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        feedback_data: MessageUpdate
    ) -> Message:
        """更新消息反馈"""
        message = await MessageService.get_message_by_id(db, message_id, user_id)
        if not message:
            raise NotFoundException("消息不存在或无权访问")
        
        update_data = feedback_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(message, key, value)
        
        await db.flush()
        await db.refresh(message)
        
        return message
    
    @staticmethod
    async def delete_message(
        db: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> bool:
        """删除消息"""
        message = await MessageService.get_message_by_id(db, message_id, user_id)
        if not message:
            raise NotFoundException("消息不存在或无权访问")
        
        conv_id = message.conversation_id
        await db.delete(message)
        await db.flush()
        
        # 更新会话消息计数
        await ConversationService.update_message_count(db, conv_id)
        
        return True
    
    @staticmethod
    async def send_message_and_get_response(
        db: AsyncSession,
        conv_id: UUID,
        user_id: UUID,
        message_data: MessageCreate,
        stream: bool = False
    ):
        """
        发送消息并获取 AI 响应
        
        Args:
            db: 数据库会话
            conv_id: 会话ID
            user_id: 用户ID
            message_data: 消息数据
            stream: 是否流式响应
        
        Returns:
            非流式: (user_message, assistant_message)
            流式: AsyncIterator
        """
        # 使用分布式锁防止并发
        async with ConversationLock.with_conversation_lock(str(conv_id), timeout=60):
            logger.info(f"获取会话锁: {conv_id}")
            
            # 1. 保存用户消息
            user_message = await MessageService.create_message(
                db, conv_id, user_id, message_data
            )
        
            # 2. 获取模型配置
            model_config = await MessageService._get_model_config(
                db, user_id, message_data
            )
            
            if not model_config:
                raise BadRequestException("未找到可用的模型配置，请先配置模型")
            
            # 3. 构建消息历史
            messages = await MessageService._build_message_history(
                db, conv_id, message_data.content, model_config
            )
            
            # 4. 调用 AI 模型
            try:
                if stream:
                    # 流式响应
                    return MessageService._stream_ai_response(
                        db, conv_id, messages, model_config
                    )
                else:
                    # 同步响应
                    return await MessageService._sync_ai_response(
                        db, conv_id, messages, model_config, user_message
                    )
            
            except Exception as e:
                logger.error(f"AI 调用失败: {e}")
                raise
    
    @staticmethod
    async def _get_model_config(
        db: AsyncSession,
        user_id: UUID,
        message_data: MessageCreate
    ) -> Optional[Dict[str, Any]]:
        """获取模型配置（三级优先级）"""
        # 1. 请求级别配置（最高优先级）
        if message_data.model_provider and message_data.model_name:
            # 从用户的模型配置中查找
            configs = await ModelConfigService.get_user_model_configs(
                db, user_id, message_data.model_provider
            )
            for config in configs:
                if config.model_name == message_data.model_name and config.is_active:
                    api_key = await ModelConfigService.get_decrypted_api_key(config)
                    return {
                        "provider": config.provider,
                        "model_name": config.model_name,
                        "api_key": api_key,
                        "api_base": config.api_base,
                        "config": {**config.config, **(message_data.model_config or {})}
                    }
        
        # 2. 应用模板配置（中优先级）
        if message_data.use_application_config:
            app_config = await ApplicationService.get_application_config(
                db, UUID(message_data.use_application_config)
            )
            if app_config:
                # 从用户的模型配置中查找对应的 API Key
                configs = await ModelConfigService.get_user_model_configs(
                    db, user_id, app_config["model_provider"]
                )
                for config in configs:
                    if config.model_name == app_config["model_name"] and config.is_active:
                        api_key = await ModelConfigService.get_decrypted_api_key(config)
                        return {
                            "provider": app_config["model_provider"],
                            "model_name": app_config["model_name"],
                            "api_key": api_key,
                            "api_base": config.api_base,
                            "config": app_config["model_config"],
                            "system_prompt": app_config.get("system_prompt")
                        }
        
        # 3. 用户默认配置（最低优先级）
        default_config = await ModelConfigService.get_default_model_config(db, user_id)
        if default_config:
            api_key = await ModelConfigService.get_decrypted_api_key(default_config)
            return {
                "provider": default_config.provider,
                "model_name": default_config.model_name,
                "api_key": api_key,
                "api_base": default_config.api_base,
                "config": default_config.config
            }
        
        return None
    
    @staticmethod
    async def _build_message_history(
        db: AsyncSession,
        conv_id: UUID,
        current_message: str,
        model_config: Dict[str, Any],
        max_history: int = 20
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages: List[Dict[str, str]] = []

        # 添加系统提示（如果有）
        if model_config.get("system_prompt"):
            messages.append({"role": "system", "content": model_config["system_prompt"]})

        # 优先使用缓存
        cached = None
        try:
            cached = await ConversationCache.get_messages(conv_id)
        except Exception:
            cached = None

        if cached:
            for msg in cached[-max_history:]:
                if msg.get("role") in ["user", "assistant"] and msg.get("content") is not None:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            return messages

        # 缓存不可用时查询数据库
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.desc())
            .limit(max_history)
        )
        history = list(result.scalars().all())
        history.reverse()

        plain_history: List[Dict[str, str]] = []
        for msg in history:
            if msg.role in ["user", "assistant"]:
                messages.append({"role": msg.role, "content": msg.content})
                plain_history.append({"role": msg.role, "content": msg.content})

        # 写入缓存（仅最近消息）
        try:
            await ConversationCache.set_messages(conv_id, plain_history, max_count=max_history)
        except Exception:
            pass

        return messages
    
    @staticmethod
    async def _sync_ai_response(
        db: AsyncSession,
        conv_id: UUID,
        messages: List[Dict[str, str]],
        model_config: Dict[str, Any],
        user_message: Message
    ) -> tuple[Message, Message]:
        """同步 AI 响应"""
        # 调用 AI 模型
        response = await AIModelService.chat(
            provider=model_config["provider"],
            api_key=model_config["api_key"],
            model=model_config["model_name"],
            messages=messages,
            stream=False,
            api_base=model_config.get("api_base"),
            **model_config.get("config", {})
        )
        
        # 保存 AI 响应消息
        assistant_message = Message(
            conversation_id=conv_id,
            role="assistant",
            content=response["content"],
            model_provider=model_config["provider"],
            model_name=response["model"],
            model_config=model_config.get("config", {}),
            prompt_tokens=response["usage"]["prompt_tokens"],
            completion_tokens=response["usage"]["completion_tokens"],
            token_count=response["usage"]["total_tokens"]
        )
        db.add(assistant_message)
        await db.flush()
        await db.refresh(assistant_message)

        # 更新会话
        await ConversationService.update_message_count(db, conv_id)
        try:
            await ConversationCache.append_message(conv_id, {"role": "assistant", "content": assistant_message.content})
        except Exception:
            pass
        
        return user_message, assistant_message
    
    @staticmethod
    async def _stream_ai_response(
        db: AsyncSession,
        conv_id: UUID,
        messages: List[Dict[str, str]],
        model_config: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式 AI 响应"""
        # 调用 AI 模型流式接口
        stream = await AIModelService.chat(
            provider=model_config["provider"],
            api_key=model_config["api_key"],
            model=model_config["model_name"],
            messages=messages,
            stream=True,
            api_base=model_config.get("api_base"),
            **model_config.get("config", {})
        )
        
        full_content = ""
        
        async for chunk in stream:
            if not chunk.get("done"):
                content = chunk.get("content", "")
                full_content += content
                yield chunk
            else:
                # 流式响应结束，保存消息
                assistant_message = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_content,
                    model_provider=model_config["provider"],
                    model_name=model_config["model_name"],
                    model_config=model_config.get("config", {})
                )
                db.add(assistant_message)
                await db.flush()
                await db.refresh(assistant_message)
                
                # 更新会话
                await ConversationService.update_message_count(db, conv_id)
                try:
                    await ConversationCache.append_message(conv_id, {"role": "assistant", "content": full_content})
                except Exception:
                    pass
                
                # 返回最后一个块，包含完整信息
                yield {
                    "content": "",
                    "done": True,
                    "message_id": str(assistant_message.id),
                    "model_provider": assistant_message.model_provider,
                    "model_name": assistant_message.model_name
                }
