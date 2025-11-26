"""
消息相关 Schema
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from uuid import UUID


class MessageBase(BaseModel):
    """消息基础模型"""
    content: str = Field(..., min_length=1)
    role: str = Field(default="user", pattern="^(user|assistant|system)$")
    model_config = ConfigDict(protected_namespaces=())


class MessageCreate(MessageBase):
    """消息创建模型"""
    # 可选的模型配置(请求级别)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_params: Optional[Dict[str, Any]] = Field(None, validation_alias="model_config", serialization_alias="model_config")
    
    # 可选引用应用配置
    use_application_config: Optional[str] = None  # application_id


class MessageUpdate(BaseModel):
    """消息更新模型"""
    feedback: Optional[str] = Field(None, pattern="^(like|dislike)$")
    feedback_comment: Optional[str] = None


class MessageInDB(MessageBase):
    """数据库中的消息模型"""
    id: UUID
    conversation_id: UUID
    model_provider: Optional[str]
    model_name: Optional[str]
    model_params: Dict[str, Any] = Field(default_factory=dict, validation_alias="model_config", serialization_alias="model_config")
    token_count: int
    prompt_tokens: int
    completion_tokens: int
    feedback: Optional[str]
    feedback_comment: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(MessageInDB):
    """消息响应模型"""
    pass


class StreamMessageChunk(BaseModel):
    """流式消息块"""
    content: str
    done: bool = False
    
    # 当done=True时包含完整消息信息
    message_id: Optional[UUID] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    token_count: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
