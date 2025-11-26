"""
Redis 分布式锁
"""
import asyncio
import time
from typing import Optional
from uuid import uuid4

from app.core.redis_client import redis_client
from app.utils.logger import logger


class DistributedLock:
    """Redis 分布式锁"""
    
    def __init__(
        self, 
        key: str, 
        timeout: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1
    ):
        """
        初始化分布式锁
        
        Args:
            key: 锁的键名
            timeout: 锁超时时间（秒）
            retry_times: 获取锁失败时的重试次数
            retry_delay: 重试延迟（秒）
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.identifier = str(uuid4())  # 唯一标识，用于安全释放锁
        self._locked = False
    
    async def acquire(self) -> bool:
        """
        获取锁
        
        Returns:
            是否成功获取锁
        """
        for attempt in range(self.retry_times):
            try:
                # 使用 SET NX EX 原子操作
                result = await redis_client.redis.set(
                    self.key,
                    self.identifier,
                    nx=True,  # 只有键不存在时才设置
                    ex=self.timeout  # 设置过期时间
                )
                
                if result:
                    self._locked = True
                    logger.debug(f"成功获取锁: {self.key}")
                    return True
                
                # 获取失败，等待后重试
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"获取锁失败: {self.key}, 错误: {e}")
                return False
        
        logger.warning(f"无法获取锁: {self.key}, 已重试 {self.retry_times} 次")
        return False
    
    async def release(self) -> bool:
        """
        释放锁（安全释放，只释放自己持有的锁）
        
        Returns:
            是否成功释放锁
        """
        if not self._locked:
            return False
        
        try:
            # 使用 Lua 脚本确保只释放自己的锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = await redis_client.redis.eval(
                lua_script,
                1,
                self.key,
                self.identifier
            )
            
            if result:
                self._locked = False
                logger.debug(f"成功释放锁: {self.key}")
                return True
            else:
                logger.warning(f"锁已被其他进程持有或已过期: {self.key}")
                return False
                
        except Exception as e:
            logger.error(f"释放锁失败: {self.key}, 错误: {e}")
            return False
    
    async def extend(self, extra_time: int = 10) -> bool:
        """
        延长锁的超时时间
        
        Args:
            extra_time: 延长的时间（秒）
        
        Returns:
            是否成功延长
        """
        if not self._locked:
            return False
        
        try:
            # 使用 Lua 脚本安全地延长锁时间
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            result = await redis_client.redis.eval(
                lua_script,
                1,
                self.key,
                self.identifier,
                str(self.timeout + extra_time)
            )
            
            if result:
                logger.debug(f"成功延长锁: {self.key}, 延长 {extra_time} 秒")
                return True
            return False
            
        except Exception as e:
            logger.error(f"延长锁失败: {self.key}, 错误: {e}")
            return False
    
    async def __aenter__(self):
        """上下文管理器入口"""
        if await self.acquire():
            return self
        raise RuntimeError(f"无法获取锁: {self.key}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.release()


class ConversationLock:
    """会话锁（基于分布式锁的便捷包装）"""
    
    @staticmethod
    async def acquire_conversation_lock(conversation_id: str, timeout: int = 30) -> Optional[DistributedLock]:
        """
        获取会话锁
        
        Args:
            conversation_id: 会话ID
            timeout: 超时时间
        
        Returns:
            分布式锁对象，获取失败返回 None
        """
        lock = DistributedLock(
            key=f"conversation:{conversation_id}",
            timeout=timeout,
            retry_times=5,
            retry_delay=0.2
        )
        
        if await lock.acquire():
            return lock
        return None
    
    @staticmethod
    def with_conversation_lock(conversation_id: str, timeout: int = 30):
        """
        会话锁装饰器（用于 async with）
        
        Usage:
            async with ConversationLock.with_conversation_lock(conv_id):
                # 在锁保护下的操作
                pass
        """
        return DistributedLock(
            key=f"conversation:{conversation_id}",
            timeout=timeout,
            retry_times=5,
            retry_delay=0.2
        )
