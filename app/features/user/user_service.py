from typing import List, Optional, Dict, Any, Tuple
from app.schemas.user_schema import UserCreate, UserUpdate, UserBase, UserLogin, UserProfileResponse, UserResponse
from app.entities.user_entity import User
from app.crud import user_crud, follow_crud, system_config_crud
from fastapi import HTTPException, UploadFile
from datetime import datetime, UTC
from app.utils.logger_service import logger
from app.infrastructure.redis.user_cache import user_cache
from app.infrastructure.auth.auth0 import Auth0
from app.infrastructure.storage.s3_service import S3Service

class UserService:

    def __init__(self):
        self.user_crud = user_crud
        self.follow_crud = follow_crud
        self.system_config_crud = system_config_crud  
        self.user_cache = user_cache
        self.auth0 = Auth0()
        self.s3_service = S3Service()

    async def create_user(self, user_data: UserBase) -> User:
        """
        先在Auth0创建用户，成功后再写入本地数据库
        """
        auth0_user = None
        try:
            # 1. 在Auth0创建用户
            auth0_user = await self.auth0.register_auth0_user(user_data)
            # 2. 准备本地用户数据，包含Auth0 ID
            local_user_data = UserCreate(**user_data.model_dump(exclude={"id"}),auth0_id=auth0_user["user_id"])
            
            # 保存Auth0 user_id到metadata
            local_user_data.metadata = auth0_user
            user = await self.user_crud.create(local_user_data)

            return user
        
        except HTTPException as e:
            raise
        except Exception as e:
            # 4. 如果本地数据库操作失败，但Auth0已创建成功，则回滚Auth0用户
            if auth0_user:
                try:
                    await self.auth0.delete_auth0_user(auth0_user["user_id"])               
                except Exception as delete_error:
                    # 记录删除失败，但不影响原始异常
                    logger.warning(f"回滚Auth0用户创建失败: {delete_error}")
            # 重新抛出异常
            if isinstance(e, HTTPException):
                raise
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": 400,
                        "message": f"创建用户失败: {str(e)}"
                    }
                )

    async def sync_user(self,token: str) -> User:
        """同步用户"""
        user_info = await self.auth0.get_auth0_user_info(token.credentials)
        if not user_info or not user_info["sub"]:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": 401,
                    "message": "未查询到user或user[sub]为空"
                }
            )
        local_user_data = await self.user_crud.get_by_auth0_id(user_info["sub"])
        if local_user_data:
            local_user_data.auth0_id = user_info["sub"]
            local_user_data.metadata = user_info
            update_data = UserUpdate(**local_user_data.model_dump())
            user = await self.user_crud.update(local_user_data.id, update_data)
        else:
            local_user_data = UserCreate(**user_info, auth0_id=user_info["sub"])
            local_user_data.metadata = user_info
            user = await self.user_crud.create(local_user_data)
        if user:
            await self.user_cache.cache_user_by_token(token.credentials, user)
        return user

    async def get_current_user(self,token: str) -> User:
        """
        通过token获取当前用户信息
        """
        cached_user = await self.user_cache.get_user_by_token(token)
        if cached_user:
            local_user=cached_user
        else:
            local_user = await self.auth0.get_user_info(access_token=token)
            if not local_user:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": 401,
                        "message": "用户不存在"
                    }
                )
        return local_user

    async def update_with_rollback(
        self,
        current_user: User, 
        name: Optional[str] = None,
        bio: Optional[str] = None,
        status: Optional[str] = None,
        password: Optional[str] = None,
        picture: Optional[UploadFile] = None
    ) -> Optional[User]:
        """
        更新用户信息（包括头像上传）并同步到Auth0
        如果Auth0同步失败，回滚本地更新
        """
        current_user_id = current_user.id
        
        # 准备更新数据
        update_data = UserUpdate()
        
        # 构建本地更新数据
        if name is not None:
            update_data.name = name
        if bio is not None:
            update_data.bio = bio
        if status is not None:
            update_data.status = status
        if password is not None:
            update_data.password = password
        
        # 获取当前用户信息（备份用于回滚）
        original_user = await self.user_crud.get(current_user_id)
        if not original_user:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": 404,
                    "message": "用户不存在"
                }
            )
        
        old_picture_url = None
        new_picture_url = None
        
        try:
            # 处理图片上传
            if picture and picture.filename:
                logger.info(f"开始上传用户头像: {picture.filename}")
                
                # 保存旧头像URL用于可能的回滚
                old_picture_url = original_user.picture
                
                # 上传新头像
                new_picture_url = await self.s3_service.upload_image(
                    file=picture,
                    folder="avatars",
                    user_id=current_user_id
                )
                
                update_data.picture = new_picture_url
                logger.info(f"头像上传成功: {new_picture_url}")
        
            # 更新本地数据库
            updated_user = await self.user_crud.update(current_user_id, update_data)
            # 删除旧头像（在确认所有更新成功后）
            if (old_picture_url and new_picture_url and
                old_picture_url.startswith("https://") and
                self.s3_service.bucket_name in old_picture_url):
                
                logger.info(f"删除旧头像: {old_picture_url}")
                await self.s3_service.delete_image(old_picture_url)
            
            # 清除用户缓存
            await self.user_cache.invalidate_user(current_user_id)
            
            return updated_user
            
        except Exception as e:
            # 发生错误时回滚
            logger.error(f"用户更新失败，开始回滚: {str(e)}")
            
            # 删除新上传的图片
            if new_picture_url:
                try:
                    await self.s3_service.delete_image(new_picture_url)
                    logger.info(f"回滚：删除新上传的图片: {new_picture_url}")
                except Exception as rollback_e:
                    logger.error(f"回滚删除图片失败: {str(rollback_e)}")
            
            # 重新抛出原始异常
            if isinstance(e, HTTPException):
                raise
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": 500,
                        "message": f"更新用户信息失败: {str(e)}"
                    }
                )
    

    async def delete_user_by_id(self,user_id: str, current_user: User) -> bool:
        """删除用户"""
        try:
            if current_user.id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="无权限删除用户"
                )
            # 1. 获取用户信息
            user = await self.user_crud.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="用户不存在"
                )
            
            try:
                await self.auth0.delete_auth0_user(user.auth0_id)
            except Exception as e:
                # 记录Auth0删除失败的错误，但继续执行本地删除
                logger.error(f"删除Auth0用户失败: {str(e)}")
                
            # 3. 删除本地用户数据
            success = await self.user_crud.delete(user_id)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="删除本地用户数据失败"
                )
            
            # 4. 清除用户相关的缓存
            try:
                from app.infrastructure.redis.user_cache import user_cache
                await self.user_cache.invalidate_user(user_id)
            except Exception as e:
                # 记录缓存清理失败的错误
                logger.error(f"清除用户缓存失败: {str(e)}")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"删除用户失败: {str(e)}"
            )
        
    async def login_user(self,login_data: UserLogin) -> Dict[str, Any]:
        """
        使用用户登录数据登录用户，并获取用户信息
        
        Args:
            login_data: 用户登录数据，包含email和password
            
        Returns:
            Dict: 包含令牌信息和用户信息的字典
        """
        # 1. 获取令牌信息
        token_info = await self.auth0.login_user(login_data)
        
        # 2. 使用邮箱查找用户
        user = await self.user_crud.get_by_email(login_data.email)
        
        # 3. 如果找不到用户，则使用token获取用户信息并同步
        if not user:
            # 使用token获取用户信息
            user_info = await self.auth0.get_user_info(token_info["access_token"])
            if not user_info:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": 401,
                        "message": "获取用户信息失败"
                    }
                )
            
            # 检查是否有auth0_id
            auth0_id = user_info.get("sub")
            if not auth0_id:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": 401,
                        "message": "获取Auth0用户ID失败"
                    }
                )
            
            # 通过auth0_id查找用户
            user = await self.user_crud.get_by_auth0_id(auth0_id)
            
            # 如果仍然找不到，创建新用户
            if not user:
                # 创建新用户
                user_data = UserCreate(**user_info, auth0_id=auth0_id)
                user_data.metadata = user_info
                user = await self.user_crud.create(user_data)
        
        # 4. 返回令牌信息和用户信息
        return {
            "access_token": token_info["access_token"],
            "id_token": token_info.get("id_token"),
            "refresh_token": token_info.get("refresh_token"),
            "expires_at": token_info.get("expires_at"),
            "user": user
        }

    async def add_fcm_token(self,current_user: User, device_id: str, fcm_token: str) -> User:
        """
        链接fcm token
        """
        user_fcm_token = current_user.fcm_token
        if user_fcm_token and device_id in user_fcm_token:
            user_fcm_token[device_id] = (fcm_token, datetime.now(UTC).isoformat())
        else:
            user_fcm_token = {device_id: (fcm_token, datetime.now(UTC).isoformat()), **user_fcm_token}
        update_data = UserUpdate(fcm_token=user_fcm_token)
        user = await self.user_crud.update(current_user.id, update_data)
        # 清除用户缓存
        await self.user_cache.invalidate_user(current_user.id)
        return user
    
    async def get_creation_user(self) -> List[UserResponse]:
        """获取创建用户列表"""
        user_ids_config = await self.system_config_crud.get_by_key("agent_creation_user_ids")
        user_ids = user_ids_config.value
        if not user_ids:
            raise ValueError("creation flow用户列表为空")
        users = await self.user_crud.get_users_by_ids(user_ids)
        user_responses = []
        for user in users:
            user_response = UserResponse.model_validate(user.model_dump())
            user_responses.append(user_response)
        return user_responses
    
    async def get_user_profile(self,current_user: User) -> UserProfileResponse:
        """获取用户信息"""
        user = await self.user_crud.get(current_user.id)
        return UserProfileResponse.model_validate(user.model_dump())
    