from typing import Dict, Any, AsyncGenerator, Optional, Tuple
from fastapi import Request
import json
from app.utils.logger_service import logger
from app.schemas.ai_schema.streaming_schema import ChatMessage, TextContent, MessageCompletionStatus, Message
from app.infrastructure.ai.sse_client import SSEClient
from uuid import UUID, uuid4
from typing import List
from app.crud import chat_crud, message_crud, live_card_crud
from app.schemas.ai_schema.chat_schema import ChatFilter, ChatCreate, PaginationParams, ChatListItemResponse, ChatStartResponse, ChatIncrementalParams, ChatIncrementalResponse
from app.schemas.ai_schema.message_schema import MessageCreate, MessageFilter, MessageResponse, IncrementalParams, MessageIncrementalResponse
from datetime import datetime, UTC
from app.entities.user_entity import User
from app.core.config import settings
import httpx
class AichatService:
    """
    AI聊天服务，处理与AI的通信逻辑
    """
    
    @staticmethod
    async def format_sse_event(data: Dict[str, Any]) -> str:
        """格式化SSE事件"""
        if data.get("created_at"):
            data["created_at"] = str(data["created_at"])
        json_data = json.dumps(data, ensure_ascii=False)
        return f"data: {json_data}\n\n"

    @staticmethod
    def convert_event_to_client_format(event: Any, message_id: str = None) -> Dict[str, Any]:
        """
        将SSE事件转换为MessageResponse对象
        
        Args:
            event: 从SSE客户端接收的事件
            message_id: 消息ID
            
        Returns:
            MessageResponse: MessageResponse对象
        """
        # 检查事件类型
        event_type = getattr(event, 'event_type', None)
        if not event_type:
            return {
                "message_id": message_id,
                "message_type": "error",
                "stream_status": "error",
                "role": "assistant",
                "message_content": "",
                "message_images": [],
                "delta": "Unknown event type",
                "created_at": str(datetime.now(UTC))
            }
            
        elif event_type == "response.chat_message.item.output_text.delta":
            # 流式文本增量
            delta_text = event.delta if hasattr(event, 'delta') else ""
            return {
                "message_id": message_id,
                "message_type": "text",
                "stream_status": "delta",
                "role": "assistant",
                "message_content": "",
                "message_images": [],
                "delta": delta_text,
                "created_at": str(datetime.now(UTC))
            }
            
        elif event_type == "response.chat_message.item.output_text.done":
            # 文本完成，包含完整内容
            complete_text = event.text if hasattr(event, 'text') else ""
            return {
                "message_id": message_id,
                "message_type": "text",
                "stream_status": "done",
                "role": "assistant",
                "message_content": complete_text,
                "message_images": [],
                "delta": "",
                "created_at": str(datetime.now(UTC))
            }
        
        # 默认返回
        return {
            "message_id": message_id,
            "message_type": "text",
            "stream_status": "default",
            "role": "assistant",
            "message_content": "",
            "message_images": [],
            "delta": "",
            "created_at": str(datetime.now(UTC))
        }

    
   
    @staticmethod
    async def stream_chat(
        request: Request,
        prompt: str,
        local_user: User,
        chat_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        从AI服务获取流式聊天响应
        
        Args:
            request: FastAPI请求对象
            prompt: 用户提问
            user_id: 用户ID
            model: 模型名称
            
        Yields:
            str: 格式化后的SSE事件
        """
        try:
            # 创建用户消息
            user_message = ChatMessage(
                role="user",
                items=[TextContent(text=prompt)],
                status=MessageCompletionStatus.COMPLETED
            )
            local_user_id = local_user.id
            session_id = uuid4()
            try:
                chat_info = await chat_crud.get_chat_by_id(chat_id)
                if not chat_info:
                    raise ValueError("聊天不存在")
                live_card_id = chat_info.participants["live_card"]
                user_message_id = str(uuid4())
                user_create_message = MessageCreate(id=user_message_id, chat_id=chat_id, sender_id=local_user_id, role="user", text=prompt, contents=[])
                await message_crud.create_and_add_to_chat(user_create_message, chat_id)
                user_input_message = {
                    "message_id": user_message_id,   
                    "message_type": "text",
                    "stream_status": "start",
                    "role": "user",
                    "message_content": prompt,
                    "message_images": [],
                    "delta": "",
                    "created_at": str(datetime.now(UTC))
                }
                yield await AichatService.format_sse_event(user_input_message)

                message_id = str(uuid4())
                # 使用async for正确迭代异步生成器
                async for event in SSEClient.stream_chat_events(
                    chat_id=chat_id,
                    session_id=session_id,
                    bot_id=live_card_id,
                    messages=[user_message]
                ):
                    # 转换事件为客户端可理解的格式
                    client_event = AichatService.convert_event_to_client_format(event, message_id)
                    event_type = getattr(event, 'event_type', None)
                    if client_event:
                        if event_type == "response.chat_message.item.output_text.delta":
                            yield await AichatService.format_sse_event(client_event)
                        if event_type == "response.chat_message.item.output_text.done":
                            bot_create_message = MessageCreate( id=message_id,
                                                                chat_id=chat_id,
                                                                sender_id=live_card_id,
                                                                role="assistant",
                                                                text=client_event["message_content"],
                                                                contents=[])
                            await message_crud.create_and_add_to_chat(bot_create_message, chat_id)
                            yield await AichatService.format_sse_event(client_event)
            
            except Exception as e:
                logger.error(f"流式获取AI响应时出错: {str(e)}")
                error_response = MessageResponse(
                    message_id="",
                    message_type="error",
                    role="assistant",
                    message_content=f"AI service error: {str(e)}",
                    message_images=[],
                    delta="[ERROR]",
                    created_at=str(datetime.now(UTC))
                )
                yield await AichatService.format_sse_event(error_response.model_dump())
            
        except Exception as e:
            logger.error(f"AI聊天服务错误: {str(e)}")
            system_error_response = MessageResponse(
                message_id="",
                message_type="error",
                role="system",
                message_content=f"Error: {str(e)}",
                message_images=[],
                delta="[SYSTEM_ERROR]",
                created_at=str(datetime.now(UTC))
            )
            yield await AichatService.format_sse_event(system_error_response.model_dump())
    
    @staticmethod
    async def live_card_stream_chat(
        request: Request,
        prompt: str,
        local_user: User,
        chat_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        从AI服务获取流式聊天响应
        
        Args:
            request: FastAPI请求对象
            prompt: 用户提问
            user_id: 用户ID
            model: 模型名称
            
        Yields:
            str: 格式化后的SSE事件
        """
        try:
            # 创建用户消息
            user_message = ChatMessage(
                role="user",
                items=[TextContent(text=prompt)],
                status=MessageCompletionStatus.COMPLETED
            )
            local_user_id = local_user.id
            session_id = uuid4()
            try:
                chat_info = await chat_crud.get_chat_by_id(chat_id)
                if not chat_info:
                    raise ValueError("聊天不存在")
                live_card_id = chat_info.participants["live_card"]
                live_card_info = await live_card_crud.get(live_card_id)
                if not live_card_info:
                    raise ValueError(f"话题{live_card_id}不存在")
                post_info = await post_crud.get(live_card_info.post_id)
                if not post_info:
                    raise ValueError(f"帖子{live_card_info.post_id}不存在")
                agent_info = await agent_crud.get(post_info.agent_id)
                if not agent_info:
                    raise ValueError(f"机器人{agent_info.agent_name}不存在")
                history_messages, _ = await message_crud.get_messages_incremental(
                    MessageFilter(chat_id=chat_id), IncrementalParams(limit=20)
                )
                history_messages_list = []
                for message in history_messages:
                    history_messages_list.append(ChatMessage(
                        role=message.role,
                        items=[TextContent(text=message.text)],
                        status=MessageCompletionStatus.COMPLETED
                    ))
                user_message_id = str(uuid4())
                user_create_message = MessageCreate(id=user_message_id, chat_id=chat_id, sender_id=local_user_id, role="user", text=prompt, contents=[])
                await message_crud.create_and_add_to_chat(user_create_message, chat_id)
                user_input_message = {
                    "message_id": user_message_id,   
                    "message_type": "text",
                    "stream_status": "start",
                    "role": "user",
                    "message_content": prompt,
                    "message_images": [],
                    "delta": "",
                    "created_at": str(datetime.now(UTC))
                }
                yield await AichatService.format_sse_event(user_input_message)

                message_id = str(uuid4())
                # 使用async for正确迭代异步生成器
                async for event in SSEClient.stream_live_card_chat_events(
                    chat_id=chat_id,
                    session_id=session_id,
                    bot_id=agent_info.id,
                    bot_name=agent_info.agent_name,
                    user_name=local_user.name,
                    focused_category=live_card_info.categories[0] if live_card_info.categories else "Information Tracker",
                    live_card_topic=live_card_info.topic_title,
                    live_card_content=json.dumps(live_card_info.metadata.get("ai_content", {})),
                    chat_history=history_messages_list,
                    user_input=user_message,
                    max_chat_history_size=20,
                    streamimg=True,
                ):
                    # 转换事件为客户端可理解的格式
                    client_event = AichatService.convert_event_to_client_format(event, message_id)
                    event_type = getattr(event, 'event_type', None)
                    if client_event:
                        if event_type == "response.chat_message.item.output_text.delta":
                            yield await AichatService.format_sse_event(client_event)
                        if event_type == "response.chat_message.item.output_text.done":
                            bot_create_message = MessageCreate( id=message_id,
                                                                chat_id=chat_id,
                                                                sender_id=live_card_id,
                                                                role="assistant",
                                                                text=client_event["message_content"],
                                                                contents=[])
                            await message_crud.create_and_add_to_chat(bot_create_message, chat_id)
                            yield await AichatService.format_sse_event(client_event)
            
            except Exception as e:
                logger.error(f"流式获取AI响应时出错: {str(e)}")
                error_response = MessageResponse(
                    message_id="",
                    message_type="error",
                    role="assistant",
                    message_content=f"AI service error: {str(e)}",
                    message_images=[],
                    delta="[ERROR]",
                    created_at=str(datetime.now(UTC))
                )
                yield await AichatService.format_sse_event(error_response.model_dump())
            
        except Exception as e:
            logger.error(f"AI聊天服务错误: {str(e)}")
            system_error_response = MessageResponse(
                message_id="",
                message_type="error",
                role="system",
                message_content=f"Error: {str(e)}",
                message_images=[],
                delta="[SYSTEM_ERROR]",
                created_at=str(datetime.now(UTC))
            )
            yield await AichatService.format_sse_event(system_error_response.model_dump())

    @staticmethod
    async def start_chat(
        chat_id: str,
        live_card_id: str,
        local_user: User
    ) -> ChatStartResponse:
        local_user_id = local_user.id
        # 优化后的逻辑
        if chat_id and chat_id != "-1":
            # chat_id优先级最高：有就查找，找不到就报错
            chat_result = await chat_crud.get_chat_by_id(chat_id)
            if not chat_result:
                raise ValueError("指定的聊天不存在")
            
            # 获取该聊天对应的agent信息
            live_card_info = await live_card_crud.get(chat_result.participants["live_card"])
            if not live_card_info:
                raise ValueError("聊天存在但关联的机器人已不存在")
                
        else:
            # 没有chat_id时，使用agent_id
            if not live_card_id:
                raise ValueError("聊天ID和live_card_id不能同时为空")
            
            # 验证live_card是否存在
            live_card_info = await live_card_crud.get(live_card_id)
            if not live_card_info:
                raise ValueError("指定的live_card不存在")
            post_info = await post_crud.get(live_card_info.post_id)
            agent_info = await agent_crud.get(post_info.agent_id)
            # 查找或创建chat
            chat_result = await chat_crud.get_chat_by_live_card_and_user(live_card_id, local_user_id)
            if not chat_result:
                logger.info(f"创建聊天: {live_card_id}")
                chat_result = await chat_crud.create(
                    ChatCreate(participants={"user": local_user_id, "live_card": live_card_id})
                )
                # 调用API获取欢迎消息
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        data = {
                            "bot_name": agent_info.agent_name,
                            "focused_category": live_card_info.categories[0] if live_card_info.categories else "Information Tracker",
                            "live_card_topic": live_card_info.topic_title,
                            "custom_style_instruction": None
                        }

                        response = await client.post(
                            f"{settings.AI_SERVICE_BASE_URL}/info_bot/live_card_post/generate_welcome_template",
                            headers={"Content-Type": "application/json"},
                            json = data
                        )
                        
                        if response.status_code == 200:
                            welcome_text = response.json().get("welcome_template", "Hi, I'm your AI assistant, how can I help you?")
                        else:
                            logger.error(f"获取欢迎消息模板失败: {response.status_code} - {response.text}")
                            welcome_text = "Hi, I'm your AI assistant, how can I help you?"
                        welcome_message = MessageCreate(
                            id=str(uuid4()),
                            chat_id=chat_result.id,
                            sender_id=live_card_id,
                            role="assistant",
                            text=welcome_text,
                        )
                        await message_crud.create_and_add_to_chat(welcome_message, chat_result.id)
                except Exception as e:
                    logger.error(f"获取欢迎消息模板失败: {str(e)}")
    
            chat_id = chat_result.id
        services = ["option1","option2","option3"]

        return ChatStartResponse(
            chat_id=chat_id,
            live_card_id=live_card_id,
            topic_title=live_card_info.topic_title,
            topic_description=live_card_info.topic_description,
            topic_image_url=live_card_info.topic_image_url,
            chat_type="live_card",
            services=services
        )
    

    @staticmethod
    async def get_chat_messages_incremental(
        current_user: User,
        chat_id: str,
        incremental_params: IncrementalParams
    ) -> MessageIncrementalResponse:
        """
        增量获取聊天消息
        
        Args:
            chat_id: 聊天ID
            last_id: 最后一条消息ID
            last_timestamp: 最后一条消息时间戳
            limit: 限制数量
            direction: 获取方向 (after: 新消息, before: 历史消息)
            
        Returns:
            MessageIncrementalResponse: 增量响应
        """

        chat = await chat_crud.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError("聊天不存在")
        chat_user_id = chat.participants["user"]
        if chat_user_id != current_user.id:
            raise ValueError("你不是创建该chat的用户，无权限获取聊天消息")
        message_filter = MessageFilter(chat_id=chat.id)
        messages, has_more = await message_crud.get_messages_incremental(message_filter, incremental_params)

        message_responses = []
        for message in messages:
            message_response = MessageResponse(
                message_id=str(message.id),
                message_type="text",
                role=message.role,
                message_content=message.text,
                message_images=message.contents,
                created_at=message.created_at
            )
            message_responses.append(message_response)
        if message_responses:
            message_responses.reverse()
            if incremental_params.direction == "before":
                last_msg_id = message_responses[0].message_id
                last_msg_timestamp = message_responses[0].created_at
            else:
                last_msg_id = message_responses[-1].message_id
                last_msg_timestamp = message_responses[-1].created_at    
            return MessageIncrementalResponse(
                items=message_responses,
                has_more=has_more,
                last_id=last_msg_id,
                last_timestamp=last_msg_timestamp
            )
        else:
            return MessageIncrementalResponse(
                items=[],
                has_more=False,
                last_id="",
                last_timestamp=None
            )
    
    @staticmethod
    async def get_user_all_chats(
        local_user: User,
        pagination: PaginationParams
    ) -> List[ChatListItemResponse]:
        local_user_id = local_user.id
        chats,total = await chat_crud.get_chats_with_messages_aggregated(
            ChatFilter(participants={"user": local_user_id}), 
            pagination
        )
        chat_responses = []
        for chat in chats:
            ### 这里需要处理一下
            ### unread_message_count, chat_title, chat_type都需要后续根据业务逻辑变化
            chat_base = ChatListItemResponse(**{
                k: v for k, v in chat.items()
                if k not in ["is_deleted", "deleted_at"]
            })
            if chat_base.live_card_id:
                chat_responses.append(chat_base)
        return chat_responses, total
    
    @staticmethod
    async def chats_list(
        current_user: User,
        incremental_params: ChatIncrementalParams
    ) -> Tuple[List[ChatListItemResponse], bool, int]:
        """处理获取收藏列表请求（带分页和过滤）"""
        chats_list, has_more, total = await chat_crud.get_chats_incremental(current_user.id, incremental_params)
        return chats_list, has_more, total