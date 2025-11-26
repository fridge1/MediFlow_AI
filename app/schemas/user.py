"""
用户相关 Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from uuid import UUID


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """用户响应模型"""
    pass


class Token(BaseModel):
    """Token 模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token 数据"""
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
