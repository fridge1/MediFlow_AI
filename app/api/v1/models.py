"""
模型配置管理 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse
)
from app.services.model_config_service import ModelConfigService
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/models", tags=["模型配置"])


@router.post("", response_model=ModelConfigResponse, status_code=201)
async def create_model_config(
    config_data: ModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    添加模型配置
    
    支持的提供商：openai, qwen, deepseek, siliconflow
    """
    config = await ModelConfigService.create_model_config(
        db, current_user.id, config_data
    )
    await db.commit()
    
    # 不返回完整的 API Key
    response = ModelConfigResponse.from_orm(config)
    return response


@router.get("")
async def list_model_configs(
    provider: Optional[str] = Query(None, regex="^(openai|qwen|deepseek|siliconflow)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取模型配置列表
    """
    configs = await ModelConfigService.get_user_model_configs(
        db, current_user.id, provider
    )
    
    # 不返回完整的 API Key
    return {
        "items": [
            {
                **ModelConfigResponse.from_orm(config).dict(),
                "api_key_masked": f"{config.api_key[:8]}..." if len(config.api_key) > 8 else "***"
            }
            for config in configs
        ]
    }


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取模型配置详情
    """
    config = await ModelConfigService.get_model_config_by_id(
        db, config_id, current_user.id
    )
    if not config:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("模型配置不存在")
    
    response = ModelConfigResponse.from_orm(config)
    return response


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: UUID,
    config_data: ModelConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新模型配置
    """
    config = await ModelConfigService.update_model_config(
        db, config_id, current_user.id, config_data
    )
    await db.commit()
    
    response = ModelConfigResponse.from_orm(config)
    return response


@router.delete("/{config_id}")
async def delete_model_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除模型配置
    """
    await ModelConfigService.delete_model_config(db, config_id, current_user.id)
    await db.commit()
    return {"message": "模型配置已删除"}


@router.get("/default/config")
async def get_default_model_config(
    provider: Optional[str] = Query(None, regex="^(openai|qwen|deepseek|siliconflow)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的默认模型配置
    """
    config = await ModelConfigService.get_default_model_config(
        db, current_user.id, provider
    )
    if not config:
        return {"message": "未设置默认模型配置"}
    
    return ModelConfigResponse.from_orm(config)

