from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.data_source import init_db
from app.middleware.error_handler import register_error_handler
from contextlib import asynccontextmanager

from app.features import (
    user_router, follow_router, like_router, subscribe_router,
    task_router, aichat_router, app_router, report_router,
    system_config_router, live_card_router, user_live_card_relation_router
)
from app.utils.logger_service import logger
from app.infrastructure.redis.redis_client import redis_client
from app.middleware.auth_middleware import AuthMiddleware
from app.infrastructure.notification.fcm_service import fcm_service
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    负责资源的初始化和清理
    """
    global redis_client
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")

        # 初始化Redis连接
        await redis_client.init()
        logger.info("Redis连接成功")

        await fcm_service.initialize()
        logger.info("FCM服务初始化完成")

        yield  # 应用运行期间

    except Exception as e:
        logger.error(f"应用初始化失败: {str(e)}")
        raise
    finally:
        # 这里可以添加资源清理代码
        if redis_client and redis_client.redis:
            try:
                await redis_client.redis.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接时出错: {str(e)}")


app = FastAPI(
    title="undefined backend",
    description="""
   
    """,
    version="1.0.0",
    contact={
        "name": "undefined", 
        "email": "undefined"
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 以正确的顺序添加中间件
# 错误处理中间件应该最先添加，这样它可以捕获其他中间件中的错误
register_error_handler(app)
app.add_middleware(AuthMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(follow_router, prefix="/api/v1", tags=["follows"])
app.include_router(subscribe_router, prefix="/api/v1", tags=["subscribes"])
app.include_router(like_router, prefix="/api/v1", tags=["likes"])
app.include_router(task_router, prefix="/api/v1", tags=["tasks"])
app.include_router(aichat_router, prefix="/api/v1", tags=["aichat"])
app.include_router(app_router, prefix="/api/v1", tags=["app"])
app.include_router(report_router, prefix="/api/v1", tags=["reports"])
app.include_router(system_config_router, prefix="/api/v1", tags=["system_config"])
app.include_router(live_card_router, prefix="/api/v1", tags=["live_cards"])
app.include_router(user_live_card_relation_router, prefix="/api/v1", tags=["user_live_card_relation"])