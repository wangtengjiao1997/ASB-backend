from typing import List, Optional, Dict, Any, Tuple
from app.entities.user_entity import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserFilter, PaginationParams
from app.crud.base_crud import BaseCRUD

class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate, UserFilter]):
    def __init__(self):
        super().__init__(User)
    
    async def _build_filter_query(self, filter_params: UserFilter) -> Dict:
        """构建用户过滤查询条件"""
        query = {}
        
        if filter_params.username:
            query["username"] = {"$regex": filter_params.username, "$options": "i"}
            
        if filter_params.email:
            query["email"] = {"$regex": filter_params.email, "$options": "i"}
            
        if filter_params.phone:
            query["phone"] = {"$regex": filter_params.phone, "$options": "i"}
            
        if filter_params.status:
            query["status"] = filter_params.status
            
        if filter_params.created_after:
            query["created_at"] = {"$gte": filter_params.created_after}
            
        if filter_params.created_before:
            if "created_at" in query:
                query["created_at"]["$lte"] = filter_params.created_before
            else:
                query["created_at"] = {"$lte": filter_params.created_before}
        
        if filter_params.updated_after:
            query["updated_at"] = {"$gte": filter_params.updated_after}
            
        if filter_params.updated_before:
            if "updated_at" in query:
                query["updated_at"]["$lte"] = filter_params.updated_before
            else:
                query["updated_at"] = {"$lte": filter_params.updated_before}
                
        return query
    
    async def get_users_with_filter(
        self,
        filter_params: UserFilter,
        pagination: PaginationParams
    ) -> Tuple[List[User], int]:
        """带分页和过滤的用户列表查询"""
        query = await self._build_filter_query(filter_params)
        
        # 构建排序
        sort_direction = -1 if pagination.sort_desc else 1
        sort_field = pagination.sort_by
        
        # 计算总数
        total = await User.find(query).count()
        
        # 计算偏移量
        skip = (pagination.page - 1) * pagination.page_size
        
        # 查询带分页的结果
        users = await User.find(query).sort(
            [(sort_field, sort_direction)]
        ).skip(skip).limit(pagination.page_size).to_list()
        
        return users, total

# 创建单例实例
user_crud = UserCRUD()