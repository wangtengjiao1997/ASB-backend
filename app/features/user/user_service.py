# app/features/user/user_service.py
from typing import Dict, Any, Optional
from app.schemas.user_schema import UserCreate, UserUpdate, UserProfileResponse
from app.entities.user_entity import User
from app.crud import user_crud, system_config_crud
from fastapi import HTTPException
from datetime import datetime, UTC
from app.utils.logger_service import logger
from app.infrastructure.redis.user_cache import user_cache
from app.infrastructure.wechat.wechat_auth import WechatAuth

class UserService:

    def __init__(self):
        self.user_crud = user_crud
        self.system_config_crud = system_config_crud
        self.user_cache = user_cache
        self.wechat_auth = WechatAuth()

    async def sync_user(self, token: str, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        微信小程序登录 + 可选用户资料写入
        - 支持两种 user_info 形态：
          1) 明文：{ nickname/nickName, avatar_url/avatarUrl, gender, country, province, city, language }
          2) 加密：{ encrypted_data, iv, signature, raw_data }
        """
        try:
            # 1. code -> openid, session_key
            wechat_data = await self.wechat_auth.code2session(token)
            openid = wechat_data["openid"]
            session_key = wechat_data["session_key"]

            # 2. 查找或创建用户（确保language为字符串，避免MongoDB text index语言覆盖字段报错）
            user = await self.user_crud.get_by_wechat_openid(openid)
            if not user:
                create_data = UserCreate(
                    wechat_openid=openid,
                    wechat_unionid=wechat_data.get("unionid"),
                    # 若你的实体/schema已有默认字符串，这里可省略
                    # language="zh-CN",
                    metadata={
                        "wechat_data": wechat_data,
                        "register_time": datetime.now(UTC).isoformat()
                    },
                    nickname=user_info.get("nickname") if user_info else None,
                    avatar_url=user_info.get("avatar_url") if user_info else None,
                    gender=user_info.get("gender") if user_info else None
                )
                user = await self.user_crud.create(create_data)

            # 4. 缓存会话（openid -> session_key, user 映射）
            await self.user_cache.cache_user_by_token(
                token=token,
                user=user
            )

            # 5. 返回
            return {
                "session_info": {
                    "session_key": session_key,
                    "openid": openid
                },
                "token": token,
                "user": user.model_dump()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"微信登录失败: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail={
                    "code": 401,
                    "message": f"微信登录失败: {str(e)}"
                }
            )

    async def update_user_info(self, user_id: str, user_info: UserUpdate) -> User:
        user = await self.user_crud.get(user_id)
        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": 401,
                    "message": "用户不存在"
                }
            )
        user = await self.user_crud.update(user_id, user_info)
        return user

    async def get_current_user(self, token: str) -> User:
        cached_user = await self.user_cache.get_user_by_token(token)
        if cached_user:
            local_user=cached_user
        else:
            local_user = await self.wechat_auth.code2session(token)
            await self.user_cache.cache_user_by_token(
                token=token,
                user=local_user
            )
            if not local_user:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": 401,
                        "message": "用户不存在"
                    }
                )
        return local_user
