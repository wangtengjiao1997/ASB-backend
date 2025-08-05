from typing import List, Optional, Dict, Any, Tuple
from app.entities.chat_entity import Chat
from app.schemas.ai_schema.chat_schema import ChatCreate, ChatUpdate, ChatFilter, PaginationParams, ChatIncrementalParams
from app.crud.base_crud import BaseCRUD
from app.entities.message_entity import Message
from app.crud.live_card_crud import live_card_crud

class ChatCRUD(BaseCRUD[Chat, ChatCreate, ChatUpdate]):
    def __init__(self):
        super().__init__(Chat)
    
    async def _build_filter_query(self, filter_params: ChatFilter) -> Dict:
        """构建聊天过滤查询条件"""
        query = {"is_deleted": False}
        
        if filter_params.id:
            query["id"] = filter_params.id
            
        if filter_params.participants:
            query["participants.user"] = filter_params.participants["user"]
            
        if filter_params.shareable is not None:
            query["shareable"] = filter_params.shareable
            
        if filter_params.start_date:
            query["created_at"] = {"$gte": filter_params.start_date}
            
        if filter_params.end_date:
            if "created_at" in query:
                query["created_at"]["$lte"] = filter_params.end_date
            else:
                query["created_at"] = {"$lte": filter_params.end_date}
                
        return query

    async def get_chats_with_filter(
        self,
        filter_params: ChatFilter,
        pagination: PaginationParams
    ) -> Tuple[List[Chat], int]:
        """带分页和过滤的聊天列表查询"""
        query = await self._build_filter_query(filter_params)
        
        # 获取总计数
        total = await Chat.find(query).count()
        
        # 排序方向
        sort_direction = -1 if pagination.sort_desc else 1
        sort_field = pagination.sort_by

        # 执行查询
        chats = await Chat.find(query).sort(
            [(sort_field, sort_direction)]
        ).skip((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).to_list()

        return chats, total
    async def count_user_chats(self, user_id: str) -> int:
        """获取用户聊天数量"""
        return await Chat.find({"participants.user": user_id, "is_deleted": False}).count()
    
    async def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """根据ID获取聊天"""
        return await Chat.find_one({"_id": chat_id})
    
    async def get_chat_by_live_card_and_user(self, live_card_id: str, user_id: str) -> Optional[Chat]:
        """根据live_card_id和user_id获取聊天"""
        return await Chat.find_one({"participants.live_card": live_card_id, "participants.user": user_id})

    async def add_message_to_chat(self, chat_id: str, message_id: str) -> Optional[Chat]:
        """向聊天添加消息"""
        chat = await self.get(chat_id)
        if not chat:
            return None
        chat.messages.append(message_id)
        return await chat.save()

    async def get_chats_with_messages_aggregated(
        self,
        filter_params: ChatFilter,
        pagination: PaginationParams,
        message_limit: int = 1
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        简化版本：分别查询聊天、消息和live_card信息
        兼容 DocumentDB 5.0.0
        """
        # 1. 获取聊天列表
        chats, total = await self.get_chats_with_filter(filter_params, pagination)
        
        if not chats:
            return [], total
        
        # 2. 收集需要查询的ID
        chat_ids = [str(chat.id) for chat in chats]
        live_card_ids = [chat.participants.get("live_card") for chat in chats if chat.participants.get("live_card")]
        
        # 3. 批量查询最新消息
        messages_dict = {}
        if chat_ids:
            # 为每个聊天查询最新消息
            for chat_id in chat_ids:
                latest_message = await Message.find_one(
                    {"chat_id": chat_id, "is_deleted": False},
                    sort=[("created_at", -1)]
                )
                if latest_message:
                    messages_dict[chat_id] = latest_message
        
        # 4. 批量查询live_card信息
        live_card_dict = {}
        if live_card_ids:
            live_cards = await live_card_crud.get_live_cards_by_ids(live_card_ids)
            live_card_dict = {str(live_card.id): live_card for live_card in live_cards}
        
        # 5. 组合数据
        results = []
        for chat in chats:
            live_card_id = chat.participants.get("live_card")
            live_card = live_card_dict.get(live_card_id) if live_card_id else None
            latest_message = messages_dict.get(str(chat.id))
            
            chat_data = {
                "_id": chat.id,
                "chat_id": str(chat.id),
                "participants": chat.participants,
                "messages": chat.messages,
                "shareable": chat.shareable,
                "snapshot": chat.snapshot,
                "chat_type": chat.chat_type,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                
                # Live Card 信息
                "topic_title": live_card.topic_title if live_card else None,
                "topic_description": live_card.topic_description if live_card else None,
                "topic_image_url": live_card.topic_image_url if live_card else None,
                "chat_title": live_card.topic_title if live_card else "未知聊天",
                
                # 最新消息信息
                "chat_last_id": str(latest_message.id) if latest_message else None,
                "chat_last_message_summary": latest_message.text if latest_message else None,
                "chat_last_message_created_at": latest_message.created_at if latest_message else None
            }
            
            results.append(chat_data)
        
        return results, total

    async def get_chats_incremental(
        self,
        current_user_id: str,
        incremental_params: ChatIncrementalParams
    ) -> Tuple[List[Chat], int, int]:
        """获取关注列表（带分页和过滤）"""
        query = {"participants.user": current_user_id,"is_deleted": False}
        total_chats = await self.count_user_chats(current_user_id)

        if incremental_params.direction == "before":  # before - 获取历史关注
            if incremental_params.last_id:
                last_chat = await Chat.find_one({"_id": incremental_params.last_id})
                if last_chat:
                    query["created_at"] = {"$lt": last_chat.created_at}           
        else:
            if incremental_params.last_id:
                last_chat = await Chat.find_one({"_id": incremental_params.last_id})
                if last_chat:
                    query["created_at"] = {"$gt": last_chat.created_at}
        sort_direction = -1
        
        # 执行查询，多查一条用于判断是否还有更多
        chats = await Chat.find(query).sort(
            [("created_at", sort_direction)]
        ).limit(incremental_params.limit + 1).to_list()

        # 判断是否还有更多
        has_more = len(chats) > incremental_params.limit
        if has_more:
            chats = chats[:-1]  # 移除多查的那一条
        if not chats:
            return [], has_more, total_chats
        
        # 6. 收集需要查询的ID
        chat_ids = [str(chat.id) for chat in chats]
        live_card_ids = [chat.participants.get("live_card") for chat in chats if chat.participants.get("live_card")]
        
        # 7. 批量查询最新消息
        messages_dict = {}
        if chat_ids:
            
            # 为每个聊天查询最新消息
            for chat_id in chat_ids:
                latest_message = await Message.find_one(
                    {"chat_id": chat_id, "is_deleted": False},
                    sort=[("created_at", -1)]
                )
                if latest_message:
                    messages_dict[chat_id] = latest_message
        
        # 8. 批量查询live_card信息
        live_card_dict = {}
        if live_card_ids:

            live_cards = await live_card_crud.get_live_cards_by_ids(live_card_ids)
            live_card_dict = {str(live_card.id): live_card for live_card in live_cards}
        
        # 9. 组合聚合数据
        results = []
        for chat in chats:
            live_card_id = chat.participants.get("live_card")
            live_card = live_card_dict.get(live_card_id) if live_card_id else None
            latest_message = messages_dict.get(str(chat.id))
            
            chat_data = {
                "_id": chat.id,
                "chat_id": str(chat.id),
                "participants": chat.participants,
                "messages": chat.messages,
                "shareable": chat.shareable,
                "snapshot": chat.snapshot,
                "chat_type": chat.chat_type,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                
                # Live Card 信息
                "topic_title": live_card.topic_title if live_card else None,
                "topic_description": live_card.topic_description if live_card else None,
                "topic_image_url": live_card.topic_image_url if live_card else None,
                "chat_title": live_card.topic_title if live_card else "未知聊天",
                
                # 最新消息信息
                "chat_last_id": str(latest_message.id) if latest_message else None,
                "chat_last_message_summary": latest_message.text if latest_message else None,
                "chat_last_message_created_at": latest_message.created_at if latest_message else None,
                
                # 增量分页相关信息
                "cursor_id": str(chat.id),  # 用于下次分页的游标
                "cursor_time": chat.created_at  # 用于调试的时间戳
            }
            
            results.append(chat_data)
        
        return results, has_more, total_chats

chat_crud = ChatCRUD()