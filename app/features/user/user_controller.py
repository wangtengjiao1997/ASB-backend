from fastapi import HTTPException, status, Depends
from app.features.user.user_service import UserService
from app.schemas.user_schema import (
    UserResponse, UserLogin, UserProfileResponse
)
import math
from typing import Dict, Any, Optional, List
from fastapi import Form, File, UploadFile
from app.entities.user_entity import User

class UserController:
    def __init__(self):
        self.user_service = UserService()

    async def sync_user(self,token: str) -> UserResponse:
        """处理同步用户请求"""
        user = await self.user_service.sync_user(token)
        return UserResponse.model_validate(user)

    async def update(
        self,
        current_user: User, 
        name: Optional[str] = Form(None), 
        bio: Optional[str] = Form(None), 
        status: Optional[str] = Form(None), 
        password: Optional[str] = Form(None), 
        picture: Optional[UploadFile] = File(None)
    ) -> UserResponse:
        """处理更新用户请求"""

        user = await self.user_service.update_with_rollback(
            current_user, 
            name,
            bio,
            status,
            password,
            picture
        )
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        return UserResponse.model_validate(user)
    
    async def login_user(self,login_data: UserLogin) -> Dict[str, Any]:
        """
        处理用户登录请求
        
        Args:
            login_data: 用户登录数据，包含email和password
            
        Returns:
            Dict: 包含access_token和用户信息的字典
        """
        result = await self.user_service.login_user(login_data)
        
        # 如果有用户信息，将其转换为UserResponse
        if result["user"]:
            result["user"] = UserResponse.model_validate(result["user"])
            
        return result
    
    async def add_fcm_token(self,current_user: User, device_id: str, fcm_token: str) -> UserResponse:
        """
        链接fcm token
        """
        user_info = await self.user_service.add_fcm_token(current_user, device_id, fcm_token)
        if user_info:
            return UserResponse.model_validate(user_info)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="添加fcm token失败"
            )
        
    async def get_user_profile(self,current_user: User) -> UserProfileResponse:
        """处理获取用户信息请求"""
        user = await self.user_service.get_user_profile(current_user)
        return user