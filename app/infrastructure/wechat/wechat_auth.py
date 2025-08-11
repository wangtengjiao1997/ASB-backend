from typing import Dict, Optional, Any
from fastapi import HTTPException
import aiohttp
import json
from datetime import datetime, timedelta
from app.core.config import settings
from app.infrastructure.redis.redis_client import redis_client
from app.utils.logger_service import logger

class WechatAuthError(Exception):
    """微信认证相关错误"""
    pass

class WechatAuth:
    def __init__(self):
        self.settings = settings
        self.redis_client = redis_client
        
    async def _request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送HTTP请求到微信服务器"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    # 先获取响应文本
                    response_text = await response.text()
                    logger.info(f"微信API响应: {response_text}")
                    
                    # 检查HTTP状态码
                    if response.status != 200:
                        raise WechatAuthError(f"HTTP错误: {response.status}, 响应: {response_text}")
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        raise WechatAuthError(f"无法解析微信API响应: {response_text}")
                    
                    # 检查微信API错误码
                    if "errcode" in data and data["errcode"] != 0:
                        error_msg = data.get('errmsg', '未知错误')
                        raise WechatAuthError(f"微信API错误 {data['errcode']}: {error_msg}")
                    
                    return data
        except aiohttp.ClientError as e:
            raise WechatAuthError(f"网络请求失败: {str(e)}")
        except Exception as e:
            if isinstance(e, WechatAuthError):
                raise
            raise WechatAuthError(f"请求微信服务器失败: {str(e)}")

    async def code2session(self, code: str) -> Dict[str, Any]:
        """
        使用 code 换取用户的 openid 和 session_key
        
        Args:
            code: 小程序登录时获取的 code
            
        Returns:
            Dict: 包含 openid 和 session_key 的字典
        """
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": self.settings.WECHAT_APP_ID,
            "secret": self.settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code"
        }
        
        try:
            data = await self._request(url, params)
            return {
                "openid": data["openid"],
                "session_key": data["session_key"],
                "unionid": data.get("unionid")  # 如果开发者帐号下存在同主体的公众号，返回 unionid
            }
        except WechatAuthError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except KeyError:
            raise HTTPException(status_code=401, detail="无效的登录凭证")

    async def get_access_token(self) -> str:
        """
        获取小程序全局接口调用凭据
        使用 Redis 缓存 access_token
        """
        # 先从 Redis 获取
        cached_token = await self.redis_client.get("wechat:access_token")
        if cached_token:
            return cached_token
            
        # 如果没有缓存，则从微信服务器获取
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.settings.WECHAT_APP_ID,
            "secret": self.settings.WECHAT_APP_SECRET
        }
        
        try:
            data = await self._request(url, params)
            access_token = data["access_token"]
            expires_in = data["expires_in"]
            
            # 将 token 存入 Redis，设置过期时间比微信服务器返回的时间短一点，确保安全
            await self.redis_client.setex(
                "wechat:access_token",
                expires_in - 300,  # 提前5分钟过期
                access_token
            )
            
            return access_token
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取微信 access_token 失败: {str(e)}"
            )

    async def verify_user_info(self, session_key: str, raw_data: str, signature: str) -> bool:
        """
        验证用户信息的签名
        
        Args:
            session_key: 用户的 session_key
            raw_data: 原始数据字符串
            signature: 签名
            
        Returns:
            bool: 验证是否通过
        """
        import hashlib
        import hmac
        
        try:
            signature_generated = hmac.new(
                session_key.encode(),
                raw_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature == signature_generated
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"验证用户信息失败: {str(e)}"
            )

    async def decrypt_data(self, session_key: str, encrypted_data: str, iv: str) -> Dict[str, Any]:
        """
        解密微信加密数据
        
        Args:
            session_key: 用户的 session_key
            encrypted_data: 加密的数据
            iv: 加密算法的初始向量
            
        Returns:
            Dict: 解密后的数据
        """
        from Crypto.Cipher import AES
        import base64
        
        try:
            # 使用 base64 解码
            session_key = base64.b64decode(session_key)
            encrypted_data = base64.b64decode(encrypted_data)
            iv = base64.b64decode(iv)
            
            # 创建解密器
            cipher = AES.new(session_key, AES.MODE_CBC, iv)
            
            # 解密
            decrypted = cipher.decrypt(encrypted_data)
            
            # 去除补位
            pad = decrypted[-1]
            decrypted = decrypted[:-pad]
            
            # 将解密后的数据转换为字典
            decrypted_data = json.loads(decrypted)
            
            # 检查数据水印
            if decrypted_data["watermark"]["appid"] != self.settings.WECHAT_APP_ID:
                raise WechatAuthError("数据水印验证失败")
                
            return decrypted_data
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"解密数据失败: {str(e)}"
            )