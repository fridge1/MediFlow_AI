"""
缓存服务
"""
import json
from typing import Optional, Any, Dict
from uuid import UUID

from app.core.redis_client import redis_client
from app.utils.logger import logger


class CacheService:
    """统一的缓存服务"""
    
    # 缓存过期时间配置（秒）
    CACHE_TTL = {
        "user_default_model": 3600,  # 1小时
        "application_config": 3600,   # 1小时
        "conversation_context": 1800, # 30分钟
        "conversation_messages": 600,  # 10分钟
    }
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """获取缓存"""
        try:
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {e}")
            return None
    
    @staticmethod
    async def set(key: str, value: str, expire: Optional[int] = None):
        """设置缓存"""
        try:
            await redis_client.set(key, value, expire=expire)
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
    
    @staticmethod
    async def delete(key: str):
        """删除缓存"""
        try:
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
    
    @staticmethod
    async def get_json(key: str) -> Optional[Dict]:
        """获取 JSON 缓存"""
        try:
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取 JSON 缓存失败: {key}, 错误: {e}")
            return None
    
    @staticmethod
    async def set_json(key: str, value: Any, expire: Optional[int] = None):
        """设置 JSON 缓存"""
        try:
            json_str = json.dumps(value, default=str)
            await redis_client.set(key, json_str, expire=expire)
        except Exception as e:
            logger.error(f"设置 JSON 缓存失败: {key}, 错误: {e}")


class UserCache:
    """用户相关缓存"""
    
    @staticmethod
    async def get_default_model_config(user_id: UUID) -> Optional[Dict]:
        """获取用户默认模型配置"""
        key = f"user:{user_id}:default_model"
        return await CacheService.get_json(key)
    
    @staticmethod
    async def set_default_model_config(user_id: UUID, config: Dict):
        """设置用户默认模型配置"""
        key = f"user:{user_id}:default_model"
        await CacheService.set_json(
            key, 
            config, 
            expire=CacheService.CACHE_TTL["user_default_model"]
        )
    
    @staticmethod
    async def clear_default_model_config(user_id: UUID):
        """清除用户默认模型配置缓存"""
        key = f"user:{user_id}:default_model"
        await CacheService.delete(key)


class ApplicationCache:
    """应用相关缓存"""
    
    @staticmethod
    async def get_config(app_id: UUID) -> Optional[Dict]:
        """获取应用配置"""
        key = f"application:{app_id}:config"
        return await CacheService.get_json(key)
    
    @staticmethod
    async def set_config(app_id: UUID, config: Dict):
        """设置应用配置"""
        key = f"application:{app_id}:config"
        await CacheService.set_json(
            key, 
            config, 
            expire=CacheService.CACHE_TTL["application_config"]
        )
    
    @staticmethod
    async def clear_config(app_id: UUID):
        """清除应用配置缓存"""
        key = f"application:{app_id}:config"
        await CacheService.delete(key)


class ConversationCache:
    """会话相关缓存"""
    
    @staticmethod
    async def get_messages(conv_id: UUID) -> Optional[list]:
        """获取会话消息缓存"""
        key = f"conversation:{conv_id}:messages"
        return await CacheService.get_json(key)
    
    @staticmethod
    async def set_messages(conv_id: UUID, messages: list, max_count: int = 20):
        """设置会话消息缓存"""
        key = f"conversation:{conv_id}:messages"
        # 只缓存最近的消息
        recent_messages = messages[-max_count:] if len(messages) > max_count else messages
        await CacheService.set_json(
            key, 
            recent_messages, 
            expire=CacheService.CACHE_TTL["conversation_messages"]
        )
    
    @staticmethod
    async def append_message(conv_id: UUID, message: Dict):
        """追加消息到缓存"""
        key = f"conversation:{conv_id}:messages"
        messages = await ConversationCache.get_messages(conv_id) or []
        messages.append(message)
        
        # 保持最多20条
        if len(messages) > 20:
            messages = messages[-20:]
        
        await ConversationCache.set_messages(conv_id, messages)
    
    @staticmethod
    async def get_context(conv_id: UUID) -> Optional[str]:
        """获取会话上下文"""
        key = f"conversation:{conv_id}:context"
        return await CacheService.get(key)
    
    @staticmethod
    async def set_context(conv_id: UUID, context: str):
        """设置会话上下文"""
        key = f"conversation:{conv_id}:context"
        await CacheService.set(
            key, 
            context, 
            expire=CacheService.CACHE_TTL["conversation_context"]
        )
    
    @staticmethod
    async def get_model_info(conv_id: UUID) -> Optional[Dict]:
        """获取会话最近使用的模型信息"""
        key = f"conversation:{conv_id}:model"
        return await redis_client.hgetall(key)
    
    @staticmethod
    async def set_model_info(conv_id: UUID, model_info: Dict):
        """设置会话最近使用的模型信息"""
        key = f"conversation:{conv_id}:model"
        for field, value in model_info.items():
            await redis_client.hset(key, field, str(value))
        await redis_client.expire(key, 3600)  # 1小时
    
    @staticmethod
    async def clear_conversation_cache(conv_id: UUID):
        """清除会话所有缓存"""
        await CacheService.delete(f"conversation:{conv_id}:messages")
        await CacheService.delete(f"conversation:{conv_id}:context")
        await CacheService.delete(f"conversation:{conv_id}:model")

