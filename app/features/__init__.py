"""
特性（功能）模块，包含各种业务功能的API接口定义
"""

from app.features.user.user_router import router as user_router
from app.features.follow.follow_router import router as follow_router    
from app.features.like.like_router import router as like_router
from app.features.task.task_router import router as task_router
from app.features.aichat.aichat_router import router as aichat_router
from app.features.app_router import router as app_router
from app.features.report.report_router import router as report_router
from app.features.system_config.system_config_router import router as system_config_router
from app.features.live_card.live_card_router import router as live_card_router
from app.features.user_live_card_relation.user_live_card_relation_router import router as user_live_card_relation_router
from app.features.subscribe.subscribe_router import router as subscribe_router

__all__ = ["user_router", "follow_router", "like_router", "task_router", "aichat_router", "app_router", "report_router",
            "system_config_router", "live_card_router", "user_live_card_relation_router", "subscribe_router"]