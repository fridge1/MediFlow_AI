"""
自定义异常类
"""
from typing import Any, Optional


class BaseAPIException(Exception):
    """API 基础异常"""
    def __init__(
        self, 
        message: str = "Internal server error",
        status_code: int = 500,
        detail: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class UnauthorizedException(BaseAPIException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(BaseAPIException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问"):
        super().__init__(message=message, status_code=403)


class NotFoundException(BaseAPIException):
    """资源未找到异常"""
    def __init__(self, message: str = "资源未找到"):
        super().__init__(message=message, status_code=404)


class BadRequestException(BaseAPIException):
    """错误请求异常"""
    def __init__(self, message: str = "错误的请求", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=400, detail=detail)


class ConflictException(BaseAPIException):
    """冲突异常"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message=message, status_code=409)


class RateLimitException(BaseAPIException):
    """限流异常"""
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message=message, status_code=429)


class AIServiceException(BaseAPIException):
    """AI 服务异常"""
    def __init__(self, message: str = "AI 服务调用失败", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=500, detail=detail)

