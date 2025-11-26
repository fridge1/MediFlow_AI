"""
会话相关 Schema
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from uuid import UUID

if TYPE_CHECKING:
    from .message import MessageResponse


class ConversationBase(BaseModel):
    """会话基础模型"""
    title: Optional[str] = Field(None, max_length=255)
    conv_metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata")
    model_config = ConfigDict(populate_by_name=True)


class ConversationCreate(ConversationBase):
    """会话创建模型"""
    pass


class ConversationUpdate(BaseModel):
    """会话更新模型"""
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|archived|deleted)$")
    summary: Optional[str] = None
    conv_metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata")
    model_config = ConfigDict(populate_by_name=True)


class ConversationInDB(ConversationBase):
    """数据库中的会话模型"""
    id: UUID
    user_id: UUID
    status: str
    summary: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(ConversationInDB):
    """会话响应模型"""
    pass


class ConversationWithMessages(ConversationResponse):
    """带消息的会话响应"""
    messages: List["MessageResponse"] = []
