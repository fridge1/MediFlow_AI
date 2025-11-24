"""
全局错误处理中间件
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.utils.exceptions import BaseAPIException
from app.utils.logger import logger


async def api_exception_handler(request: Request, exc: BaseAPIException):
    """处理自定义 API 异常"""
    logger.error(f"API 异常: {exc.message}, 详情: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "detail": exc.detail
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求数据验证失败",
            "detail": exc.errors()
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """处理数据库异常"""
    logger.error(f"数据库错误: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败",
            "detail": str(exc) if logger.level == "DEBUG" else None
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.exception(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if logger.level == "DEBUG" else None
        }
    )

