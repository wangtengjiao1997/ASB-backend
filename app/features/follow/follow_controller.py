from fastapi import HTTPException, status, Query, Depends
from app.features.follow.follow_service import follow_service
from app.schemas.follow_schema import (
    FollowCreate, FollowUpdate, FollowResponse, FollowFilter, 
    PaginationParams, PaginatedResponse, FollowClick,
    FollowIncrementalParams, FollowIncrementalResponse
)
import math
from app.infrastructure.auth.auth0 import Auth0
from app.features.user.user_service import UserService
from app.entities.user_entity import User
from typing import Dict
class FollowController:
    def __init__(self):
        self.service = follow_service

    async def follow_click(self, current_user: User, follow_click: FollowClick) -> Dict:
        """关注点击"""
        if follow_click.is_follow:
            data = await self.service.create_follow(current_user.id, follow_click.target_id, follow_click.target_type)
        else:
            data = await self.service.remove_follow(current_user.id, follow_click.target_id, follow_click.target_type)
        return data

    async def follow_list(
        self,
        current_user: User,
        incremental_params: FollowIncrementalParams
    ) -> FollowIncrementalResponse:
        """处理获取关注列表请求（带分页和过滤）"""
        follows_list, has_more, total = await self.service.follow_list(current_user, incremental_params)
        return FollowIncrementalResponse(
            items=follows_list,
            has_more=has_more,
            last_id=follows_list[-1].id if follows_list else None,
            last_timestamp=follows_list[-1].created_at if follows_list else None,
            total=total
        )

# 全局Controller实例
follow_controller = FollowController()