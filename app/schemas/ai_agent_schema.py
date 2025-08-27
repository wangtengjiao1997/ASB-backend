from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class DecisionRequest(BaseModel):
    """AI决策请求模型"""
    user_input: str = Field(..., description="用户的选择困难描述", min_length=1, max_length=1000)
    context: Optional[str] = Field(None, description="额外的上下文信息", max_length=500)


class DecisionResponse(BaseModel):
    """AI决策响应模型"""
    advice: str = Field(..., description="AI给出的智慧建议")
    confidence: str = Field(..., description="建议的置信度")
    model_used: str = Field(..., description="使用的AI模型")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token使用统计")
    timestamp: Optional[str] = Field(None, description="生成时间戳")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    model_available: bool = Field(..., description="AI模型是否可用")
    message: str = Field(..., description="状态描述")
    
    class Config:
        case_sensitive = True
