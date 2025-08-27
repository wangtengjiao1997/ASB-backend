import httpx
import json
from typing import Dict, Any, List, Optional
from app.utils.logger_service import logger
from app.core.config import settings
from openai import OpenAI

class DeepSeekModel:
    """
    DeepSeek AI 模型连接类
    只负责与DeepSeek API的连接和基础调用功能
    """
    
    def __init__(self):
        # 重新添加配置，因为用户回退了config更改
        self.settings = settings
        self.api_key = self.settings.DEEPSEEK_API_KEY
        self.base_url = self.settings.DEEPSEEK_BASE_URL
        self.model = "deepseek-chat"
        
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，请设置环境变量 DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30.0
        )
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.8,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        调用DeepSeek聊天完成API
        
        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            top_p: Top-p采样参数
            
        Returns:
            API响应结果
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # 将 OpenAI 响应对象转换为字典格式
            return {
                "choices": [
                    {
                        "message": {
                            "role": response.choices[0].message.role,
                            "content": response.choices[0].message.content
                        },
                        "finish_reason": response.choices[0].finish_reason,
                        "index": response.choices[0].index
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "id": response.id,
                "created": response.created
            }
                    
        except Exception as e:
            logger.error(f"DeepSeek API 调用异常: {str(e)}")
            if "timeout" in str(e).lower():
                raise Exception("AI服务响应超时，请稍后重试")
            elif "401" in str(e) or "authentication" in str(e).lower():
                raise Exception("API密钥无效，请检查 DEEPSEEK_API_KEY 配置")
            elif "429" in str(e):
                raise Exception("API调用频率限制，请稍后重试")
            else:
                raise Exception(f"AI服务异常: {str(e)}")
    
    async def function_call(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]] = None,
        tool_choice: str = None
    ) -> Dict[str, Any]:
        """
        支持function calling的API调用
        
        Args:
            messages: 对话消息列表
            functions: 可用函数定义列表
            function_call: 指定调用的函数
            
        Returns:
            API响应结果
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.1  # function call 时使用较低温度
            }
            
            if tools:
                kwargs["tools"] = tools
                
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
            
            response = await self.client.chat.completions.create(**kwargs)
            
            # 转换为字典格式
            choices = []
            for choice in response.choices:
                choice_dict = {
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "finish_reason": choice.finish_reason,
                    "index": choice.index
                }
                
                # 如果有工具调用
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    choice_dict["message"]["tool_calls"] = [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in choice.message.tool_calls
                    ]
                
                choices.append(choice_dict)
            
            return {
                "choices": choices,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "id": response.id,
                "created": response.created
            }
                    
        except Exception as e:
            logger.error(f"Function call API 异常: {str(e)}")
            raise Exception(f"Function call服务异常: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        检查 DeepSeek API 服务健康状态
        """
        if not self.api_key or self.api_key == "placeholder":
            return False
            
        try:
            # 使用简单的测试消息检查连接
            await self.chat_completion([{"role": "user", "content": "测试连接"}])
            return True
        except Exception as e:
            logger.warning(f"DeepSeek API 健康检查失败: {str(e)}")
            return False

deepseek_model = DeepSeekModel()