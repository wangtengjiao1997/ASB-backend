"""
特性（功能）模块，包含各种业务功能的API接口定义
"""

from app.features.user.user_router import router as user_router
from app.features.post.post_router import router as post_router
from app.features.user_feed.user_feed_router import router as user_feed_router


__all__ = ["user_router", "post_router", "user_feed_router"]