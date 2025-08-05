from typing import List, Optional, Dict, Any, Tuple
from app.entities.message_entity import Message
from app.schemas.ai_schema.message_schema import MessageCreate, MessageUpdate, MessageFilter, IncrementalParams
from app.crud.base_crud import BaseCRUD
from app.crud.chat_crud import chat_crud
from app.schemas.ai_schema.chat_schema import ChatUpdate

class MessageCRUD(BaseCRUD[Message, MessageCreate, MessageUpdate]):
    def __init__(self):
        super().__init__(Message)
    
    async def _build_filter_query(self, filter_params: MessageFilter) -> Dict:
        """构建消息过滤查询条件"""
        query = {"is_deleted": False}
        
        if filter_params.chat_id:
            query["chat_id"] = filter_params.chat_id
            
        if filter_params.sender_id:
            query["sender_id"] = filter_params.sender_id
            
        if filter_params.role:
            query["role"] = filter_params.role.value
            
        return query

    async def get_messages_incremental(
        self,
        filter_params: MessageFilter,
        incremental_params: IncrementalParams
    ) -> Tuple[List[Message], bool]:
        """
        增量获取消息
        
        Args:
            filter_params: 消息过滤条件
            incremental_params: 增量参数
            
        Returns:
            Tuple[List[Message], bool]: 消息列表和是否还有更多
        """
        query = await self._build_filter_query(filter_params)
        

        if incremental_params.direction == "before":  # before - 获取历史消息
            if incremental_params.last_id:
                last_message = await Message.find_one({"_id": incremental_params.last_id})
                if last_message:
                    query["created_at"] = {"$lt": last_message.created_at}           
        else:
            if incremental_params.last_id:

                last_message = await Message.find_one({"_id": incremental_params.last_id})
                if last_message:
                    query["created_at"] = {"$gt": last_message.created_at}
        sort_direction = -1
        
        # 执行查询，多查一条用于判断是否还有更多
        messages = await Message.find(query).sort(
            [("created_at", sort_direction)]
        ).limit(incremental_params.limit + 1).to_list()
        
        # 判断是否还有更多
        has_more = len(messages) > incremental_params.limit
        if has_more:
            messages = messages[:-1]  # 移除多查的那一条
        
        return messages, has_more
    
    async def create_and_add_to_chat(self, message: MessageCreate, chat_id: str) -> Message:
        """创建消息并添加到聊天"""
        message = await self.create(message)
        chat = await chat_crud.get_chat_by_id(chat_id)
        if chat:
            chat.messages.append(message.id)
            await chat_crud.update(chat.id, ChatUpdate(messages=chat.messages))
        return message

message_crud = MessageCRUD()