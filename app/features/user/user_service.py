from typing import List, Optional, Dict, Any, Tuple
from app.schemas.user_schema import UserFilter, PaginationParams, UserCreate, UserUpdate
from app.entities.user_entity import User
from app.crud.user_crud import user_crud

class UserService:
    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """创建用户"""
        return await user_crud.create(user_data)

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return await user_crud.get(user_id)

    @staticmethod
    async def update_user_by_id(user_id: str, update_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        return await user_crud.update(user_id, update_data)

    @staticmethod
    async def delete_user_by_id(user_id: str) -> bool:
        """删除用户"""
        return await user_crud.delete(user_id)

    @staticmethod
    async def get_users_with_filter(
        filter_params: UserFilter,
        pagination: PaginationParams
    ) -> Tuple[List[User], int]:
        """带分页和过滤的用户列表查询"""
        return await user_crud.get_users_with_filter(filter_params, pagination)