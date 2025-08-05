from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
import httpx
import json
import logging

from app.entities.task_entity import TaskEntity
from app.schemas.task_schema import (ArticleWritingTask, TaskResponse, TaskCreate, ArticleWritingTaskCallback,
                                      TaskUpdate, ArticleWritingTaskConfig, ArticleWritingRequest, ContentCreationTaskRequest,
                                        ContentCreationTaskCallback, ContentCreationTask, LiveCardCreationTask, LiveCardCreationTaskCallback, LiveCardCreationTaskRequest)
from app.schemas.live_card_schema import LiveCardUpdate
from app.core.config import settings
from app.crud import task_crud, chat_crud, message_crud, user_crud, live_card_crud
from app.utils.logger_service import logger
from app.utils.json_serializer import dumps
from fastapi import HTTPException
from app.schemas.ai_schema.message_schema import MessageCreate
from app.infrastructure.notification.fcm_service import fcm_service
from app.features.live_card.live_card_service import LiveCardService
from app.utils.live_card_mapper import transform_ai_to_entity, transform_entity_to_ai, metadata_increment, get_update_increment

class TaskService:
    @staticmethod
    async def create_task(task_data: TaskCreate) -> TaskResponse:
        """
        创建通用任务
        """
        try:
            user = await user_crud.get(task_data.user_id)
            if not user:
                raise ValueError(f"user不存在 {task_data.user_id}")
            # 创建本地任务记录
            task = TaskEntity(
                task_type=task_data.task_type,
                task_config=task_data.task_config,
                tags=task_data.tags,
                task_status=task_data.task_status,
                user_id=task_data.user_id,
                trigger_at=task_data.trigger_at,
                executed_at=task_data.executed_at,
                finished_at=task_data.finished_at,
                result_id=task_data.result_id,
                failure_reason=task_data.failure_reason,
            )
        
            created_task = await task_crud.create(task)
            
            return TaskResponse(
                task_id=str(created_task.id),
                status=created_task.task_status,
                message="任务创建成功",
                created_at=created_task.created_at
            )
        except HTTPException as e:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": f"创建任务失败: {str(e)}"
                }
            )
        
    @staticmethod
    async def create_content_creation_task(task_data: ContentCreationTask) -> TaskResponse:
        """
        创建内容创建任务
        """
        try:
            user = await user_crud.get(task_data.user_id)
            if not user:
                raise ValueError(f"user不存在 {task_data.user_id}")
            agent_config = agent.get_config_dict()
            
            ai_service_url = settings.AI_CONTENT_CREATION_BOT_BASE_URL

            article_writing_task = ContentCreationTaskRequest(
                profile=agent_config.get("profile", {}),
                content_creation_task_config=agent_config.get("content_creation_task_config", {}),
                tools=agent_config.get("tools", []),
                task=task_data.task if task_data.task else {},
                user_id=user.id,
                on_success_callback_url=task_data.on_success_callback_url,
                on_failure_callback_url=task_data.on_failure_callback_url,
            )
            print(f"------------------article_writing_task--------------------------------\n: {article_writing_task}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    ai_service_url,
                    data=dumps(article_writing_task.model_dump()),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return TaskResponse(
                        task_id="create_content_creation_task",
                        status="success",
                        message="内容创建任务已成功创建并分配给AI服务",
                        created_at=datetime.now(UTC),
                    )
                else:
                    logging.error(f"AI服务创建任务失败: {response.status_code} - {response.text}")
                    return TaskResponse(
                        task_id="create_content_creation_task",
                        status="failed",
                        message=f"任务创建失败: {response.text}",
                        created_at=datetime.now(UTC),
                    )
        except HTTPException as e:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": f"创建任务失败: {str(e)}"
                }
            )
        except Exception as e:
            logging.exception("调用AI服务创建任务时发生异常")
            return TaskResponse(
                task_id="create_content_creation_task",
                status="failed",
                message=f"任务创建失败: {str(e)}",
                created_at=datetime.now(UTC),
            )

    @staticmethod
    async def create_live_card_task(task_data: LiveCardCreationTask) -> TaskResponse:
        """
        创建直播卡片任务
        """

        user = await user_crud.get(task_data.user_id)
        if not user:
            raise ValueError(f"user不存在 {task_data.user_id}")
        agent_data = agent.model_dump_with_json_config()
        agent_config = agent_data.get("config", {})
        live_card_info = await live_card_crud.get(task_data.live_card_id)
        if not live_card_info:
            raise ValueError(f"直播卡片不存在 {task_data.live_card_id}")
        
        live_card_items = await live_card_item_crud.get_live_card_item_by_live_card_id(task_data.live_card_id)

        if not live_card_info.metadata.get("ai_content"):
            live_card_ai_data = transform_entity_to_ai(live_card_info, live_card_items)
            print(f"------------------live_card_ai_data--------------------------------\n: {live_card_ai_data}")
        else:
            live_card_ai_data = live_card_info.metadata.get("ai_content")

        task = {
            "references" : task_data.task.get("references", []),
            "original_live_card":live_card_ai_data,
        }
        
        live_card_creation_task = LiveCardCreationTaskRequest(
            user_id=user.id,
            live_card_id=task_data.live_card_id,
            on_success_callback_url=task_data.on_success_callback_url,
            on_failure_callback_url=task_data.on_failure_callback_url,
            live_card_creation_task_config=agent_config.get("live_card_creation_task_config", {}),
            task=task,
        )
        logger.info(f"------------------live_card_creation_task--------------------------------\n: {live_card_creation_task}")

        ai_service_url = settings.AI_LIVE_CARD_CREATION_BOT_BASE_URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ai_service_url,
                data=dumps(live_card_creation_task.model_dump()),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return TaskResponse(
                    task_id="create_live_card_task",
                    status="success",
                    message="内容创建任务已成功创建并分配给AI服务",
                    created_at=datetime.now(UTC),
                )
            else:
                logging.error(f"AI服务创建任务失败: {response.status_code} - {response.text}")
                return TaskResponse(
                    task_id="create_live_card_task",
                    status="failed",
                    message=f"任务创建失败: {response.text}",
                    created_at=datetime.now(UTC),
                )

    @staticmethod
    async def create_live_card_task_callback(live_card: LiveCardCreationTaskCallback) -> TaskResponse:
        """
        创建直播卡片任务回调
        """
        logger.info(f"------------------创建直播卡片任务回调--------------------------------\n: {live_card}")
        live_card_dict, live_card_items_dict = transform_ai_to_entity(live_card.article)
        if not live_card_dict:
            return TaskResponse(
                task_id="create_live_card_task_callback",
                status="failed",
                message="直播卡片任务回调失败, article为空，未触发更新",
                created_at=datetime.now(UTC),
            )
        live_card_db = await live_card_crud.get(live_card.live_card_id)
        if not live_card_db:
            raise ValueError(f"直播卡片不存在 {live_card.live_card_id}")
        
        # 获取原始事件侧边栏数据
        original_related_info = live_card_db.related_info
        original_event_overview = original_related_info.get("event_overview", [])
        related_info_callback = live_card_dict.get("related_info", {})
        # 除了event_overview是把新的append到后面，其他都是覆盖
        related_info = {
            "background_context": related_info_callback.get("background_context", ""),
            "event_overview": original_event_overview + related_info_callback.get("event_overview", []),
            "key_stakeholders": related_info_callback.get("key_stakeholders", []),
            "impact_of_event": related_info_callback.get("impact_of_event", []),
        }
        metadata_updated = metadata_increment(live_card_db.metadata.get("ai_content"), live_card.article.get("live_card", {}))
        original_metadata = live_card_db.metadata
        original_metadata["ai_content"] = metadata_updated
        if live_card_dict:
            live_card_update = LiveCardUpdate(
                related_info=related_info,
                metadata=original_metadata
            )
            await live_card_crud.update(live_card.live_card_id, live_card_update)
        for live_card_items in live_card_items_dict:
            live_card_item = LiveCardItemCreate(
                live_card_id=live_card.live_card_id,
                name=live_card_items.get("name", ""),
                topic=live_card_items.get("topic", ""),
                description=live_card_items.get("description", ""),
                image_urls=live_card_items.get("image_urls", []),
                reference_urls=live_card_items.get("reference_urls", []),
                date_time=live_card_items.get("date_time", datetime.now()),
            )
            await LiveCardService.create_live_card_item(live_card_item)
        # 获取更新后的live_card信息
        live_card_info = await live_card_crud.get(live_card.live_card_id)
        update_increment = get_update_increment(live_card.article.get("live_card", {}))
        # 获取ai生成提醒词，调用API获取欢迎消息
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                data = {
                    "bot_name": live_card_info.agent_name,
                    "focused_category": live_card_info.categories[0] if live_card_info.categories else "Information Tracking",
                    "live_card_topic": live_card_info.topic_title,
                    "live_card_updates": update_increment,
                    "custom_style_instruction": None
                }
                logger.info(f"------------------生成更新消息模版--------------------------------\n: {data}")
                response = await client.post(
                    f"{settings.AI_SERVICE_BASE_URL}/info_bot/live_card_post/generate_update_notification",
                    headers={"Content-Type": "application/json"},
                    json = data
                )
                
                if response.status_code == 200:
                    update_message = response.json().get("update_notification", "Hi, new updates are available for you.")
                else:
                    logger.error(f"获取更新消息模板失败: {response.status_code} - {response.text}")
                    update_message = "Hi, new updates are available for you."
        except Exception as e:
            update_message = "Hi, new updates are available for you."
            logger.error(f"获取更新消息模板失败: {str(e)}")
        # 发送通知
        # TODO 需要埋点
        logger.info(f"------------------发送通知--------------------------------\n: {update_message}")
        for agent_tap_me in agent_tap_mes:
            chat = await chat_crud.get_chat_by_live_card_and_user(live_card_db.id, agent_tap_me.user_id)
            if chat:
                notification_message = MessageCreate( 
                                            chat_id=chat.id,
                                            sender_id=live_card_db.id,
                                            role="assistant",
                                            type="notification",
                                            text=update_message,
                                            contents=[]
                                        )   
                await message_crud.create_and_add_to_chat(notification_message, chat.id)
            user_fcm_token = await user_crud.get_user_fcm_token(agent_tap_me.user_id)
            if user_fcm_token:
                for device_id, (fcm_token, _) in user_fcm_token.items():
                    simple_notification = FcmNotificationMessage.create_simple_notification(
                        fcm_token,
                        f"@{agent_info.agent_name}",
                        live_card_info.topic_title,
                        live_card_info.topic_description,
                        f"/live_card/detail?live_card_id={live_card_db.id}",
                        live_card_info.topic_image_url if live_card_info.topic_image_url else "https://tapiavatar.s3.us-east-1.amazonaws.com/avatars/e7078115-59b6-4d29-9e10-e605980fae79/2025/06/6805d43c-2f9b-4d10-adaa-41536fcd87f5.jpg"
                    )
                    print(f"------------------发送通知--------------------------------\n: {simple_notification.model_dump()}")
                    await fcm_service.send_notification(
                        simple_notification
                    )
        
        return TaskResponse(
            task_id="create_live_card_task_callback",
            status="success",
            message="直播卡片任务回调已成功创建",
            created_at=datetime.now(UTC),
        )

    @staticmethod
    async def create_article_task(task_data: ArticleWritingTask) -> TaskResponse:
        """
        创建文章任务
        """
        try:
            agent = await agent_crud.get(task_data.bot_id)
            if not agent:
                raise ValueError(f"agent不存在 {task_data.bot_id}")
            # 创建本地任务记录
            task = TaskEntity(
                bot_id=agent.id,
                task_type=task_data.task_type,
                task_config=task_data.task_config,
                tags=task_data.tags,
                task_status="pending",
                trigger_at=task_data.trigger_at,
                executed_at=task_data.executed_at,
                finished_at=task_data.finished_at,
                failure_reason=task_data.failure_reason,
                on_success_callback_url=task_data.on_success_callback_url,
                on_failure_callback_url=task_data.on_failure_callback_url,
            )
            
            created_task = await task_crud.create(task)
        
            ai_service_url = settings.AI_INFO_BOT_BASE_URL
            article_writing_task_config = ArticleWritingTaskConfig(
                topic=task_data.task_config.get("topic", ""),
                description=task_data.task_config.get("description", ""),
                references=task_data.task_config.get("references", []),
                include_media_types=["image"],
            )
            article_writing_task = ArticleWritingRequest(
                task_type="article_writing",
                task_id=created_task.id,
                created_at=created_task.created_at,
                task_config=article_writing_task_config.model_dump(),
                task_status="pending",
                tags=task_data.tags,
                bot_id=agent.id,
                on_success_callback_url=task_data.on_success_callback_url,
                on_failure_callback_url=task_data.on_failure_callback_url,
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    ai_service_url,
                    data=dumps(article_writing_task.model_dump()),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    # AI端创建成功，更新本地任务状态
                    task.task_status = "processing"
                    await task.save()
                    
                    return TaskResponse(
                        task_id=str(task.id),
                        status=task.task_status,
                        message="文章任务已成功创建并分配给AI服务",
                        created_at=task.created_at
                    )
                else:
                    # AI端创建失败，更新本地任务状态
                    task.task_status = "failed"
                    task.failure_reason = f"AI服务创建任务失败: {response.text}"
                    await task.save()
                    
                    logging.error(f"AI服务创建任务失败: {response.status_code} - {response.text}")
                    return TaskResponse(
                        task_id=str(task.id),
                        status=task.task_status,
                        message=f"任务创建失败: {response.text}",
                        created_at=task.created_at
                    )
        except HTTPException as e:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": f"创建任务失败: {str(e)}"
                }
            )
        except Exception as e:
            # 发生异常，更新本地任务状态
            task.task_status = "failed"
            task.failure_reason = f"调用AI服务时发生错误: {str(e)}"
            await task.save()
            
            logging.exception("调用AI服务创建任务时发生异常")
            return TaskResponse(
                task_id=str(task.id),
                status=task.task_status,
                message=f"任务创建失败: {str(e)}",
                created_at=task.created_at
            )
        
    @staticmethod
    async def create_content_task_callback(bot_id: str, task_id: str, failure_reason: Optional[str] = None, article: Optional[ContentCreationTaskCallback] = None) -> TaskResponse:
        """
        创建文章任务回调
        """
        # 创建帖子
        if article:
            agent = await agent_crud.get(bot_id)
            if not agent:
                raise ValueError(f"agent不存在 {bot_id}")
            post = PostCreate(
                agent_id=agent.id,
                media_urls={},
                share_link="",
                content_data={"title": article.title, "post_content": article.raw_markdown_content, "summary": article.raw_summary},
                tags=article.tags,
                card_type="article",
                date_time=datetime.now(UTC),
                published=True,
                visibility="public",
                status="published",
                metadata={},
            )        
            # 创建帖子
            post = await PostService.create_post(post)
            logger.info(f"------------------创建帖子--------------------------------\n: {post}")
            if not post:
                raise ValueError(f"创建帖子失败, 任务id: {task_id}")
            # 获取追踪记录
            agent_tap_mes = await TapMeService.get_tap_me_by_agent_id(agent.id)
            # 发送通知
            # 需要埋点
            for agent_tap_me in agent_tap_mes:
                chat = await chat_crud.get_chat_by_agent_and_user(agent_tap_me.agent_id, agent_tap_me.user_id)
                if chat:
                    notification_message = MessageCreate( 
                                                chat_id=chat.id,
                                                sender_id=agent_tap_me.agent_id,
                                                role="assistant",
                                                type="notification",
                                                text=post.id,
                                                contents=[]
                                            )   
                    await message_crud.create_and_add_to_chat(notification_message, chat.id)
                user_fcm_token = await user_crud.get_user_fcm_token(agent_tap_me.user_id)
                if user_fcm_token:
                    for device_id, (fcm_token, _) in user_fcm_token.items():
                        simple_notification = FcmNotificationMessage.create_simple_notification(
                            fcm_token,
                            f"@{agent.agent_name}",
                            post.content_data.get("title", ""),
                            post.content_data.get("summary", ""),
                            f"/post/detail?postId={post.id}",
                            post.media_urls[0] if post.media_urls else "https://tapiavatar.s3.us-east-1.amazonaws.com/avatars/e7078115-59b6-4d29-9e10-e605980fae79/2025/06/6805d43c-2f9b-4d10-adaa-41536fcd87f5.jpg"
                        )
                        print(f"------------------发送通知--------------------------------\n: {simple_notification.model_dump()}")
                        await fcm_service.send_notification(
                           simple_notification
                        )
               
                await push_crud.create_push(PushCreate(
                    user_id=agent_tap_me.user_id,
                    agent_id=agent_tap_me.agent_id,
                    post_id=post.id,
                    content=f"({agent.agent_name}) taped you, he posted a new article: {post.content_data.get('title', '')}"
            ))
                
            return TaskResponse(
                task_id=task_id,
                status="success",
                message="文章任务已成功创建并更新ai task为成功",
                updated_at=datetime.now(UTC),
            )
        else:
            updated_task = TaskUpdate(
                task_status="failed",
                failure_reason=failure_reason,
            )
            await task_crud.update(task_id, updated_task)
            return TaskResponse(
                task_id=task_id,
                status="failed",
                message=failure_reason,
                updated_at=datetime.now(UTC),
            )

    @staticmethod
    async def create_article_task_callback(bot_id: str, task_id: str, failure_reason: Optional[str] = None, article: Optional[ArticleWritingTaskCallback] = None) -> TaskResponse:
        """
        创建文章任务回调
        """
        # 创建帖子
        if article:
            agent = await agent_crud.get(article.bot_id)
            if not agent:
                raise ValueError(f"agent不存在 {article.bot_id}")
            post = PostCreate(
                agent_id=agent.id,
                media_urls=article.medias,
                share_link="",
                content_data={"title": article.title, "post_content": article.content, "summary": article.summary, "sources": article.references if article.references else [],},
                card_type="article",
                date_time=datetime.now(UTC),
                published=True,
                visibility="public",
                status="published",
                metadata={},
            )        
            # 创建帖子
            post = await PostService.create_post(post)
            if not post:
                raise ValueError(f"创建帖子失败, 任务id: {task_id}")
            # 获取追踪记录
            agent_tap_mes = await TapMeService.get_tap_me_by_agent_id(agent.id)
            # 发送通知
            # 需要埋点
            for agent_tap_me in agent_tap_mes:
                chat = await chat_crud.get_chat_by_agent_and_user(agent_tap_me.agent_id, agent_tap_me.user_id)
                if chat:
                    notification_message = MessageCreate( 
                                                chat_id=chat.id,
                                                sender_id=agent_tap_me.agent_id,
                                                role="assistant",
                                                type="notification",
                                                text=post.id,
                                                contents=[]
                                            )   
                    await message_crud.create_and_add_to_chat(notification_message, chat.id)
                user_fcm_token = await user_crud.get_user_fcm_token(agent_tap_me.user_id)
                if user_fcm_token:
                    for device_id, (fcm_token, _) in user_fcm_token.items():
                        simple_notification = FcmNotificationMessage.create_simple_notification(
                            fcm_token,
                            f"@{agent.agent_name}",
                            post.content_data.get("title", ""),
                            post.content_data.get("summary", ""),
                            f"/post/detail?postId={post.id}",
                            post.media_urls[0] if post.media_urls else "https://tapiavatar.s3.us-east-1.amazonaws.com/avatars/e7078115-59b6-4d29-9e10-e605980fae79/2025/06/6805d43c-2f9b-4d10-adaa-41536fcd87f5.jpg"
                        )
                        print(f"------------------发送通知--------------------------------\n: {simple_notification.model_dump()}")
                        await fcm_service.send_notification(
                           simple_notification
                        )
                await push_crud.create_push(PushCreate(
                    user_id=agent_tap_me.user_id,
                    agent_id=agent_tap_me.agent_id,
                    post_id=post.id,
                    content=f"({agent.agent_name}) taped you, he posted a new article: {post.content_data.get('title', '')}"
            ))
                

            # 更新任务
            if article.updated_task_body:
                article.updated_task_body["result_id"] = post.id
                updated_task = TaskUpdate(**article.updated_task_body)
                await task_crud.update(task_id, updated_task)

            return TaskResponse(
                task_id=task_id,
                status="success",
                message="文章任务已成功创建并更新ai task为成功",
                updated_at=datetime.now(UTC),
            )
        else:
            updated_task = TaskUpdate(
                task_status="failed",
                failure_reason=failure_reason,
            )
            await task_crud.update(task_id, updated_task)
            return TaskResponse(
                task_id=task_id,
                status="failed",
                message=failure_reason,
                updated_at=datetime.now(UTC),
            )


    @staticmethod
    async def get_task(task_id: str) -> TaskResponse:
        """
        获取任务详情
        """
        try:
            task = await task_crud.get(task_id)
            if not task:
                return TaskResponse(
                    task_id=task_id,
                    status="error",
                    message="任务不存在",
                )
            
            return TaskResponse(
                task_id=str(task.id),
                status=task.task_status,
                message="获取任务成功",
                created_at=task.created_at,
            )
        except HTTPException as e:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": f"获取任务失败: {str(e)}"
                }
            )
    
    @staticmethod
    async def get_tasks(
        skip: int = 0, 
        limit: int = 10,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[TaskResponse]:
        """
        获取任务列表，使用批量查询模式避免N+1查询问题
        """
        try:
            # 构建查询条件
            query_dict = {}
            if status:
                query_dict["task_status"] = status
            if task_type:
                query_dict["task_type"] = task_type
                
            # 批量查询任务
            tasks = await task_crud.find(query_dict)
            
            # 限制数量并分页
            paginated_tasks = tasks[skip:skip+limit] if tasks else []
            
            # 构建响应
            return [
                TaskResponse(
                    task_id=str(task.id),
                    status=task.task_status,
                    message="",
                    created_at=task.created_at,
                )
                for task in paginated_tasks
            ]
        except HTTPException as e:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": f"获取任务列表失败: {str(e)}"
                }
            )

    @staticmethod
    async def auto_post(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动发帖
        """
        print(f"------------------自动发帖--------------------------------\n: {data}")
        try:
            topic = data.get("topic", "")
            data = data.get("data", "")
            result = await bot_manager.send_message(topic, data)
            return result
        except Exception as e:
            return {
                "status": "error", 
                "message": f"自动发帖失败: {str(e)}"
            }
        