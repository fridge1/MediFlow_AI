"""
Token 管理服务
"""
from typing import Optional
from datetime import timedelta
from uuid import UUID

from app.core.redis_client import redis_client
from app.core.security import decode_access_token


class TokenService:
    """Token 管理服务"""
    
    @staticmethod
    async def add_token_to_blacklist(token: str, user_id: UUID, expire_seconds: int = 900):
        """
        将 token 添加到黑名单
        
        Args:
            token: JWT token
            user_id: 用户ID
            expire_seconds: 过期时间（秒）
        """
        # 解码 token 获取 jti（如果有的话）
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti", token[:32])  # 使用 jti 或 token 前32位
        else:
            jti = token[:32]
        
        key = f"token_blacklist:{jti}"
        await redis_client.set(key, str(user_id), expire=expire_seconds)
    
    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """
        检查 token 是否在黑名单中
        
        Args:
            token: JWT token
        
        Returns:
            是否在黑名单中
        """
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti", token[:32])
        else:
            jti = token[:32]
        
        key = f"token_blacklist:{jti}"
        return await redis_client.exists(key)
    
    @staticmethod
    async def save_refresh_token(user_id: UUID, refresh_token: str, expire_days: int = 7):
        """
        保存 refresh token 到 Redis
        
        Args:
            user_id: 用户ID
            refresh_token: Refresh token
            expire_days: 过期天数
        """
        key = f"user:{user_id}:refresh_token"
        await redis_client.set(key, refresh_token, expire=expire_days * 86400)
    
    @staticmethod
    async def get_refresh_token(user_id: UUID) -> Optional[str]:
        """
        获取用户的 refresh token
        
        Args:
            user_id: 用户ID
        
        Returns:
            Refresh token 或 None
        """
        key = f"user:{user_id}:refresh_token"
        return await redis_client.get(key)
    
    @staticmethod
    async def delete_refresh_token(user_id: UUID):
        """
        删除用户的 refresh token
        
        Args:
            user_id: 用户ID
        """
        key = f"user:{user_id}:refresh_token"
        await redis_client.delete(key)

