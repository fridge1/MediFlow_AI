"""
数据库连接和会话管理
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .config import settings


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite") or "+aiosqlite" in url

# 创建异步引擎（兼容 sqlite 与 postgres）
if _is_sqlite(settings.DATABASE_URL):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()

# Ensure models are registered for metadata operations
try:
    from app.models import User, Application, Conversation, Message, ModelConfig, KBItem  # noqa: F401
except Exception:
    pass


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)
    def process_result_value(self, value, dialect):
        return value


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    用作 FastAPI 的依赖项
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
