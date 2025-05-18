from fastapi import HTTPException, status, Query, Depends
from app.features.user.user_service import UserService
from app.schemas.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserFilter, 
    PaginationParams, PaginatedResponse
)
import math

class UserController:
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserResponse:
        """处理创建用户请求"""
        try:
            user = await UserService.create_user(user_data)
            return UserResponse.model_validate(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建用户失败: {str(e)}"
            )

    @staticmethod
    async def get_user_by_id(user_id: str) -> UserResponse:
        """处理获取用户请求"""
        try:
            user = await UserService.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return UserResponse.model_validate(user)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户ID格式"
            )

    @staticmethod
    async def update_user_by_id(user_id: str, update_data: UserUpdate) -> UserResponse:
        """处理更新用户请求"""
        try:
            user = await UserService.update_user_by_id(user_id, update_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"更新失败: {str(e)}"
            )

    @staticmethod
    async def delete_user_by_id(user_id: str) -> dict:
        """处理删除用户请求"""
        try:
            success = await UserService.delete_user_by_id(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return {"success": True}
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户ID格式"
            )

    @staticmethod
    async def get_users_with_filter(
        filter_params: UserFilter = Depends(),
        pagination: PaginationParams = Depends()
    ) -> PaginatedResponse:
        """处理获取用户列表请求（带分页和过滤）"""
        users, total = await UserService.get_users_with_filter(filter_params, pagination)
        
        # 计算分页信息
        current_page = pagination.page
        total_pages = math.ceil(total / pagination.page_size)
        
        # 将用户列表转换为响应对象
        user_responses = [UserResponse.model_validate(user) for user in users]
        return PaginatedResponse(
            total=total,
            items=user_responses,
            page=current_page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )