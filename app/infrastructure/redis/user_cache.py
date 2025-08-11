from app.entities.user_entity import User
from typing import Optional, Dict
from app.utils.logger_service import logger
from app.infrastructure.redis.redis_client import redis_client
from cachetools import TTLCache
import asyncio
import time
from typing import Optional, Dict

class UserCache:
    def __init__(self):
        self.redis = redis_client
        self.cache_expire = 3600
        self._operation_timeout = 5.0
        
        # 使用TTLCache，自动过期
        self._memory_cache = TTLCache(
            maxsize=1000,  # 最多缓存1000个用户
            ttl=300        # 5分钟自动过期
        )

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """通过token获取用户数据（使用TTLCache）"""
        if not token:
            return None
        
        token_key = token
        
        # 1. 检查内存缓存（TTLCache自动处理过期）
        if token_key in self._memory_cache:
            user_data = self._memory_cache[token_key]
            return User(**user_data)
        
        # 2. 检查Redis缓存
        try:
            async with asyncio.timeout(self._operation_timeout):
                user_data = await self.redis.get_json(token_key)
                if user_data:
                    # 缓存到内存（TTLCache自动管理过期）
                    self._memory_cache[token_key] = user_data
                    return User(**user_data)
                return None
        except asyncio.TimeoutError:
            logger.warning(f"Redis获取超时: {token_key}")
            return None
        except Exception as e:
            logger.warning(f"Redis获取失败: {e}")
            return None
    
    async def cache_user_by_token(self, token: str, user: User) -> None:
        """缓存用户数据"""
        if not token:
            return
        
        token_key = token
        user_data = user.model_dump(exclude={"password"})
        
        # 立即缓存到内存（TTLCache自动管理过期）
        self._memory_cache[token_key] = user_data
        
        # 异步缓存到Redis
        asyncio.create_task(self._cache_to_redis(token_key, user_data))
    
    async def _cache_to_redis(self, token_key: str, user_data: dict):
        """异步缓存到Redis"""
        try:
            async with asyncio.timeout(self._operation_timeout):
                await self.redis.set_json(token_key, user_data, expire=self.cache_expire)
        except Exception as e:
            logger.warning(f"Redis缓存失败: {e}")
    
    async def invalidate_user(self, user_id: str) -> None:
        """删除用户缓存"""
        # 从内存缓存中删除
        keys_to_remove = []
        for key, user_data in list(self._memory_cache.items()):
            if user_data.get('id') == user_id:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            self._memory_cache.pop(key, None)
            async with asyncio.timeout(self._operation_timeout):
                await self.redis.delete(key)
        # 从Redis删除
        try:
            async with asyncio.timeout(self._operation_timeout):
                for key in keys_to_remove:
                    await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"删除Redis用户缓存失败: {e}")
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        return {
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_maxsize": self._memory_cache.maxsize,
            "memory_cache_currsize": self._memory_cache.currsize,
            "memory_cache_ttl": self._memory_cache.ttl
        }

user_cache = UserCache()