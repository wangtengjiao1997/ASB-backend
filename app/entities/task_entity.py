from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import Field
from app.entities.base import BaseDocument


class TaskEntity(BaseDocument):
    """任务实体"""
    task_type: str = Field(default="article_writing", description="任务类型，只能为'article_writing'")
    task_config: Dict[str, Any] = Field(..., description="任务配置，影响机器人行为的信息")
    task_status: str = Field(default="pending", description="任务状态")
    tags: List[str] = Field(default=[], description="任务标签列表")
    bot_id: str = Field(..., description="执行任务的机器人ID")
    trigger_at: Optional[datetime] = Field(default=None, description="任务触发时间，不提供则表示创建后立即触发")
    executed_at: Optional[datetime] = Field(default=None, description="任务执行时间，不提供则表示尚未执行")
    finished_at: Optional[datetime] = Field(default=None, description="任务完成时间，不提供则表示尚未完成")
    result_id: Optional[str] = Field(default=None, description="任务结果ID")
    failure_reason: Optional[str] = Field(default=None, description="任务失败原因")
    on_success_callback_url: Optional[str] = Field(default=None, description="任务成功回调URL")
    on_failure_callback_url: Optional[str] = Field(default=None, description="任务失败回调URL")

    class Settings:
        name = "task"