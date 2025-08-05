from fastapi import APIRouter, Depends, Body, Query
from app.features.task.task_controller import TaskController
from app.schemas.task_schema import (
    TaskResponse, TaskCreate, ArticleWritingTask, ArticleWritingTaskCallback, ContentCreationTaskCallback, ContentCreationTask, LiveCardCreationTask, LiveCardCreationTaskCallback
)
from typing import Dict, Optional, List, Any, Union
from app.schemas.response_schema import BaseResponse
from pydantic import BaseModel, Field
from app.utils.logger_service import logger

router = APIRouter(prefix="/task", tags=["任务管理"])

class ArticleTaskCallback(BaseModel):
    bot_id: Optional[str] = None
    task_id: str
    failure_reason: Optional[str] = None
    article: Union[ArticleWritingTaskCallback, ContentCreationTaskCallback] | None = Field(default=None, union_mode="smart")

class ContentTaskCallback(BaseModel):
    bot_id: Optional[str] = None
    task_id: str
    failure_reason: Optional[str] = None
    article: ContentCreationTaskCallback | None = Field(default=None)

@router.post("/create", response_model=BaseResponse[TaskResponse])
async def create_task(task_data: TaskCreate):
    """创建通用任务"""
    data = await TaskController.create_task(task_data)
    return BaseResponse.success(data=data)

@router.post("/create_content_creation_task", response_model=BaseResponse[TaskResponse])
async def create_content_creation_task(task_data: ContentCreationTask):
    """创建内容创建任务"""
    data = await TaskController.create_content_creation_task(task_data)
    return BaseResponse.success(data=data)

@router.post("/create_article_task", response_model=BaseResponse[TaskResponse])
async def create_article_task(task_data: ArticleWritingTask):
    """创建文章任务"""
    data = await TaskController.create_article_task(task_data)
    return BaseResponse.success(data=data)

@router.post("/create_live_card_task", response_model=BaseResponse[TaskResponse])
async def create_live_card_task(task_data: LiveCardCreationTask):
    """创建直播卡片任务"""
    data = await TaskController.create_live_card_task(task_data)
    return BaseResponse.success(data=data)

@router.post("/create_live_card_task_callback", response_model=BaseResponse[TaskResponse])
async def create_live_card_task_callback(live_card_task_callback: LiveCardCreationTaskCallback):
    """创建直播卡片任务回调"""
    data = await TaskController.create_live_card_task_callback(live_card_task_callback)
    return BaseResponse.success(data=data)

@router.post("/create_article_task_callback", response_model=BaseResponse[TaskResponse])
async def create_article_task_callback(article_task_callback: ArticleTaskCallback):
    """创建文章任务回调"""
    if isinstance(article_task_callback.article, ArticleWritingTaskCallback):
        data = await TaskController.create_article_task_callback(article_task_callback.bot_id, article_task_callback.task_id, article_task_callback.failure_reason, article_task_callback.article)
    elif isinstance(article_task_callback.article, ContentCreationTaskCallback):
        data = await TaskController.create_content_task_callback(article_task_callback.bot_id, article_task_callback.task_id, article_task_callback.failure_reason, article_task_callback.article)
    else:
        logger.warning(f"Failed to create task callback, article is not a valid type: {article_task_callback.article}")
        data = TaskResponse(task_id=article_task_callback.task_id, status="failed", message=article_task_callback.failure_reason)
    return BaseResponse.success(data=data)

@router.post("/create_content_task_callback", response_model=BaseResponse[TaskResponse])
async def create_content_task_callback(content_task_callback: ContentTaskCallback):
    """创建内容任务回调"""
    data = await TaskController.create_content_task_callback(content_task_callback.bot_id, content_task_callback.task_id, content_task_callback.failure_reason, content_task_callback.article)
    return BaseResponse.success(data=data)

# @router.post("/scraper_callback", response_model=BaseResponse[TaskResponse])
# async def scraper_callback(scraper_callback: ScraperCallback):
#     """创建爬虫任务回调"""
#     data = await TaskController.scraper_callback(scraper_callback.task_id, scraper_callback.failure_reason, scraper_callback.article)
#     return BaseResponse.success(data=data)

@router.get("/{task_id}", response_model=BaseResponse[TaskResponse])
async def get_task(task_id: str):
    """获取任务详情"""
    data = await TaskController.get_task(task_id)
    return BaseResponse.success(data=data)

@router.get("/", response_model=BaseResponse[List[TaskResponse]])
async def get_tasks(
    skip: int = 0, 
    limit: int = 10,
    status: Optional[str] = None,
    task_type: Optional[str] = None
):
    """获取任务列表"""
    data = await TaskController.get_tasks(skip, limit, status, task_type)
    return BaseResponse.success(data=data)

@router.post("/discord_bot/create_task", response_model=BaseResponse[TaskResponse])
async def create_discord_bot_task(task_data: Dict[str, Any]):
    """创建Discord机器人任务"""
    data = await TaskController.create_discord_bot_task(task_data)
    return BaseResponse.success(data=data)

@router.post("/discord_bot/auto_post", response_model=BaseResponse[Dict[str, Any]])
async def auto_post(data: Dict[str, Any]):
    """自动发帖"""
    data = await TaskController.auto_post(data)
    return BaseResponse.success(data=data)