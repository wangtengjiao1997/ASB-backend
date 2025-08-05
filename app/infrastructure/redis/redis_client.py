import json
import asyncio
from typing import Any, Optional, Union, List, Dict
import redis.asyncio as redis
from app.core.config import settings
from app.utils.json_serializer import json_serializer
from app.utils.logger_service import logger

class RedisClient:
    def __init__(self):
        self.redis = None
        self._initialized = False
    
    async def init(self):
        """正确初始化连接池"""
        if self._initialized:
            return
        
        # 先创建连接池
        self._pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            decode_responses=True,
            username=settings.REDIS_USERNAME if settings.REDIS_USERNAME else None,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            
            # 连接池配置
            max_connections=2000,  # 适中的连接数
            retry_on_timeout=True,
            retry_on_error=[redis.ConnectionError, redis.TimeoutError],
            socket_timeout=30,
            socket_connect_timeout=15,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # 使用连接池创建Redis客户端
        self.redis = redis.Redis(connection_pool=self._pool)
        
        try:
            await self.redis.ping()
            self._initialized = True

        except Exception as e:
            raise Exception(f"Redis连接失败: {e}")

    async def close(self):
        """正确关闭连接池"""
        if self.redis:
            await self.redis.aclose()
        if self._pool:
            await self._pool.aclose()
        self._initialized = False
    
    # 添加连接池状态监控
    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "max_connections": self._pool.max_connections,
            "created_connections": self._pool.created_connections,
            "available_connections": len(self._pool._available_connections),
            "in_use_connections": len(self._pool._in_use_connections),
        }
    
    def generate_key(self, key: str) -> str:
        """生成带前缀的键名"""
        return f"{settings.REDIS_PREFIX}{key}"
    
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值（只加超时控制）"""
        full_key = self.generate_key(key)
        try:
            # 只加超时控制，其他什么都不改
            async with asyncio.timeout(10.0):  # 3秒超时
                return await self.redis.get(full_key)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            # 只在连接池耗尽时记录错误
            if "max number of clients" in str(e).lower():
                logger.error(f"Redis连接池耗尽: {self.get_pool_status()}")
            raise
    
    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """设置字符串值（只加超时控制）"""
        full_key = self.generate_key(key)
        if expire is None:
            expire = getattr(settings, 'REDIS_DEFAULT_EXPIRE', 3600)
        
        try:
            # 只加超时控制
            async with asyncio.timeout(10.0):  # 3秒超时
                return await self.redis.set(full_key, value, ex=expire)
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            # 只在连接池耗尽时记录错误
            if "max number of clients" in str(e).lower():
                logger.error(f"Redis连接池耗尽: {self.get_pool_status()}")
            raise
    
    async def delete(self, *keys: str) -> int:
        """删除键 - 支持批量删除"""
        if not keys:
            return 0
        full_keys = [self.generate_key(key) for key in keys]
        return await self.redis.delete(*full_keys)
    
    # JSON操作
    async def set_json(self, key: str, value: Any, expire: int = None) -> bool:
        """保存JSON数据"""
        try:
            # 尝试直接序列化
            json_value = json.dumps(value, ensure_ascii=False)
        except TypeError:
            # 如果失败，使用自定义编码器
            json_value = json.dumps(value, default=json_serializer, ensure_ascii=False)
        
        return await self.set(key, json_value, expire)

    async def get_json(self, key: str) -> Any:
        """获取JSON数据"""
        json_value = await self.get(key)
        if json_value:
            try:
                return json.loads(json_value)
            except json.JSONDecodeError:
                return None
        return None
redis_client = RedisClient()