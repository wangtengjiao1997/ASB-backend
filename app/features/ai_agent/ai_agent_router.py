from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.features.ai_agent.ai_agent_controller import AIAgentController
from app.schemas.ai_agent_schema import DecisionRequest, DecisionResponse, HealthCheckResponse
from app.schemas.response_schema import BaseResponse
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_optional, get_current_user_required


router = APIRouter(prefix="/ai-agent", tags=["AI智能决策助手"])


@router.post("/decision", response_model=BaseResponse[DecisionResponse])
async def get_decision_advice(
    request: DecisionRequest,
    user: User = Depends(get_current_user_optional),
    ai_agent_controller: AIAgentController = Depends(AIAgentController)
):
    """
    获取AI智能决策建议（高级版）
    
    使用完整的chat completion API，提供更详细的token使用统计和更精确的控制参数。
    适合需要更精细控制和统计的场景。
    
    Args:
        request: 包含用户输入和上下文的决策请求
        user: 当前用户（可选，用于个性化建议）
        
    Returns:
        包含详细AI建议和统计信息的响应数据
    """
    try:
        data = await ai_agent_controller.get_decision_advice(request, user)
        return BaseResponse.success(data=data, message="高级AI决策建议生成成功")
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "高级AI决策服务暂时不可用，请稍后重试"
            }
        )


@router.post("/decision/authenticated", response_model=BaseResponse[DecisionResponse])
async def get_decision_advice_authenticated(
    request: DecisionRequest,
    user: User = Depends(get_current_user_required),
    ai_agent_controller: AIAgentController = Depends(AIAgentController)
):
    """
    获取AI智能决策建议（需要认证）
    
    与普通决策接口相比，这个接口需要用户登录，可以提供更加个性化的建议
    
    Args:
        request: 包含用户输入和上下文的决策请求
        user: 当前已认证用户
        
    Returns:
        包含个性化AI建议的响应数据
    """
    try:
        data = await ai_agent_controller.get_decision_advice(request, user)
        return BaseResponse.success(data=data, message="个性化AI决策建议生成成功")
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "AI决策服务暂时不可用，请稍后重试"
            }
        )


@router.get("/health", response_model=BaseResponse[HealthCheckResponse])
async def health_check(
    ai_agent_controller: AIAgentController = Depends(AIAgentController)
):
    """
    检查AI服务健康状态
    
    用于监控AI决策服务和DeepSeek模型的可用性
    
    Returns:
        服务健康状态信息
    """
    try:
        data = await ai_agent_controller.health_check()
        return BaseResponse.success(data=data, message="健康检查完成")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "健康检查失败"
            }
        )
