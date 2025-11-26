"""
FastAPI 应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import redis_client
from app.utils.logger import logger
from app.utils.exceptions import BaseAPIException
from app.middleware.error_handler import (
    api_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from app.middleware.rate_limiter import RateLimiterMiddleware

# 导入路由
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.applications import router as applications_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.messages import router as messages_router, message_router
from app.api.v1.models import router as models_router
from app.api.v1.knowledge import router as knowledge_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("应用启动中...")
    
    # 初始化数据库
    # await init_db()  # 注释掉，使用 Alembic 管理迁移
    logger.info("数据库连接已建立")
    
    # 初始化 Redis
    await redis_client.connect()
    logger.info("Redis 连接已建立")
    
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动成功")
    
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")
    
    # 关闭数据库连接
    await close_db()
    logger.info("数据库连接已关闭")
    
    # 关闭 Redis 连接
    await redis_client.close()
    logger.info("Redis 连接已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="类似 Dify 的 AI 应用管理和会话管理平台",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置限流中间件
app.add_middleware(RateLimiterMiddleware, rate_limit=settings.RATE_LIMIT_PER_MINUTE)


# 注册异常处理器
app.add_exception_handler(BaseAPIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# 注册路由
@app.get("/", tags=["根"])
async def root():
    """API 根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# 注册 v1 API 路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(message_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
