from fastapi import APIRouter, Request, Body, Query, Depends
from app.features.aichat.aichat_controller import AichatController
from app.schemas.response_schema import BaseResponse
from fastapi.security import HTTPBearer
from app.schemas.ai_schema.chat_schema import ChatStreamRequest, ChatStartRequest, ChatStartResponse, PaginationParams, ChatListPaginatedResponse, ChatIncrementalParams, ChatIncrementalResponse
from app.schemas.ai_schema.message_schema import MessageIncrementalResponse, IncrementalParams
from app.middleware.auth_middleware import get_current_user_optional, get_current_user_required
from app.entities.user_entity import User
token_auth_scheme = HTTPBearer()
router = APIRouter(prefix="/aichat", tags=["聊天"])

@router.post("/stream")
async def aichat_stream_post(
    request: Request,
    current_user: User = Depends(get_current_user_required),
    data: ChatStreamRequest = Body(...)
):
    """
    流式聊天API (POST方法)
    
    Args:
        request: FastAPI请求对象
        data: 请求体，包含用户提问等数据
    
    Returns:
        StreamingResponse: 包含AI回复的事件流
    """
        
    return await AichatController.stream_chat(request, current_user, data)

@router.post("/live_card_stream")
async def live_card_stream_post(
    request: Request,
    current_user: User = Depends(get_current_user_required),
    data: ChatStreamRequest = Body(...)
):
    return await AichatController.live_card_stream_chat(request, current_user, data)

@router.post("/start", response_model=BaseResponse[ChatStartResponse])
async def start_chat(
    current_user: User = Depends(get_current_user_required),
    data: ChatStartRequest = Body(...)
):
    data = await AichatController.start_chat(current_user, data)
    return BaseResponse.success(data=data)

@router.get("/messages", response_model=BaseResponse[MessageIncrementalResponse])
async def get_chat_history_messages(
    current_user: User = Depends(get_current_user_required),
    chat_id: str = Query(..., description="聊天ID"),
    incremental_params: IncrementalParams = Depends()
):
    """
    增量获取聊天消息
    
    Args:
        chat_id: 聊天ID
        last_id: 最后一条消息ID（用于增量获取）
        last_timestamp: 最后一条消息时间戳
        limit: 限制数量
        direction: 获取方向，before获取历史消息，after获取新消息
    """
    result = await AichatController.get_chat_messages_incremental(
        current_user, chat_id, incremental_params
    )
    return BaseResponse.success(data=result)


@router.get("/chats")
async def get_user_all_chats(
    current_user: User = Depends(get_current_user_required),
    pagination: PaginationParams = Depends()
):
    data = await AichatController.get_user_all_chats(current_user, pagination)
    return BaseResponse.success(data=data)

@router.get("/chats_list", response_model=BaseResponse[ChatIncrementalResponse])
async def chats_list(
    current_user: User = Depends(get_current_user_required),
    incremental_params: ChatIncrementalParams = Depends(ChatIncrementalParams)
):
    data = await AichatController.chats_list(current_user, incremental_params)
    return BaseResponse.success(data=data)

