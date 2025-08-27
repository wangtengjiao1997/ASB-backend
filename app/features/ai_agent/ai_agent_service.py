from typing import Optional, Dict, Any
from datetime import datetime, UTC
from fastapi import HTTPException
from app.infrastructure.ai_agent.model import deepseek_model
from app.utils.logger_service import logger
from app.entities.user_entity import User


class AIAgentService:
    """
    AI智能决策助手 - Service层
    - 负责业务逻辑与prompt构建
    - 调用model层完成与DeepSeek的连接
    """

    def __init__(self):
        self.model = deepseek_model

    def _build_system_prompt(self) -> str:
        """系统提示词（玄学风格与实用建议结合）"""
        return (
            "你是一位融合古老智慧与现代洞察的智能决策助手。"
            "当用户面临选择困难时，请结合直觉、能量场与理性分析，"
            "用温暖、亲和且实用的方式给出建议。回答结构建议包含："
            "输出结合东方玄学，天罡八卦的一些解释，然后输出最终建议。"
            "输出格式为："
            "```"
            "玄学解释"
            "最终建议"
            "```"
            "输出尽量简洁，控制在几句话内"
        )

    def _build_user_prompt(
        self, user_input: str, context: Optional[str] = None, user: Optional[User] = None
    ) -> str:
        """用户提示词拼装（含上下文与个性化）"""
        parts = [f"我现在面临一个选择困难：{user_input}"]
        if context:
            parts.append(f"补充信息：{context}")
        if user and getattr(user, 'nickname', None):
            parts.append(f"（请称呼我为：{user.nickname}）")
        parts.append(
            "请基于上述信息，给出具有洞察力且可执行的建议，语气温暖、有深度。"
        )
        return "\n\n".join(parts)

    def _analyze_confidence(self, text: str) -> str:
        """简单启发式置信度评估"""
        if len(text) > 500:
            return "高"
        if len(text) > 200:
            return "中"
        return "低"

    async def get_decision_advice(
        self,
        user_input: str,
        context: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        高级版：生成AI决策建议（完整chat接口，带token统计）
        """

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(user_input, context, user)}
        ]
        resp = await self.model.chat_completion(
            messages=messages,
            max_tokens=1000,
            temperature=0.8,
            top_p=0.9
        )
        advice = resp["choices"][0]["message"]["content"]

        return {
            "advice": advice,
            "confidence": self._analyze_confidence(advice),
            "model_used": getattr(self.model, "model", "unknown"),
            "token_usage": resp.get("usage", {}),
            "timestamp": datetime.now(UTC).isoformat()
        }

  

    async def health_check(self) -> Dict[str, Any]:
        """健康检查：仅透传model可用性"""
        ok = await self.model.health_check()
        return {
            "status": "healthy" if ok else "degraded",
            "model_available": ok,
            "message": "服务正常" if ok else "模型暂不可用"
        }