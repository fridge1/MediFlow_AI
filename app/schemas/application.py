"""
应用相关 Schema
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class ApplicationBase(BaseModel):
    """应用基础模型"""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    app_type: str = "chatbot"
    
    model_provider: str = "openai"
    model_name: str = "gpt-3.5-turbo"
    model_parameters: Dict[str, Any] = {}
    
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    opening_statement: Optional[str] = None
    
    max_conversation_length: int = 10
    enable_context: bool = True
    model_config = ConfigDict(protected_namespaces=())


class ApplicationCreate(ApplicationBase):
    """应用创建模型"""
    pass


class ApplicationUpdate(BaseModel):
    """应用更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    app_type: Optional[str] = None
    
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    opening_statement: Optional[str] = None
    
    max_conversation_length: Optional[int] = None
    enable_context: Optional[bool] = None


class ApplicationInDB(ApplicationBase):
    """数据库中的应用模型"""
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(ApplicationInDB):
    """应用响应模型"""
    pass


class ApplicationPublish(BaseModel):
    """应用发布请求"""
    pass
