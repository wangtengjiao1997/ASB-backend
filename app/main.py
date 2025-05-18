from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.data_source import init_db
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.features import user_router,post_router, user_feed_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    yield

app = FastAPI(
    title="Asb backend",
    description="""
   
    """,
    version="1.0.0",
    contact={
        "name": "Jack Wang", 
        "email": "wangtengjiao1997@gmail.com"
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
app.add_middleware(ErrorHandlerMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(post_router, prefix="/api/v1/posts", tags=["posts"])

