from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.entities import (User, Follow, Like, TaskEntity, Chat, Message, Report, SystemConfig,
                          LiveCard, UserLiveCardRelation,Subscribe)
from datetime import timezone
# 创建一个全局client变量
client: AsyncIOMotorClient = None

async def init_db():
    # 创建MongoDB客户端
    global client
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        maxPoolSize=100,           # 最大连接数
        minPoolSize=10,            # 最小连接数
        maxIdleTimeMS=30000,       # 连接空闲时间30秒
        serverSelectionTimeoutMS=5000,  # 服务器选择超时5秒
        socketTimeoutMS=20000,     # Socket超时20秒
        connectTimeoutMS=10000,    # 连接超时10秒
        retryWrites=False,          # 启用重试写入
        retryReads=False,           # 启用重试读取
        # w="majority"               # 写关注级别
        tz_aware=True,  # 关键配置
        tzinfo=timezone.utc  # 指定默认时区为UTC
    )
    
    # 初始化Beanie
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            User,
            Follow,
            Like,
            TaskEntity,
            Chat,
            Message,
            Report,
            SystemConfig,
            LiveCard,
            UserLiveCardRelation,
            Subscribe
        ]
    ) 
    return client

def get_client() -> AsyncIOMotorClient:
    """
    获取MongoDB客户端实例
    """
    if client is None:
        raise RuntimeError("Database client not initialized. Call init_db() first.")
    return client