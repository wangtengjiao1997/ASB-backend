from typing import List, Optional, Dict, Any, Tuple
from app.entities.task_entity import TaskEntity
from app.schemas.task_schema import TaskCreate, TaskUpdate
from app.crud.base_crud import BaseCRUD
from datetime import datetime


class TaskCRUD(BaseCRUD[TaskEntity, TaskCreate, TaskUpdate]):
    def __init__(self):
        super().__init__(TaskEntity)
    
    async def update_task_status(self, task_id: str, status: str) -> Optional[TaskEntity]:
        """更新任务状态"""
        task = await self.get(task_id)
        if task:
            task.task_status = status
            task.updated_at = datetime.now()
            await task.save()
        return task
    
    async def update_task_result(self, task_id: str, result_id: str) -> Optional[TaskEntity]:
        """更新任务结果ID"""
        task = await self.get(task_id)
        if task:
            task.result_id = result_id
            task.updated_at = datetime.now()
            await task.save()
        return task
    
    async def add_followed_task(self, task_id: str, followed_task_id: str) -> Optional[TaskEntity]:
        """添加后续任务"""
        task = await self.get(task_id)
        if task:
            if task.followed_tasks is None:
                task.followed_tasks = []
            
            if followed_task_id not in task.followed_tasks:
                task.followed_tasks.append(followed_task_id)
                await task.save()
                
        return task


# 创建单例实例
task_crud = TaskCRUD()