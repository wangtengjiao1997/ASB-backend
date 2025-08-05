from app.schemas.task_schema import TaskCreate, TaskResponse, ArticleWritingTask, ArticleWritingTaskCallback, ContentCreationTaskCallback, ContentCreationTask, LiveCardCreationTask, LiveCardCreationTaskCallback
from app.features.task.task_service import TaskService
from typing import Any, Optional, List, Dict


class TaskController:
    @staticmethod
    async def create_task(task_data: TaskCreate) -> TaskResponse:
        """
        创建通用任务
        
        Args:
            task_data: 任务数据
        
        Returns:
            TaskResponse: 任务创建结果
        """
        return await TaskService.create_task(task_data)
    
    @staticmethod
    async def create_article_task(task_data: ArticleWritingTask) -> TaskResponse:
        """
        创建文章任务
        
        Args:
            task_data: 文章任务数据
        
        Returns:
            TaskResponse: 任务创建结果
        """
        return await TaskService.create_article_task(task_data)
    
    @staticmethod
    async def create_content_creation_task(task_data: ContentCreationTask) -> TaskResponse:
        """
        创建内容创建任务
        """
        return await TaskService.create_content_creation_task(task_data)
    
    @staticmethod
    async def create_live_card_task(task_data: LiveCardCreationTask) -> TaskResponse:
        """
        创建直播卡片任务
        """
        return await TaskService.create_live_card_task(task_data)
    
    @staticmethod
    async def create_live_card_task_callback(live_card_task_callback: LiveCardCreationTaskCallback) -> TaskResponse:
        """
        创建直播卡片任务回调
        """
        return await TaskService.create_live_card_task_callback(live_card_task_callback)
    
    @staticmethod
    async def create_article_task_callback(bot_id: str, task_id: str, failure_reason: Optional[str] = None, article: Optional[ArticleWritingTaskCallback] = None) -> TaskResponse:
        """
        创建文章任务回调
        """
        return await TaskService.create_article_task_callback(bot_id, task_id, failure_reason, article)
    
    @staticmethod
    async def create_content_task_callback(bot_id: str, task_id: str, failure_reason: Optional[str] = None, article: Optional[ContentCreationTaskCallback] = None) -> TaskResponse:
        """
        创建内容创建任务回调
        """
        return await TaskService.create_content_task_callback(bot_id, task_id, failure_reason, article)
    
    @staticmethod
    async def get_task(task_id: str) -> TaskResponse:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
        
        Returns:
            TaskResponse: 任务详情
        """
        return await TaskService.get_task(task_id)
    
    @staticmethod
    async def get_tasks(
        skip: int = 0, 
        limit: int = 10,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[TaskResponse]:
        """
        获取任务列表
        
        Args:
            skip: 跳过数量
            limit: 限制数量
            status: 任务状态
            task_type: 任务类型
        
        Returns:
            List[TaskResponse]: 任务列表
        """
        return await TaskService.get_tasks(skip, limit, status, task_type)

    @staticmethod
    async def auto_post(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动发帖
        """
        return await TaskService.auto_post(data)
    
    @staticmethod
    async def create_discord_bot_task(task_data: Dict[str, Any]) -> TaskResponse:
        """
        创建Discord机器人任务
        """
        return await TaskService.create_discord_bot_task(task_data)