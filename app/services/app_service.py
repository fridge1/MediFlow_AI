"""
应用服务
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services.cache_service import ApplicationCache
from app.utils.exceptions import NotFoundException, ForbiddenException


class ApplicationService:
    """应用服务"""
    
    @staticmethod
    async def create_application(
        db: AsyncSession, 
        user_id: UUID, 
        app_data: ApplicationCreate
    ) -> Application:
        """创建应用"""
        db_app = Application(
            **app_data.dict(),
            user_id=user_id
        )
        db.add(db_app)
        await db.flush()
        await db.refresh(db_app)
        
        return db_app
    
    @staticmethod
    async def get_application_by_id(
        db: AsyncSession, 
        app_id: UUID, 
        user_id: Optional[UUID] = None
    ) -> Optional[Application]:
        """获取应用详情"""
        query = select(Application).where(Application.id == app_id)
        if user_id:
            query = query.where(Application.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_applications(
        db: AsyncSession, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> tuple[List[Application], int]:
        """获取用户的应用列表"""
        query = select(Application).where(Application.user_id == user_id)
        
        if status:
            query = query.where(Application.status == status)
        
        # 获取总数
        count_query = select(Application).where(Application.user_id == user_id)
        if status:
            count_query = count_query.where(Application.status == status)
        count_result = await db.execute(count_query)
        total = len(count_result.all())
        
        # 分页查询
        query = query.order_by(Application.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        applications = result.scalars().all()
        
        return list(applications), total
    
    @staticmethod
    async def update_application(
        db: AsyncSession, 
        app_id: UUID, 
        user_id: UUID, 
        app_data: ApplicationUpdate
    ) -> Application:
        """更新应用"""
        app = await ApplicationService.get_application_by_id(db, app_id, user_id)
        if not app:
            raise NotFoundException("应用不存在或无权访问")
        
        update_data = app_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(app, key, value)
        
        await db.flush()
        await db.refresh(app)
        
        # 清除缓存
        await ApplicationCache.clear_config(app_id)
        
        return app
    
    @staticmethod
    async def delete_application(
        db: AsyncSession, 
        app_id: UUID, 
        user_id: UUID
    ) -> bool:
        """删除应用"""
        app = await ApplicationService.get_application_by_id(db, app_id, user_id)
        if not app:
            raise NotFoundException("应用不存在或无权访问")
        
        await db.delete(app)
        await db.flush()
        
        return True
    
    @staticmethod
    async def publish_application(
        db: AsyncSession, 
        app_id: UUID, 
        user_id: UUID
    ) -> Application:
        """发布应用"""
        app = await ApplicationService.get_application_by_id(db, app_id, user_id)
        if not app:
            raise NotFoundException("应用不存在或无权访问")
        
        app.status = "published"
        await db.flush()
        await db.refresh(app)
        
        return app
    
    @staticmethod
    async def get_application_config(
        db: AsyncSession, 
        app_id: UUID
    ) -> Optional[dict]:
        """获取应用的模型配置（带缓存）"""
        # 尝试从缓存获取
        cached_config = await ApplicationCache.get_config(app_id)
        if cached_config:
            return cached_config
        
        # 从数据库查询
        app = await ApplicationService.get_application_by_id(db, app_id)
        if not app:
            return None
        
        config = {
            "model_provider": app.model_provider,
            "model_name": app.model_name,
            "model_config": app.model_parameters,
            "system_prompt": app.system_prompt,
            "max_conversation_length": app.max_conversation_length,
            "enable_context": app.enable_context
        }
        
        # 缓存配置
        await ApplicationCache.set_config(app_id, config)
        
        return config

