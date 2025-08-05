import os
import json
import asyncio
from uuid import UUID
from typing import Dict, List, Any, Optional, AsyncIterator
import httpx
from app.utils.logger_service import logger
from app.schemas.ai_schema.streaming_schema import (
    StreamingResponseEvent, StreamingResponse, 
    ChatInputMessage, Message, MessageHandler, StreamingResponseEventHandler, validate_streaming_response_event
)
from app.core.config import settings
import traceback

class SSEClient:
    """
    SSE客户端类，用于与支持Server-Sent Events的API进行通信
    """
    
    @staticmethod
    def parse_event(lines: List[str]) -> Dict[str, Any]:
        """解析SSE事件"""
        event = {
            "id": None,
            "event": "message",  # 默认事件类型是message
            "data": ""
        }

        for line in lines:
            if line.startswith("id:"):
                event["id"] = line[3:].strip()
            elif line.startswith("event:"):
                event["event"] = line[6:].strip()
            elif line.startswith("data:"):
                if event["data"]:
                    event["data"] += "\n"
                event["data"] += line[5:].strip()

        try:
            event["data"] = json.loads(event["data"])
        except Exception:
            # 如果不是JSON格式，保持原样
            pass

        return event
    
    @staticmethod
    async def chat_completions(
        chat_id: UUID,
        session_id: UUID,
        bot_id: UUID,
        messages: List[ChatInputMessage],
        stream: bool = True,
    ) -> List[Message]:
        """
        使用SSE进行聊天完成
        
        Args:
            chat_id: 聊天ID
            session_id: 会话ID
            bot_id: 机器人ID
            messages: 聊天消息列表
            stream: 是否使用流式响应
            
        Returns:
            List[Message]: 聊天消息列表
        """
        url = settings.AI_SERVICE_BOT_BASE_URL
        
        logger.info(f"发送聊天请求到: {url}")
        
        try:
            # 增加超时时间，并添加重试逻辑
            for attempt in range(3):  # 最多尝试3次
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client_session:
                        if not stream:
                            # 非流式请求
                            response = await client_session.post(
                                url=url,
                                json={
                                    "chat_id": str(chat_id),
                                    "session_id": str(session_id),
                                    "bot_id": str(bot_id),
                                    "messages": [msg.model_dump(mode="json") for msg in messages],
                                    "stream": stream,
                                },
                                headers={"Content-Type": "application/json"}
                            )
                            
                            response.raise_for_status()
                            messages_raw = response.json()
                            logger.debug(f"收到非流式响应: {messages_raw}")
                            return [MessageHandler.model_validate({"message": msg_raw}).message for msg_raw in messages_raw]
                        else:
                            # 流式请求处理
                            streaming_response = None
                            all_messages = []
                            
                            # 使用httpx的流式API
                            async with client_session.stream(
                                "POST",
                                url=url,
                                json={
                                    "chat_id": str(chat_id),
                                    "session_id": str(session_id),
                                    "bot_id": str(bot_id),
                                    "messages": [msg.model_dump(mode="json") for msg in messages],
                                    "stream": stream,
                                },
                                headers={
                                    "Content-Type": "application/json",
                                    "Accept": "text/event-stream"
                                }
                            ) as response:
                                response.raise_for_status()
                                
                                buffer = []
                                async for chunk in response.aiter_bytes():
                                    for line in chunk.decode("utf-8").split("\n"):
                                        line = line.strip()
                                        if line:
                                            buffer.append(line)
                                        else:
                                            # 空行表示事件结束
                                            if buffer:
                                                event_data = SSEClient.parse_event(buffer)
                                                if event_data:
                                                    if event_data["event"] == "respond":
                                                        response_event_raw = event_data["data"]
                                                        
                                                        response_event = StreamingResponseEventHandler.model_validate(response_event_raw)
                                                        
                                                        if streaming_response is None:
                                                            if hasattr(response_event, 'event_type') and response_event.event_type == "response.created":
                                                                streaming_response = StreamingResponse(event=response_event)
                                                        else:
                                                            streaming_response.add(response_event)
                                                    
                                                    elif event_data["event"] == "done":
                                                        logger.debug("收到done事件，SSE流结束")
                                                        break
                                            buffer = []
                            
                            if streaming_response:
                                return streaming_response.messages
                            return all_messages
                    
                    # 如果成功处理了请求，跳出重试循环
                    break
                    
                except httpx.ReadTimeout:
                    if attempt < 2:  # 最后一次不重试
                        logger.warning(f"连接超时，正在进行第{attempt+2}次尝试...")
                        await asyncio.sleep(1)
                    else:
                        logger.error("多次尝试连接AI服务均超时")
                        raise
                        
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
                    raise
                except Exception as e:
                    logger.error(f"发送请求时出错: {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"聊天完成请求失败: {str(e)}")
            raise
    
    @staticmethod
    async def stream_chat_events(
        chat_id: UUID,
        session_id: UUID,
        bot_id: UUID,
        messages: List[ChatInputMessage]
    ) -> AsyncIterator[StreamingResponseEvent]:
        """
        流式获取聊天事件
        
        Args:
            chat_id: 聊天ID
            session_id: 会话ID
            bot_id: 机器人ID
            messages: 聊天消息列表
            
        Yields:
            StreamingResponseEvent: 流式响应事件
        """
        url = settings.AI_SERVICE_BOT_BASE_URL
        
        logger.info(f"发送流式聊天请求到: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client_session:
                # 使用httpx的流式API
                async with client_session.stream(
                    "POST",
                    url=url,
                    json={
                        "chat_id": str(chat_id),
                        "session_id": str(session_id),
                        "bot_id": str(bot_id),
                        "messages": [msg.model_dump(mode="json") for msg in messages],
                        "stream": True,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:
                    response.raise_for_status()
                    streaming_response = None
                    buffer = []
                    # 使用aiter_bytes()逐字节流式接收响应
                    async for chunk in response.aiter_bytes():
                        # 将字节解码为文本并按行分割
                        for line in chunk.decode("utf-8").split("\n"):
                            line = line.strip()
                            if line:
                                logger.debug(f"接收到行: {line}")
                                buffer.append(line)
                            else:
                                # 空行表示事件结束
                                if buffer:
                                    event_data = SSEClient.parse_event(buffer)
                                    if event_data:
                                        logger.debug(f"解析的事件: {event_data}")
                                        match event_data["event"]:
                                            case "ping":
                                                # 保持连接活跃
                                                logger.debug("收到ping事件")
                                            case "done":
                                                logger.debug("收到done事件，SSE流结束")
                                                return
                                            case "respond":
                                                print("--------------------------------event_data:\n", event_data)
                                                response_event_raw = event_data["data"]
                                                response_event = StreamingResponseEventHandler.model_validate({"event": response_event_raw}).event
                                                if streaming_response is None:
                                                    streaming_response = StreamingResponse(event=response_event)
                                                else:
                                                    streaming_response.add(response_event)
                                                logger.debug(f"生成事件: {response_event.event_type}")
                                                yield response_event

                                buffer = []
                    if streaming_response:
                        messages = streaming_response.messages        
        except httpx.ReadTimeout:
            logger.error("读取AI服务响应超时")
            # 模拟一个错误事件，让调用者知道发生了问题
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error="连接到AI服务超时"
                )
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            # 模拟一个错误事件
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error=f"HTTP错误: {e.response.status_code}"
                )
            )
            
        except Exception as e:
            # 模拟一个错误事件
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            logger.error(f"SSE客户端错误: {traceback.format_exc()}")
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error=f"客户端错误: {str(e)}"
                )
            )
            
    @staticmethod
    async def stream_live_card_chat_events(
        chat_id: UUID,
        session_id: UUID,
        bot_id: UUID,
        bot_name: str,
        user_name: str,
        focused_category: str,
        live_card_topic: str,
        live_card_content: str,
        chat_history: List[ChatInputMessage],
        user_input: ChatInputMessage,
        max_chat_history_size: int = 20,
        streamimg: bool = True,
    ) -> AsyncIterator[StreamingResponseEvent]:
        """
        流式获取聊天事件
        
        Args:
            chat_id: 聊天ID
            session_id: 会话ID
            bot_id: 机器人ID
            messages: 聊天消息列表
            
        Yields:
            StreamingResponseEvent: 流式响应事件
        """
        url = settings.AI_SERVICE_BASE_URL
        
        logger.info(f"发送流式聊天请求到: {url}")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client_session:
                # 使用httpx的流式API
                async with client_session.stream(
                    "POST",
                    url=f"http://3.20.140.217:9100/api/v1/info_bot/live_card_chat/completion",
                    json={
                        "chat_id": str(chat_id),
                        "session_id": str(session_id),
                        "bot_id": str(bot_id),
                        "bot_name": bot_name,
                        "user_name": user_name,
                        "focused_category": focused_category,
                        "live_card_topic": live_card_topic,
                        "live_card_content": live_card_content,
                        "chat_history": [msg.model_dump(mode="json") for msg in chat_history],
                        "user_input": user_input.model_dump(mode="json"),
                        "max_chat_history_size": max_chat_history_size,
                        "stream": streamimg,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:
                    response.raise_for_status()
                    streaming_response = None
                    buffer = []
                    # 使用aiter_bytes()逐字节流式接收响应
                    async for chunk in response.aiter_bytes():
                        # 将字节解码为文本并按行分割
                        for line in chunk.decode("utf-8").split("\n"):
                            line = line.strip()
                            if line:
                                logger.debug(f"接收到行: {line}")
                                buffer.append(line)
                            else:
                                # 空行表示事件结束
                                if buffer:
                                    event_data = SSEClient.parse_event(buffer)
                                    if event_data:
                                        logger.debug(f"解析的事件: {event_data}")
                                        match event_data["event"]:
                                            case "ping":
                                                # 保持连接活跃
                                                logger.debug("收到ping事件")
                                            case "done":
                                                logger.debug("收到done事件，SSE流结束")
                                                return
                                            case "respond":
                                                print("--------------------------------event_data:\n", event_data)
                                                response_event_raw = event_data["data"]
                                                response_event = StreamingResponseEventHandler.model_validate({"event": response_event_raw}).event
                                                if streaming_response is None:
                                                    streaming_response = StreamingResponse(event=response_event)
                                                else:
                                                    streaming_response.add(response_event)
                                                logger.debug(f"生成事件: {response_event.event_type}")
                                                yield response_event

                                buffer = []
                    if streaming_response:
                        messages = streaming_response.messages        
        except httpx.ReadTimeout:
            logger.error("读取AI服务响应超时")
            # 模拟一个错误事件，让调用者知道发生了问题
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error="连接到AI服务超时"
                )
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            # 模拟一个错误事件
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error=f"HTTP错误: {e.response.status_code}"
                )
            )
            
        except Exception as e:
            # 模拟一个错误事件
            from app.schemas.ai_schema.streaming_schema import ResponseFailed, ResponseEventResponseBody
            logger.error(f"SSE客户端错误: {traceback.format_exc()}")
            yield ResponseFailed(
                response=ResponseEventResponseBody(
                    error=f"客户端错误: {str(e)}"
                )
            )