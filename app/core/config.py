"""
应用配置管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Medical AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    
    # 数据库配置
    DATABASE_URL: str
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Milvus 配置(可选)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: Optional[str] = None
    MILVUS_PASSWORD: Optional[str] = None
    
    # JWT 配置
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    
    # AI 模型配置(系统默认,用户可覆盖)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    DASHSCOPE_API_KEY: Optional[str] = None
    
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    
    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"
    
    # Embedding 配置
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_PROVIDER: Optional[str] = None
    
    # 其他配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_KB: bool = False
    VECTOR_BACKEND: str = "memory"  # memory | milvus
    CELERY_ALWAYS_EAGER: bool = True
    KB_CALLBACK_SECRET: str = "kb-callback-secret"
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
