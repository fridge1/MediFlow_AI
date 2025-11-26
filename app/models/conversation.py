"""
会话模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from app.core.database import Base, GUID
from sqlalchemy.orm import relationship



class Conversation(Base):
    """会话表 - 独立的对话容器"""
    __tablename__ = "conversations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255))
    status = Column(String(50), default="active", nullable=False, index=True)  # active, archived, deleted
    summary = Column(Text)
    
    # 会话元数据(可存储关联的应用ID等扩展信息)
    conv_metadata = Column(JSON, default=dict)
    message_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, index=True)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, status={self.status})>"
