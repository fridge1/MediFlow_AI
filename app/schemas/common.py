"""
通用 Schema
"""
from typing import Optional, Any, List
from pydantic import BaseModel, ConfigDict


class ResponseBase(BaseModel):
    """统一响应基类"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(from_attributes=True)

