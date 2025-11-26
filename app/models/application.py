"""
应用模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from app.core.database import Base, GUID
from sqlalchemy.orm import relationship



class Application(Base):
    """应用配置模板表"""
    __tablename__ = "applications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    icon = Column(String(255))
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, published
    app_type = Column(String(50), default="chatbot", nullable=False)  # chatbot, completion, agent
    
    # 模型配置
    model_provider = Column(String(50), default="openai")  # openai, qwen, deepseek, siliconflow
    model_name = Column(String(100), default="gpt-3.5-turbo")
    model_parameters = Column(JSON, default=dict)  # temperature, max_tokens, etc.
    
    # 提示词配置
    system_prompt = Column(Text)
    user_prompt_template = Column(Text)
    opening_statement = Column(Text)  # 开场白
    
    # 其他配置
    max_conversation_length = Column(Integer, default=10)
    enable_context = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="applications")
    
    def __repr__(self):
        return f"<Application(id={self.id}, name={self.name}, status={self.status})>"
