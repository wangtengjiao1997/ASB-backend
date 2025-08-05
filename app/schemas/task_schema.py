from pydantic import BaseModel, Field, AnyUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from datetime import UTC

class TaskBase(BaseModel):
    """任务基类"""
    task_type: str = Field(default="article_writing", description="任务类型，只能为'article_writing'")
    task_config: Dict[str, Any] = Field(..., description="任务配置")
    task_status: str = Field(default="pending", description="任务状态")
    tags: List[str] = Field(default=[], description="任务标签列表")
    bot_id: str = Field(..., description="执行任务的机器人ID")
    trigger_at: Optional[datetime] = Field(default=None, description="任务触发时间")
    executed_at: Optional[datetime] = Field(default=None, description="任务执行时间")
    finished_at: Optional[datetime] = Field(default=None, description="任务完成时间")
    result_id: Optional[str] = Field(default=None, description="任务结果ID")
    failure_reason: Optional[str] = Field(default=None, description="任务失败原因")


    class Config:
        from_attributes = True

class TaskCreate(TaskBase):
    """创建任务"""
    pass

class TaskUpdate(BaseModel):
    """更新任务"""
    task_type: Optional[str] = Field(default="article_writing", description="任务类型，只能为'article_writing'")
    task_config: Optional[Dict[str, Any]] = Field(default=None, description="任务配置")
    task_status: Optional[str] = Field(default="pending", description="任务状态")
    tags: Optional[List[str]] = Field(default=[], description="任务标签列表")
    bot_id: Optional[str] = Field(default=None, description="执行任务的机器人ID")
    trigger_at: Optional[datetime] = Field(default=None, description="任务触发时间")
    executed_at: Optional[datetime] = Field(default=None, description="任务执行时间")
    finished_at: Optional[datetime] = Field(default=None, description="任务完成时间")
    result_id: Optional[str] = Field(default=None, description="任务结果ID")
    failure_reason: Optional[str] = Field(default=None, description="任务失败原因")

class ArticleWritingTaskConfig(BaseModel):
    """文章配置信息"""
    topic: Optional[str] = Field(None, description="The main topic of the article to be written.")
    description: Optional[str] = Field(None, description="The description of the article to be written.")
    references: Optional[List[str]] = Field(None, description="A list of documents used as references to write the article.")
    content_style_instructions: Optional[str] = Field(None, description="The style instructions for the article content.")
    include_media_types: Optional[List[str]] = Field(None, description="Media types that should be included in the article.")
    exclude_media_types: Optional[List[str]] = Field(None, description="Media types that should be excluded from the article.")
    enable_research: bool = Field(False, description="Whether to enable (deep-)research before writing the article.")
    research_urls_constraints: Optional[List[AnyUrl]] = Field(None, description="Constraint the bot to only research on these URLs and their sub-pages.")
    research_domains_constraints: Optional[List[str]] = Field(None, description="Constraint the bot to only research on these domains.")

class DiscordBotTask(BaseModel):
    """Discord机器人任务"""
    task_id: str = Field(..., description="The ID of the task.")
    task: Dict[str, Any] = Field(..., description="The configuration of the task.")
    on_success_callback_url: Optional[str] = Field(None, description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: Optional[str] = Field(None, description="The callback URL to send back the failure reason when failed.")

class ArticleWritingTask(TaskBase):
    """创建文章任务"""
    task: Optional[Dict[str, Any]] = Field(default=None, description="The configuration of the task.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")

class ContentCreationTask(BaseModel):
    """创建内容任务"""
    task: Optional[Dict[str, Any]] = Field(default=None, description="The configuration of the task.")
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")

class LiveCardCreationTask(BaseModel):
    """创建直播卡片任务"""
    task: Optional[Dict[str, Any]] = Field(default=None, description="The configuration of the task.")
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    live_card_id: str = Field(..., description="The ID of the live card that should be created.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")

class ArticleWritingRequest(BaseModel):
    """AI创建文章请求"""
    task_id: str = Field(..., description="The ID of the task.")
    task_config: Dict[str, Any] = Field(..., description="The configuration of the task.")
    task_status: str = Field(default="pending", description="The status of the task.")
    tags: List[str] = Field(default=[], description="A list of tags of the task.")
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    created_at: datetime = Field(..., description="The creation time of the task.")
    trigger_at: Optional[datetime] = Field(None, description="The time when the task will be triggered.")
    executed_at: Optional[datetime] = Field(None, description="The time when the task was executed.")
    finished_at: Optional[datetime] = Field(None, description="The time when the task was finished.")
    result_id: Optional[str] = Field(None, description="The task's result ID.")
    failure_reason: Optional[str] = Field(None, description="The reason why the task failed.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")

class LiveCardCreationTaskCallback(BaseModel):
    """直播卡片任务回调"""
    bot_id: str = Field(default="", description="bot_id")
    task_id: str = Field(default="", description="live_card_id")
    live_card_id: str = Field(default="", description="live_card_id")
    article: Dict[str, Any] = Field(default={}, description="article")
    failure_reason: Optional[str] = Field(default=None, description="The reason why the task failed.")

class ContentCreationTaskCallback(BaseModel):
    """内容创建任务回调"""
    title: str = Field(..., description="The title of the article.")
    tags: List[str] = Field(default=[], description="The tags of the article.")
    blocks: List[Dict[str,Any]] = Field(default=[], description="The blocks of the article.")
    raw_markdown_content: Optional[str] = Field(default = "", description="The raw markdown of the article.")
    raw_html_content: Optional[str] = Field(default = "", description="The raw html of the article.")
    raw_summary: Optional[str] = Field(default = "", description="The raw summary of the article.")

class ArticleWritingTaskCallback(BaseModel):
    """文章任务回调"""
    article_id: Optional[str] = Field(None, description="The ID of the article.")
    task_id: Optional[str] = Field(None, description="The ID of the task.")
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    title: str = Field(..., description="The title of the article.")
    content: str = Field(..., description="The content of the article.")
    medias: Dict[str,str] = Field(default={}, description="The medias of the article.")
    summary: str = Field(..., description="The summary of the article.")
    references: List[str] = Field(default=[], description="The references of the article.")
    updated_task_body: Optional[Dict[str, Any]] = Field(None, description="The updated task body.")

class ContentCreationTaskRequest(BaseModel):
    """内容创建任务"""
    profile: Dict[str, Any] = Field(..., description="The profile of the content creation task.")
    content_creation_task_config: Dict[str, Any] = Field(..., description="The configuration of the content creation task.")
    tools: List[Any] = Field(..., description="The tools of the content creation task.")
    task: Dict[str, Any] = Field(..., description="The task of the content creation task.")
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")

class LiveCardCreationTaskRequest(BaseModel):
    """直播卡片创建任务"""
    bot_id: str = Field(..., description="The ID of the bot that should execute this task.")
    live_card_id: str = Field(..., description="The ID of the live card that should be created.")
    on_success_callback_url: str = Field(..., description="The callback URL to send back the task result when successful.")
    on_failure_callback_url: str = Field(..., description="The callback URL to send back the failure reason when failed.")
    live_card_creation_task_config: Dict[str, Any] = Field(..., description="The configuration of the live card creation task.")
    task: Dict[str, Any] = Field(..., description="The task of the live card creation task.")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None