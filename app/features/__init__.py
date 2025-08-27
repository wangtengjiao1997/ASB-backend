"""
特性（功能）模块，包含各种业务功能的API接口定义
"""

from app.features.user.user_router import router as user_router
from app.features.ai_agent.ai_agent_router import router as ai_agent_router

__all__ = ["user_router", "ai_agent_router"]