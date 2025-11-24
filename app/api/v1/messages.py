"""
消息管理 API
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json

from app.core.database import get_db
from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse
from app.services.message_service import MessageService
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/conversations/{conv_id}/messages", tags=["消息管理"])


@router.post("", response_model=dict)
async def send_message(
    conv_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取 AI 响应（同步）
    
    支持三级配置优先级：
    1. 请求级别：直接在请求中指定 model_provider 和 model_name
    2. 应用模板级别：通过 use_application_config 引用应用配置
    3. 用户默认级别：使用用户的默认模型配置
    """
    user_msg, assistant_msg = await MessageService.send_message_and_get_response(
        db, conv_id, current_user.id, message_data, stream=False
    )
    await db.commit()
    
    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg
    }


@router.post("/stream")
async def send_message_stream(
    conv_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取 AI 响应（流式）
    
    使用 Server-Sent Events (SSE) 返回流式响应
    """
    
    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 获取流式响应
            stream = await MessageService.send_message_and_get_response(
                db, conv_id, current_user.id, message_data, stream=True
            )
            
            async for chunk in stream:
                # 格式化为 SSE 格式
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
            
            # 提交数据库事务
            await db.commit()
            
        except Exception as e:
            # 发送错误信息
            error_data = json.dumps({
                "error": str(e),
                "done": True
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 单独的消息管理路由
message_router = APIRouter(prefix="/messages", tags=["消息管理"])


@message_router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单条消息详情
    """
    message = await MessageService.get_message_by_id(db, message_id, current_user.id)
    if not message:
        from app.utils.exceptions import NotFoundException
        raise NotFoundException("消息不存在")
    return message


@message_router.put("/{message_id}/feedback", response_model=MessageResponse)
async def update_message_feedback(
    message_id: UUID,
    feedback_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新消息反馈（点赞/点踩）
    """
    message = await MessageService.update_message_feedback(
        db, message_id, current_user.id, feedback_data
    )
    await db.commit()
    return message


@message_router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除消息
    """
    await MessageService.delete_message(db, message_id, current_user.id)
    await db.commit()
    return {"message": "消息已删除"}

