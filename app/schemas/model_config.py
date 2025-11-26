"""
模型配置相关 Schema
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from uuid import UUID


class ModelConfigBase(BaseModel):
    """模型配置基础模型"""
    provider: str = Field(..., pattern="^(openai|qwen|deepseek|siliconflow)$")
    model_name: str = Field(..., min_length=1, max_length=100)
    api_base: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(protected_namespaces=())


class ModelConfigCreate(ModelConfigBase):
    """模型配置创建模型"""
    api_key: str = Field(..., min_length=1)


class ModelConfigUpdate(BaseModel):
    """模型配置更新模型"""
    api_key: Optional[str] = Field(None, min_length=1)
    api_base: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class ModelConfigInDB(ModelConfigBase):
    """数据库中的模型配置(不返回api_key)"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelConfigResponse(ModelConfigInDB):
    """模型配置响应模型"""
    api_key_masked: str = "sk-***"  # 掩码后的key
