"""
模型配置模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelConfig(Base):
    """模型配置表"""
    __tablename__ = "model_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # openai, qwen, deepseek, siliconflow
    model_name = Column(String(100), nullable=False)
    api_key = Column(String(500), nullable=False)  # 加密存储
    api_base = Column(String(255))
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="model_configs")
    
    # 唯一约束: 每个用户的同一提供商和模型名称组合唯一
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', 'model_name', name='uq_user_provider_model'),
    )
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, provider={self.provider}, model={self.model_name}, is_default={self.is_default})>"

