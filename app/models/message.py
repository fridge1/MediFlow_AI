"""
消息模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 消息内容
    role = Column(String(50), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # 模型信息(每条消息可使用不同模型)
    model_provider = Column(String(50))  # openai, qwen, deepseek, siliconflow
    model_name = Column(String(100))
    model_config = Column(JSON, default=dict)  # 本次使用的模型参数
    
    # Token 统计
    token_count = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    
    # 反馈
    feedback = Column(String(50))  # like, dislike, null
    feedback_comment = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"

