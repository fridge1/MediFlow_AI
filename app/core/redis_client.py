"""
Redis 客户端管理
"""
from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis

from .config import settings


class RedisClient:
    """Redis 客户端封装"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """连接 Redis"""
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def close(self):
        """关闭 Redis 连接"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """设置值"""
        if not self.redis:
            await self.connect()
        await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """删除键"""
        if not self.redis:
            await self.connect()
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            await self.connect()
        return await self.redis.exists(key) > 0
    
    async def lpush(self, key: str, *values):
        """列表左插入"""
        if not self.redis:
            await self.connect()
        await self.redis.lpush(key, *values)
    
    async def lrange(self, key: str, start: int, end: int):
        """获取列表范围"""
        if not self.redis:
            await self.connect()
        return await self.redis.lrange(key, start, end)
    
    async def ltrim(self, key: str, start: int, end: int):
        """修剪列表"""
        if not self.redis:
            await self.connect()
        await self.redis.ltrim(key, start, end)
    
    async def hset(self, name: str, key: str, value: str):
        """哈希设置"""
        if not self.redis:
            await self.connect()
        await self.redis.hset(name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """哈希获取"""
        if not self.redis:
            await self.connect()
        return await self.redis.hget(name, key)
    
    async def hgetall(self, name: str) -> dict:
        """获取哈希所有字段"""
        if not self.redis:
            await self.connect()
        return await self.redis.hgetall(name)
    
    async def expire(self, key: str, seconds: int):
        """设置过期时间"""
        if not self.redis:
            await self.connect()
        await self.redis.expire(key, seconds)
    
    async def incr(self, key: str) -> int:
        """自增"""
        if not self.redis:
            await self.connect()
        return await self.redis.incr(key)


# 全局 Redis 客户端实例
redis_client = RedisClient()

