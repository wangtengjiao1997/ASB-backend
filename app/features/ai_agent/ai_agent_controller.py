from typing import Dict, Any
from fastapi import HTTPException
from app.features.ai_agent.ai_agent_service import AIAgentService
from app.schemas.ai_agent_schema import DecisionRequest, DecisionResponse, HealthCheckResponse
from app.entities.user_entity import User
from app.utils.logger_service import logger


class AIAgentController:
    """
    AI智能决策助手控制器
    处理HTTP请求并调用相应的服务方法
    """
    
    def __init__(self):
        self.ai_agent_service = AIAgentService()

    async def get_decision_advice(
        self, 
        request: DecisionRequest, 
        user: User = None
    ) -> DecisionResponse:
        """
        处理获取高级AI决策建议的请求
        
        Args:
            request: 决策请求数据
            user: 当前用户（可选）
            
        Returns:
            AI决策响应
        """

        if not request.user_input or not request.user_input.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": "请输入您的选择困难描述"
                }
            )
        
        # 调用高级服务
        result = await self.ai_agent_service.get_decision_advice(request.user_input, request.context, user)
        return result
            
       
    
    async def health_check(self) -> HealthCheckResponse:
        """
        处理健康检查请求
        
        Returns:
            健康检查响应
        """
        result = await self.ai_agent_service.health_check()
        return result
        
            
        