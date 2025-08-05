from fastapi import Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from app.features.aichat.atchat_service import AichatService
from app.schemas.response_schema import BaseResponse
from app.schemas.ai_schema.message_schema import MessageIncrementalResponse, IncrementalParams
from app.schemas.ai_schema.chat_schema import ChatListPaginatedResponse, ChatStartRequest, ChatStartResponse, ChatStreamRequest, PaginationParams, ChatIncrementalParams, ChatIncrementalResponse
from app.features.user.user_service import UserService
from datetime import datetime
import math
from app.entities.user_entity import User
from datetime import UTC
class AichatController:
    """
    AI聊天控制器，处理HTTP请求和响应
    """
    
    @staticmethod
    def get_sse_headers() -> Dict[str, str]:
        """获取SSE响应头"""
        return {
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream',
            'X-Accel-Buffering': 'no',  # 禁用Nginx缓冲
        }
    
    @staticmethod
    async def stream_chat(
        request: Request,
        current_user: User,
        data: ChatStreamRequest
    ) -> StreamingResponse:
        """
        处理AI聊天流请求
        
        Args:
            request: FastAPI请求对象
            prompt: 用户提问
            user_id: 用户ID
            model: 模型名称
            
        Returns:
            StreamingResponse: 流式响应对象
        """
        prompt = data.prompt
        chat_id = data.chat_id

        if not prompt:
            raise ValueError("提示语不能为空")
            
        # 创建流式响应
        return StreamingResponse(
            AichatService.stream_chat(request, prompt, current_user, chat_id),
            media_type="text/event-stream",
            headers=AichatController.get_sse_headers()
        )

    @staticmethod
    async def live_card_stream_chat(
        request: Request,
        current_user: User,
        data: ChatStreamRequest
    ) -> StreamingResponse:
        """
        处理AI聊天流请求
        
        Args:
            request: FastAPI请求对象
            prompt: 用户提问
            user_id: 用户ID
            model: 模型名称
            
        Returns:
            StreamingResponse: 流式响应对象
        """
        prompt = data.prompt
        chat_id = data.chat_id

        if not prompt:
            raise ValueError("提示语不能为空")
            
        # 创建流式响应
        return StreamingResponse(
            AichatService.live_card_stream_chat(request, prompt, current_user, chat_id),
            media_type="text/event-stream",
            headers=AichatController.get_sse_headers()
        )

    @staticmethod
    async def start_chat(
        current_user: User,
        data: ChatStartRequest
    ) -> ChatStartResponse:
        chat_id = data.chat_id
        live_card_id = data.live_card_id
        chat_start_response = await AichatService.start_chat(chat_id, live_card_id, current_user)
        return chat_start_response
    

    @staticmethod
    async def get_chat_messages_incremental(
        current_user: User,
        chat_id: str,
        incremental_params: IncrementalParams
    ) -> MessageIncrementalResponse:
        """
        增量获取聊天消息
        
        Args:
            direction: "after" 获取新消息(用于增量更新), "before" 获取历史消息(用于向上滚动加载)
        """
        
        return await AichatService.get_chat_messages_incremental(
            current_user,
            chat_id=chat_id,
            incremental_params=incremental_params
        )
    
    
    @staticmethod
    async def get_user_all_chats(
        current_user: User,
        pagination: PaginationParams
    ) -> ChatListPaginatedResponse:
        chats, total = await AichatService.get_user_all_chats(current_user, pagination)
        return ChatListPaginatedResponse(
            items=chats,
            total=total,
            page=1,
            page_size=10,
            total_pages=math.ceil(total / 10)
        )
    
    @staticmethod
    async def chats_list(
        current_user: User,
        incremental_params: ChatIncrementalParams
    ) -> ChatIncrementalResponse:
        """处理获取收藏列表请求（带分页和过滤）"""
        chats_list, has_more, total = await AichatService.chats_list(current_user, incremental_params)
        return ChatIncrementalResponse(
            items=chats_list,
            has_more=has_more,
            last_id=chats_list[-1].get("_id") if chats_list else None,
            last_timestamp=chats_list[-1].get("created_at") if chats_list else None,
            total=total
        )