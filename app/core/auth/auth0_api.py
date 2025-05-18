import os
import json
import time
import requests
from typing import Dict, Optional, Any, List
from fastapi import HTTPException, status
from app.core.config import settings

class Auth0API:
    """
    Auth0 API封装类，提供用户创建、登录和获取信息的功能
    """
    
    def __init__(self):
        """初始化Auth0 API客户端"""
        self.domain = settings.AUTH0_DOMAIN
        self.audience = settings.AUTH0_API_AUDIENCE
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.connection = settings.AUTH0_CONNECTION
        self.token_endpoint = f"https://{self.domain}/oauth/token"
        self.users_endpoint = f"https://{self.domain}/api/v2/users"
        
        # Management API 令牌相关
        self.management_client_id = settings.AUTH0_MANAGEMENT_CLIENT_ID
        self.management_client_secret = settings.AUTH0_MANAGEMENT_CLIENT_SECRET
        self.management_audience = f"https://{self.domain}/api/v2/"
        self._mgmt_token = None
        self._mgmt_token_expires_at = 0
    
    async def _get_management_token(self) -> str:
        """
        获取Auth0 Management API的访问令牌
        """
        current_time = int(time.time())
        
        # 检查现有令牌是否有效
        if self._mgmt_token and current_time < self._mgmt_token_expires_at - 60:
            return self._mgmt_token
        
        # 获取新的访问令牌
        payload = {
            "client_id": self.management_client_id,
            "client_secret": self.management_client_secret,
            "audience": self.management_audience,
            "grant_type": "client_credentials"
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.token_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self._mgmt_token = data["access_token"]
            self._mgmt_token_expires_at = current_time + data["expires_in"]
            
            return self._mgmt_token
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取Auth0管理令牌失败: {str(e)}"
            )
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在Auth0中创建用户

        Args:
            user_data: 包含用户信息的字典，必须包含email和password字段

        Returns:
            创建成功的用户信息
        """
        if "email" not in user_data or "password" not in user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建用户需要提供email和password"
            )
        
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备用户数据
        auth0_user = {
            "email": user_data["email"],
            "password": user_data["password"],
            "connection": self.connection,
            "email_verified": False
        }
        
        # 添加可选字段
        if "username" in user_data:
            auth0_user["username"] = user_data["username"]
        
        # 添加用户元数据
        user_metadata = {}
        for field in ["phone", "avatar", "bio"]:
            if field in user_data:
                user_metadata[field] = user_data[field]
        
        if user_metadata:
            auth0_user["user_metadata"] = user_metadata
        
        try:
            response = requests.post(self.users_endpoint, headers=headers, json=auth0_user)
            
            if response.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="用户已存在"
                )
            
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            error_msg = f"创建Auth0用户失败: {str(e)}"
            if response and hasattr(response, 'text'):
                try:
                    error_detail = response.json()
                    if "message" in error_detail:
                        error_msg = f"创建Auth0用户失败: {error_detail['message']}"
                except:
                    pass
            
            raise HTTPException(
                status_code=response.status_code if response else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建Auth0用户出错: {str(e)}"
            )
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        用户登录并获取访问令牌

        Args:
            email: 用户邮箱
            password: 用户密码

        Returns:
            包含访问令牌和ID令牌的响应
        """
        payload = {
            "grant_type": "password",
            "username": email,
            "password": password,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience,
            "scope": "openid profile email"
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.token_endpoint, json=payload, headers=headers)
            
            if response.status_code == 403 or response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            response.raise_for_status()
            return response.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登录失败: {str(e)}"
            )
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        通过用户ID获取用户信息

        Args:
            user_id: Auth0用户ID

        Returns:
            用户信息
        """
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{self.users_endpoint}/{user_id}", headers=headers)
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            response.raise_for_status()
            return response.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户信息失败: {str(e)}"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        通过邮箱获取用户信息

        Args:
            email: 用户邮箱

        Returns:
            用户信息，如果用户不存在则返回None
        """
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"https://{self.domain}/api/v2/users-by-email", 
                headers=headers, 
                params={"email": email}
            )
            
            response.raise_for_status()
            users = response.json()
            
            if not users or len(users) == 0:
                return None
            
            return users[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"通过邮箱获取用户信息失败: {str(e)}"
            )
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户信息

        Args:
            user_id: Auth0用户ID
            update_data: 要更新的用户数据

        Returns:
            更新后的用户信息
        """
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备更新数据
        auth0_update = {}
        
        # 处理基本字段
        for field in ["email", "username", "password", "email_verified"]:
            if field in update_data:
                auth0_update[field] = update_data[field]
        
        # 处理用户元数据
        user_metadata = {}
        for field in ["phone", "avatar", "bio"]:
            if field in update_data:
                user_metadata[field] = update_data[field]
        
        if user_metadata:
            auth0_update["user_metadata"] = user_metadata
        
        try:
            response = requests.patch(
                f"{self.users_endpoint}/{user_id}", 
                headers=headers, 
                json=auth0_update
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            response.raise_for_status()
            return response.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新用户信息失败: {str(e)}"
            )
    
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id: Auth0用户ID

        Returns:
            是否删除成功
        """
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(f"{self.users_endpoint}/{user_id}", headers=headers)
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            response.raise_for_status()
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除用户失败: {str(e)}"
            )
    
    async def change_password(self, email: str) -> bool:
        """
        发起密码重置请求

        Args:
            email: 用户邮箱

        Returns:
            是否成功发送重置邮件
        """
        payload = {
            "client_id": self.client_id,
            "email": email,
            "connection": self.connection
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                f"https://{self.domain}/dbconnections/change_password", 
                json=payload, 
                headers=headers
            )
            
            response.raise_for_status()
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"发送密码重置邮件失败: {str(e)}"
            )
    
    async def get_users(self, page: int = 0, per_page: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户列表

        Args:
            page: 页码（从0开始）
            per_page: 每页用户数量

        Returns:
            用户列表
        """
        token = await self._get_management_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "page": page,
            "per_page": per_page,
            "include_totals": "true"
        }
        
        try:
            response = requests.get(self.users_endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户列表失败: {str(e)}"
            )

# 创建单例实例
auth0_api = Auth0API() 