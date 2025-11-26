"""
Pytest 配置和共享 fixtures
"""
import os
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# 为测试环境设置必要的环境变量（使用 Postgres 服务，而非本地 SQLite 文件）
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "0" * 32)
os.environ.setdefault("JWT_SECRET_KEY", "jwt-test-secret")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://medical_user:medical_pass@localhost:5432/medical_db",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core import redis_client as redis_module
from app.models.knowledge import KBItem


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.hash = {}
    async def connect(self):
        return None
    async def close(self):
        return None
    async def get(self, key: str):
        return self.store.get(key)
    async def set(self, key: str, value: str, expire: int | None = None):
        self.store[key] = value
    async def delete(self, key: str):
        self.store.pop(key, None)
    async def exists(self, key: str) -> bool:
        return key in self.store
    async def incr(self, key: str) -> int:
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val
    async def expire(self, key: str, seconds: int):
        return None
    async def lpush(self, key: str, *values):
        lst = self.store.setdefault(key, [])
        for v in values:
            lst.insert(0, v)
    async def lrange(self, key: str, start: int, end: int):
        lst = self.store.get(key, [])
        if end == -1:
            end = len(lst) - 1
        return lst[start:end+1]
    async def ltrim(self, key: str, start: int, end: int):
        lst = self.store.get(key, [])
        self.store[key] = lst[start:end+1]
    async def hset(self, name: str, key: str, value: str):
        h = self.hash.setdefault(name, {})
        h[key] = value
    async def hget(self, name: str, key: str):
        return self.hash.get(name, {}).get(key)
    async def hgetall(self, name: str) -> dict:
        return dict(self.hash.get(name, {}))


# 测试数据库 URL（指向 Postgres 的测试库）
# 注意：需要在 Postgres 中存在 medical_test_db 数据库
TEST_DATABASE_URL = settings.DATABASE_URL.replace("medical_db", "medical_test_db")

# 创建测试引擎
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# 使用 pytest-asyncio 默认事件循环


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """获取测试客户端"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    fake = FakeRedis()
    redis_module.redis_client = fake
    from app.services import token_service as ts
    ts.redis_client = fake
    from app.middleware import rate_limiter as rl
    rl.redis_client = fake
    from app.services import cache_service as cs
    cs.redis_client = fake
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
