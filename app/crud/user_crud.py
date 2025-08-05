from typing import List, Optional, Dict, Any, Tuple
from app.entities.user_entity import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserFilter
from app.crud.base_crud import BaseCRUD
from datetime import datetime
class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)
    
    async def delete(self, id: str) -> bool:
        """软删除用户"""
        user = await self.get(id)
        if user:
            user.is_deleted = True
            user.deleted_at = datetime.now()
            user.name = f"deleted_{user.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            await user.save()
            return True
        else:
            return False

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查询用户"""
        return await User.find_one({"email": email, "is_deleted": False})

    async def get_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """根据auth0_id查询用户"""
        return await User.find_one({"auth0_id": auth0_id, "is_deleted": False})
    
    async def get_user_fcm_token(self, user_id: str) -> Optional[Dict[str, Tuple[str, str]]]:
        """根据用户ID查询用户"""
        user = await User.find_one({"_id": user_id, "is_deleted": False})
        if user:
            return user.fcm_token
        else:
            return None
        
    async def get_users_by_ids(self, user_ids: List[str]) -> List[User]:
        """
        根据用户ID列表批量查询用户信息
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            用户列表（过滤掉已删除的用户）
        """
        if not user_ids:
            return []
            
        query = {
            "_id": {"$in": user_ids},
            "is_deleted": False
        }
        
        users = await User.find(query).to_list()
        return users

# 创建单例实例
user_crud = UserCRUD()