from app.crud.user_crud import user_crud

from app.crud.follow_crud import follow_crud
from app.crud.like_crud import like_crud
from app.crud.task_crud import task_crud
from app.crud.chat_crud import chat_crud
from app.crud.message_crud import message_crud
from app.crud.report_crud import report_crud
from app.crud.system_config_crud import system_config_crud
from app.crud.live_card_crud import live_card_crud
from app.crud.user_live_card_relation_curd import user_live_card_relation_crud
from app.crud.subscribe_crud import subscribe_crud
# 导出CRUD实例，方便直接导入
__all__ = ["user_crud", "follow_crud", "like_crud", "task_crud", "chat_crud", "message_crud", "report_crud", "system_config_crud", 
           "live_card_crud", "user_live_card_relation_crud", "subscribe_crud"]