"""
模型配置服务
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate
from app.core.security import api_key_encryption
from app.services.cache_service import UserCache
from app.utils.exceptions import NotFoundException, ConflictException


class ModelConfigService:
    """模型配置服务"""
    
    @staticmethod
    async def create_model_config(
        db: AsyncSession, 
        user_id: UUID, 
        config_data: ModelConfigCreate
    ) -> ModelConfig:
        """创建模型配置"""
        # 检查是否已存在相同的配置
        result = await db.execute(
            select(ModelConfig).where(
                and_(
                    ModelConfig.user_id == user_id,
                    ModelConfig.provider == config_data.provider,
                    ModelConfig.model_name == config_data.model_name
                )
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("该模型配置已存在")
        
        # 如果设置为默认，取消其他默认配置
        if config_data.is_default:
            await ModelConfigService._unset_default(db, user_id, config_data.provider)
        
        # 加密 API Key
        encrypted_key = api_key_encryption.encrypt(config_data.api_key)
        
        db_config = ModelConfig(
            user_id=user_id,
            provider=config_data.provider,
            model_name=config_data.model_name,
            api_key=encrypted_key,
            api_base=config_data.api_base,
            is_default=config_data.is_default,
            is_active=config_data.is_active,
            config=config_data.config
        )
        db.add(db_config)
        await db.flush()
        await db.refresh(db_config)
        
        return db_config
    
    @staticmethod
    async def get_model_config_by_id(
        db: AsyncSession, 
        config_id: UUID, 
        user_id: UUID
    ) -> Optional[ModelConfig]:
        """获取模型配置"""
        result = await db.execute(
            select(ModelConfig).where(
                and_(
                    ModelConfig.id == config_id,
                    ModelConfig.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_model_configs(
        db: AsyncSession, 
        user_id: UUID,
        provider: Optional[str] = None
    ) -> List[ModelConfig]:
        """获取用户的模型配置列表"""
        query = select(ModelConfig).where(ModelConfig.user_id == user_id)
        
        if provider:
            query = query.where(ModelConfig.provider == provider)
        
        query = query.order_by(ModelConfig.is_default.desc(), ModelConfig.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_default_model_config(
        db: AsyncSession, 
        user_id: UUID,
        provider: Optional[str] = None
    ) -> Optional[ModelConfig]:
        """获取用户的默认模型配置（带缓存）"""
        # 尝试从缓存获取
        cached_config = await UserCache.get_default_model_config(user_id)
        if cached_config and (not provider or cached_config.get("provider") == provider):
            # 从缓存构造对象（简化版）
            config = ModelConfig(**cached_config)
            return config
        
        # 从数据库查询
        query = select(ModelConfig).where(
            and_(
                ModelConfig.user_id == user_id,
                ModelConfig.is_default == True,
                ModelConfig.is_active == True
            )
        )
        
        if provider:
            query = query.where(ModelConfig.provider == provider)
        
        result = await db.execute(query)
        config = result.scalar_one_or_none()
        
        # 缓存结果
        if config:
            config_dict = {
                "id": str(config.id),
                "user_id": str(config.user_id),
                "provider": config.provider,
                "model_name": config.model_name,
                "api_key": config.api_key,
                "api_base": config.api_base,
                "is_default": config.is_default,
                "is_active": config.is_active,
                "config": config.config
            }
            await UserCache.set_default_model_config(user_id, config_dict)
        
        return config
    
    @staticmethod
    async def update_model_config(
        db: AsyncSession, 
        config_id: UUID, 
        user_id: UUID, 
        config_data: ModelConfigUpdate
    ) -> ModelConfig:
        """更新模型配置"""
        config = await ModelConfigService.get_model_config_by_id(db, config_id, user_id)
        if not config:
            raise NotFoundException("模型配置不存在")
        
        update_data = config_data.dict(exclude_unset=True)
        
        # 如果更新 API Key，需要加密
        if "api_key" in update_data:
            update_data["api_key"] = api_key_encryption.encrypt(update_data["api_key"])
        
        # 如果设置为默认，取消其他默认配置
        if update_data.get("is_default"):
            await ModelConfigService._unset_default(db, user_id, config.provider)
        
        for key, value in update_data.items():
            setattr(config, key, value)
        
        await db.flush()
        await db.refresh(config)
        
        # 清除缓存
        await UserCache.clear_default_model_config(user_id)
        
        return config
    
    @staticmethod
    async def delete_model_config(
        db: AsyncSession, 
        config_id: UUID, 
        user_id: UUID
    ) -> bool:
        """删除模型配置"""
        config = await ModelConfigService.get_model_config_by_id(db, config_id, user_id)
        if not config:
            raise NotFoundException("模型配置不存在")
        
        await db.delete(config)
        await db.flush()
        
        return True
    
    @staticmethod
    async def get_decrypted_api_key(config: ModelConfig) -> str:
        """获取解密后的 API Key"""
        return api_key_encryption.decrypt(config.api_key)
    
    @staticmethod
    async def _unset_default(db: AsyncSession, user_id: UUID, provider: str):
        """取消该提供商的其他默认配置"""
        result = await db.execute(
            select(ModelConfig).where(
                and_(
                    ModelConfig.user_id == user_id,
                    ModelConfig.provider == provider,
                    ModelConfig.is_default == True
                )
            )
        )
        configs = result.scalars().all()
        for config in configs:
            config.is_default = False
        await db.flush()
