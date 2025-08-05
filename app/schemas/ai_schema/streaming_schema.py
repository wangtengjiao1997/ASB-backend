from pydantic import BaseModel, Field, PrivateAttr, field_serializer
from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime

# Enum 定义
class ActionExecutionStatus(str, Enum):
    created = "created"
    executing = "executing"
    completed = "completed"
    failed = "failed"

class MessageCompletionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"

class MessageTypes(str, Enum):
    reasoning = "reasoning"
    chat = "chat"
    action = "action"

class StreamingResponseStatus(Enum):
    created = "created"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    aborted = "aborted"

# 内容类型模型
class TextContent(BaseModel):
    content_type: Literal["text"] = "text"
    text: str

class FunctionCallContent(BaseModel):
    content_type: Literal["function_call"] = "function_call"
    function_name: str
    arguments: Optional[Union[str, Dict[str, Any]]] = None

# 消息模型
class ActionMessage(BaseModel):
    type: Literal["action"] = "action"
    role: Literal["assistant"] = "assistant"
    name: Optional[str] = None
    status: ActionExecutionStatus = ActionExecutionStatus.completed
    action: FunctionCallContent
    observation_summary: Optional[str] = None
    failure_reason: Optional[str] = None

class ChatMessage(BaseModel):
    type: Literal["chat"] = "chat"
    role: Literal["user", "assistant"]
    name: Optional[str] = None
    status: MessageCompletionStatus = MessageCompletionStatus.COMPLETED
    items: List[TextContent]

class ReasoningMessage(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    role: Literal["assistant"] = "assistant"
    name: Optional[str] = None
    status: MessageCompletionStatus = MessageCompletionStatus.COMPLETED
    thought: TextContent

# 联合类型定义
Message = Union[ActionMessage, ChatMessage, ReasoningMessage]
ChatInputMessage = Union[ChatMessage, ReasoningMessage]
CHAT_MESSAGE_ITEM_TYPES = TextContent

# 响应事件模型
class ResponseEventResponseBody(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# 响应级别事件
class ResponseCreated(BaseModel):
    event_type: Literal["response.created"] = "response.created"
    response: ResponseEventResponseBody

class ResponseInProgress(BaseModel):
    event_type: Literal["response.in_progress"] = "response.in_progress"
    response: ResponseEventResponseBody

class ResponseCompleted(BaseModel):
    event_type: Literal["response.completed"] = "response.completed"
    response: ResponseEventResponseBody

class ResponseFailed(BaseModel):
    event_type: Literal["response.failed"] = "response.failed"
    response: ResponseEventResponseBody

class ResponseAborted(BaseModel):
    event_type: Literal["response.aborted"] = "response.aborted"
    response: ResponseEventResponseBody

# 消息级别事件
class ActionMessageBody(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: ActionMessage

class ActionMessageAdded(BaseModel):
    response_id: UUID
    event_type: Literal["response.action_message.added"] = "response.action_message.added"
    message_index: int
    message_type: Literal["action"] = "action"
    message: ActionMessageBody

class ActionMessageDone(BaseModel):
    response_id: UUID
    event_type: Literal["response.action_message.done"] = "response.action_message.done"
    message_index: int
    message_type: Literal["action"] = "action"
    message: ActionMessageBody
    usage: Optional["CompletionUsage"] = None

class ChatMessageBody(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: ChatMessage

class ChatMessageAdded(BaseModel):
    response_id: UUID
    event_type: Literal["response.chat_message.added"] = "response.chat_message.added"
    message_index: int
    message_type: Literal["chat"] = "chat"
    message: ChatMessageBody

class ChatMessageDone(BaseModel):
    response_id: UUID
    event_type: Literal["response.chat_message.done"] = "response.chat_message.done"
    message_index: int
    message_type: Literal["chat"] = "chat"
    message: ChatMessageBody
    finish_reason: Literal["stop", "length", "tool_calls"] = "stop"
    usage: Optional["CompletionUsage"] = None

class ReasoningMessageBody(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: ReasoningMessage

class ReasoningMessageAdded(BaseModel):
    response_id: UUID
    event_type: Literal["response.reasoning_message.added"] = "response.reasoning_message.added"
    message_index: int
    message_type: Literal["chat"] = "chat"
    message: ReasoningMessageBody

class ReasoningMessageDone(BaseModel):
    response_id: UUID
    event_type: Literal["response.reasoning_message.done"] = "response.reasoning_message.done"
    message_index: int
    message_type: Literal["chat"] = "chat"
    message: ReasoningMessageBody
    finish_reason: Literal["stop", "length", "tool_calls"] = "stop"
    usage: Optional["CompletionUsage"] = None

# Action内容级别事件
class ActionCreated(BaseModel):
    event_type: Literal["response.action_message.action.created"] = "response.action_message.action.created"
    message_id: UUID

class ActionExecuting(BaseModel):
    event_type: Literal["response.action_message.action.executing"] = "response.action_message.action.executing"
    message_id: UUID

class ActionCompleted(BaseModel):
    event_type: Literal["response.action_message.action.completed"] = "response.action_message.action.completed"
    message_id: UUID

class ActionFailed(BaseModel):
    event_type: Literal["response.action_message.action.failed"] = "response.action_message.action.failed"
    message_id: UUID

# Chat消息内容级别事件
class ChatMessageItemBody(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: TextContent

class ChatMessageItemAdded(BaseModel):
    event_type: Literal["response.chat_message.item.added"] = "response.chat_message.item.added"
    message_id: UUID
    item_index: int
    item_type: Literal["text"] = "text"
    item: ChatMessageItemBody

class ChatMessageItemDone(BaseModel):
    event_type: Literal["response.chat_message.item.done"] = "response.chat_message.item.done"
    message_id: UUID
    item_index: int
    item_type: Literal["text"] = "text"
    item: ChatMessageItemBody

class ChatMessageItemOutputTextDelta(BaseModel):
    event_type: Literal["response.chat_message.item.output_text.delta"] = "response.chat_message.item.output_text.delta"
    item_id: UUID
    delta: str

class ChatMessageItemOutputTextDone(BaseModel):
    event_type: Literal["response.chat_message.item.output_text.done"] = "response.chat_message.item.output_text.done"
    item_id: UUID
    text: str

# Reasoning消息内容级别事件
class ThoughtDelta(BaseModel):
    event_type: Literal["response.reasoning_message.thought.delta"] = "response.reasoning_message.thought.delta"
    message_id: UUID
    delta: str

class ThoughtDone(BaseModel):
    event_type: Literal["response.reasoning_message.thought.done"] = "response.reasoning_message.thought.done"
    message_id: UUID
    thought: str

# 补充模型
class CompletionUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


# 流式响应事件联合类型
StreamingResponseEvent = Union[
    ResponseCreated, ResponseInProgress, ResponseCompleted, ResponseFailed, ResponseAborted,
    ActionMessageAdded, ActionMessageDone, ChatMessageAdded, ChatMessageDone,
    ReasoningMessageAdded, ReasoningMessageDone, ActionCreated, ActionExecuting,
    ActionCompleted, ActionFailed, ChatMessageItemAdded, ChatMessageItemDone,
    ChatMessageItemOutputTextDelta, ChatMessageItemOutputTextDone, ThoughtDelta, ThoughtDone
]

def validate_streaming_response_event(data: Dict[str, Any]) -> StreamingResponseEvent:
    """验证并转换流式响应事件数据"""
    event_type = data.get("event_type")
    
    # 根据事件类型选择相应的模型类进行验证
    if event_type == "response.created":
        return ResponseCreated.model_validate(data)
    elif event_type == "response.in_progress":
        return ResponseInProgress.model_validate(data)
    elif event_type == "response.completed":
        return ResponseCompleted.model_validate(data)
    elif event_type == "response.failed":
        return ResponseFailed.model_validate(data)
    elif event_type == "response.aborted":
        return ResponseAborted.model_validate(data)
    elif event_type == "response.action_message.added":
        return ActionMessageAdded.model_validate(data)
    elif event_type == "response.action_message.done":
        return ActionMessageDone.model_validate(data)
    elif event_type == "response.chat_message.added":
        return ChatMessageAdded.model_validate(data)
    elif event_type == "response.chat_message.done":
        return ChatMessageDone.model_validate(data)
    elif event_type == "response.reasoning_message.added":
        return ReasoningMessageAdded.model_validate(data)
    elif event_type == "response.reasoning_message.done":
        return ReasoningMessageDone.model_validate(data)
    elif event_type == "response.action_message.action.created":
        return ActionCreated.model_validate(data)
    elif event_type == "response.action_message.action.executing":
        return ActionExecuting.model_validate(data)
    elif event_type == "response.action_message.action.completed":
        return ActionCompleted.model_validate(data)
    elif event_type == "response.action_message.action.failed":
        return ActionFailed.model_validate(data)
    elif event_type == "response.chat_message.item.added":
        return ChatMessageItemAdded.model_validate(data)
    elif event_type == "response.chat_message.item.done":
        return ChatMessageItemDone.model_validate(data)
    elif event_type == "response.chat_message.item.output_text.delta":
        return ChatMessageItemOutputTextDelta.model_validate(data)
    elif event_type == "response.chat_message.item.output_text.done":
        return ChatMessageItemOutputTextDone.model_validate(data)
    elif event_type == "response.reasoning_message.thought.delta":
        return ThoughtDelta.model_validate(data)
    elif event_type == "response.reasoning_message.thought.done":
        return ThoughtDone.model_validate(data)
    else:
        raise ValueError(f"未知的事件类型: {event_type}")
    
class MessageHandler(BaseModel):
    message: Message

class StreamingResponseEventHandler(BaseModel):
    event: StreamingResponseEvent

# 缓存流式响应事件的容器类
class StreamingResponse(BaseModel):
    """缓存流式响应事件的容器类。"""
    id: UUID
    created_at: datetime
    status: StreamingResponseStatus
    events: List[StreamingResponseEvent]
    messages: List[Message]

    _messages: Dict[str, Message] = PrivateAttr(default_factory=dict)
    _items: Dict[str, CHAT_MESSAGE_ITEM_TYPES] = PrivateAttr(default_factory=dict)

    @field_serializer("status")
    def serialize_status(self, status: StreamingResponseStatus) -> str:
        return status.value

    def __init__(self, event: ResponseCreated):
        if not isinstance(event, ResponseCreated):
            raise TypeError("只有 `ResponseCreated` 事件可以初始化 `StreamingResponse`。")
        super().__init__(
            id=event.response.id,
            created_at=event.response.created_at,
            status=StreamingResponseStatus.created,
            events=[event],
            messages=[],
        )

    def add(self, event: StreamingResponseEvent) -> None:
        # 每种响应事件在响应中只能出现一次
        if isinstance(event, ResponseCreated):
            raise ValueError("`ResponseCreated` 事件只能用于初始化响应")
        if isinstance(event, ResponseInProgress) and self.status != StreamingResponseStatus.created:
                raise ValueError("尝试在响应不处于 `created` 状态时设置 `ResponseInProgress` 事件。")
        if isinstance(event, (ResponseCompleted, ResponseFailed, ResponseAborted)) and (
            self.count_event("response.completed") >= 1 or
            self.count_event("response.failed") >= 1 or
            self.count_event("response.aborted") >= 1
        ):
            raise ValueError("尝试在响应已经完成、失败或中止时设置 `ResponseCompleted`、`ResponseFailed` 或 `ResponseAborted` 事件。")
        
        # 消息完成事件必须小于或等于消息添加事件
        if event.event_type.endswith("message.done") and self.count_event_suffix("message.added") <= self.count_event_suffix("message.done"):
            raise ValueError("消息完成事件必须小于或等于消息添加事件。")
        
        self.events.append(event)
        match event.event_type:
            case "response.in_progress":
                self.status = StreamingResponseStatus.in_progress
            case "response.completed":
                self.status = StreamingResponseStatus.completed
            case "response.failed":
                self.status = StreamingResponseStatus.failed
            case "response.aborted":
                self.status = StreamingResponseStatus.aborted
            case "response.action_message.added":
                self.messages.append(event.message.message)
                self._messages[event.message.id.hex] = event.message.message
            case "response.chat_message.added":
                event.message.message.status = MessageCompletionStatus.IN_PROGRESS
                self.messages.append(event.message.message)
                self._messages[event.message.id.hex] = event.message.message
            case "response.chat_message.done":
                message = self.get_message(event.message.id)
                if event.finish_reason == "length":
                    message.status = MessageCompletionStatus.INCOMPLETE
                else:
                    message.status = MessageCompletionStatus.COMPLETED
            case "response.reasoning_message.added":
                event.message.message.status = MessageCompletionStatus.IN_PROGRESS
                self.messages.append(event.message.message)
                self._messages[event.message.id.hex] = event.message.message
            case "response.reasoning_message.done":
                message = self.get_message(event.message.id)
                if event.finish_reason == "length":
                    message.status = MessageCompletionStatus.INCOMPLETE
                else:
                    message.status = MessageCompletionStatus.COMPLETED
            case "response.action_message.action.created":
                message = self.get_message(event.message_id)
                message.status = ActionExecutionStatus.created
            case "response.action_message.action.executing":
                message = self.get_message(event.message_id)
                message.status = ActionExecutionStatus.executing
            case "response.action_message.action.completed":
                message = self.get_message(event.message_id)
                message.status = ActionExecutionStatus.completed
                message.observation_summary = event.observation_summary if hasattr(event, 'observation_summary') else None
            case "response.action_message.action.failed":
                message = self.get_message(event.message_id)
                message.status = ActionExecutionStatus.failed
                message.failure_reason = event.failure_reason if hasattr(event, 'failure_reason') else None
            case "response.chat_message.item.added":
                message = self.get_message(event.message_id)
                message.items.append(event.item.content)
                self._items[event.item.id.hex] = event.item.content
            case "response.chat_message.item.output_text.delta":
                item = self.get_item(event.item_id)
                item.text += event.delta
            case "response.chat_message.item.output_text.done":
                item = self.get_item(event.item_id)
                item.text = event.text
            case "response.reasoning_message.thought.delta":
                message = self.get_message(event.message_id)
                message.thought.text += event.delta
            case "response.reasoning_message.thought.done":
                message = self.get_message(event.message_id)
                message.thought.text = event.thought
    
    def get_message(self, message_id: UUID) -> Message:
        return self._messages[message_id.hex]
    
    def get_item(self, item_id: UUID) -> CHAT_MESSAGE_ITEM_TYPES:
        return self._items[item_id.hex]
    
    def count_event(self, event_type: str) -> int:
        return len([event for event in self.events if event.event_type == event_type])

    def count_event_prefix(self, event_type_prefix: str) -> int:
        return len([event for event in self.events if event.event_type.startswith(event_type_prefix)])
    
    def count_event_suffix(self, event_type_suffix: str) -> int:
        return len([event for event in self.events if event.event_type.endswith(event_type_suffix)])