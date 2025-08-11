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

    async def get_by_wechat_openid(self, openid: str) -> Optional[User]:
        """根据微信openid查询用户"""
        return await User.find_one({"wechat_openid": openid, "is_deleted": False})

    async def get_by_wechat_unionid(self, unionid: str) -> Optional[User]:
        """根据微信unionid查询用户"""
        return await User.find_one({"wechat_unionid": unionid, "is_deleted": False})

    async def get_or_create_wechat_user(
        self,
        openid: str,
        unionid: Optional[str] = None,
        user_info: Optional[Dict] = None
    ) -> Tuple[User, bool]:
        """
        获取或创建微信用户
        
        Args:
            openid: 微信openid
            unionid: 微信unionid（可选）
            user_info: 微信用户信息（可选）
            
        Returns:
            Tuple[User, bool]: (用户对象, 是否新创建)
        """
        # 1. 先通过openid查找
        user = await self.get_by_wechat_openid(openid)
        if user:
            return user, False
            
        # 2. 如果有unionid，尝试通过unionid查找
        if unionid:
            user = await self.get_by_wechat_unionid(unionid)
            if user:
                # 更新openid
                user.wechat_openid = openid
                await user.save()
                return user, False
        
        # 3. 创建新用户
        user_data = {
            "wechat_openid": openid,
            "wechat_unionid": unionid,
            "is_deleted": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # 如果有用户信息，添加到用户数据中
        if user_info:
            user_data.update({
                "nickname": user_info.get("nickName"),
                "avatar_url": user_info.get("avatarUrl"),
                "gender": user_info.get("gender"),
                "country": user_info.get("country"),
                "province": user_info.get("province"),
                "city": user_info.get("city"),
                "language": user_info.get("language"),
                "metadata": {
                    "wechat_user_info": user_info,
                    "register_time": datetime.now().isoformat()
                }
            })
        
        user_create = UserCreate(**user_data)
        user = await self.create(user_create)
        return user, True

    async def update_wechat_user_info(
        self,
        user_id: str,
        user_info: Dict[str, Any]
    ) -> Optional[User]:
        """
        更新微信用户信息
        
        Args:
            user_id: 用户ID
            user_info: 微信用户信息
            
        Returns:
            Optional[User]: 更新后的用户对象
        """
        update_data = UserUpdate(
            nickname=user_info.get("nickName"),
            avatar_url=user_info.get("avatarUrl"),
            gender=user_info.get("gender"),
            country=user_info.get("country"),
            province=user_info.get("province"),
            city=user_info.get("city"),
            language=user_info.get("language"),
            metadata={
                "wechat_user_info": user_info,
                "update_time": datetime.now().isoformat()
            }
        )
        return await self.update(user_id, update_data)

    async def get_user_fcm_token(self, user_id: str) -> Optional[Dict[str, Tuple[str, str]]]:
        """根据用户ID查询用户FCM token"""
        user = await User.find_one({"_id": user_id, "is_deleted": False})
        if user:
            return user.fcm_token
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

    async def search_users(
        self,
        keyword: Optional[str] = None,
        filters: Optional[UserFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[User], int]:
        """
        搜索用户
        
        Args:
            keyword: 搜索关键词
            filters: 过滤条件
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            Tuple[List[User], int]: (用户列表, 总数)
        """
        base_query = {"is_deleted": False}
        
        if keyword:
            base_query.update({
                "$or": [
                    {"nickname": {"$regex": keyword, "$options": "i"}},
                    {"name": {"$regex": keyword, "$options": "i"}},
                ]
            })
            
        if filters:
            if filters.gender is not None:
                base_query["gender"] = filters.gender
            if filters.country:
                base_query["country"] = filters.country
            if filters.province:
                base_query["province"] = filters.province
            if filters.city:
                base_query["city"] = filters.city
        
        total = await User.find(base_query).count()
        users = await User.find(base_query).skip(skip).limit(limit).to_list()
        
        return users, total

# 创建单例实例
user_crud = UserCRUD()