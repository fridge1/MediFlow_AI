import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON

from app.core.database import Base


class KBItem(Base):
    __tablename__ = "kb_items"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection = Column(String(255), index=True, nullable=False)
    backend_pk = Column(String(64), index=True, nullable=False)
    text = Column(Text, nullable=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
