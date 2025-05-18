from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.entities import Post, User
# 创建一个全局client变量
client: AsyncIOMotorClient = None

async def init_db():
    # 创建MongoDB客户端
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # 初始化Beanie
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Post,
            User
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