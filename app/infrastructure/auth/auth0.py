from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
import jwt
import requests

from app.core.config import settings
from app.schemas.user_schema import UserCreate, UserLogin, AuthUserInfo
from app.entities.user_entity import User
from app.crud import user_crud
from app.utils.logger_service import logger
from app.infrastructure.redis.user_cache import user_cache

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403"""
        super().__init__(status_code=401, detail={"code": 4001, "message": "Token Unauthorized"})

class UnauthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401, 
            detail={"code": 4002, "message": "Requires authentication"}
        )

class Auth0:
    """
    Auth0 API封装类，提供用户创建、登录和获取信息的功能
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Auth0, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化Auth0 API客户端"""
        if self._initialized:
            return
        # 认证相关
        self.domain = settings.AUTH0_DOMAIN
        self.algorithms = settings.AUTH0_ALGORITHMS
        self.issuer = settings.AUTH0_ISSUER
        self.audience = settings.AUTH0_API_AUDIENCE

        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.app_client_id = settings.AUTH0_APP_CLIENT_ID
        self.app_client_secret = settings.AUTH0_APP_CLIENT_SECRET
        self.connection = settings.AUTH0_CONNECTION
        self.token_endpoint = f"https://{self.domain}/oauth/token"
        self.users_endpoint = f"https://{self.domain}/api/v2/users"
        
        # Management API 令牌相关
        self.management_client_id = settings.AUTH0_MANAGEMENT_CLIENT_ID
        self.management_client_secret = settings.AUTH0_MANAGEMENT_CLIENT_SECRET
        self.management_audience = f"https://{self.domain}/api/v2/"
        self._mgmt_token = None
        self._mgmt_token_expires_at = 0

        # 初始化JWKS客户端
        jwks_url = f'https://{self.domain}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)
        self._initialized = True
        logger.info(f"Auth0 客户端初始化完成，domain: {self.domain}")
    # 获取Auth0管理API令牌
    def get_management_token(self):
        """获取Auth0管理API令牌"""
        response = requests.post(
            f"https://{self.domain}/oauth/token",
            json={
                "client_id": self.management_client_id,
                "client_secret": self.management_client_secret,
                "audience": f"https://{self.domain}/api/v2/",
                "grant_type": "client_credentials"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="无法获取Auth0管理令牌"
            )
        
        return response.json().get("access_token")

    async def verify(self,
                    security_scopes: SecurityScopes,
                    token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
                    ):
        """验证JWT令牌"""
        if token is None:
            raise UnauthenticatedException
        
        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))
            
        try:
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.algorithms,
                audience=[self.audience, self.client_id],
                issuer=self.issuer,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))
    
        return payload
    
    async def get_user_info(self, access_token: str) -> Optional[User]:
        """使用access token从Auth0获取用户信息"""
        try:
            response = requests.get(
                f"https://{self.domain}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            local_user = await user_crud.get_by_auth0_id(data.get("sub"))
            await user_cache.cache_user_by_token(access_token, local_user)
            return local_user
        except requests.exceptions.RequestException as e:
            raise UnauthorizedException("Failed to retrieve user information")
        except Exception as e:
            raise Exception("Failed to retrieve user information")
    
    async def get_auth0_user_info(self, access_token: str) -> Dict[str, Any]:
        """使用access token从Auth0获取用户信息"""
        try:
            response = requests.get(
                f"https://{self.domain}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            response.raise_for_status()
            
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            
            print(f"Error fetching user info: {str(e)}")
            raise UnauthorizedException("Failed to retrieve user information")

    async def register_auth0_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        在Auth0创建用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            Dict: 创建的Auth0用户信息
            
        Raises:
            HTTPException: 当创建失败时抛出
        """
        try:
            # 获取管理API令牌
            token = self.get_management_token()
            
            # 在Auth0创建用户
            response = requests.post(
                f"https://{self.domain}/api/v2/users",
                json={
                    "email": user_data.email,
                    "password": user_data.password,
                    "connection": self.connection,
                    "name": user_data.name,
                    "email_verified": False
                },
                headers={"Authorization": f"Bearer {token}"}
            )
                
            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Auth0用户创建失败: {response.text}"
                )
                
            return response.json()
        
        except HTTPException:
            # 直接重新抛出HTTP异常
            raise
        except Exception as e:
            # 转换其他异常为HTTP异常
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auth0用户创建失败: {str(e)}"
            )
            
    async def delete_auth0_user(self, auth0_user_id: str) -> bool:
        """
        删除Auth0用户
        
        Args:
            auth0_user_id: Auth0用户ID
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            HTTPException: 当删除失败时抛出
        """
        try:
            # 获取管理API令牌
            token = self.get_management_token()
            
            # 删除Auth0用户
            response = requests.delete(
                f"https://{self.domain}/api/v2/users/{auth0_user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code not in (200, 201, 204):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Auth0用户删除失败: {response.text}"
                )
                
            return True
        
        except HTTPException:
            # 直接重新抛出HTTP异常
            raise
        except Exception as e:
            # 转换其他异常为HTTP异常
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auth0用户删除失败: {str(e)}"
            )

    async def login_user(self, login_data: UserLogin) -> str:
        """
        用户登录方法
        
        Args:
            login_data: 用户登录数据，包含email和password
            
        Returns:
            str: access_token
            
        Raises:
            HTTPException: 登录失败时抛出
        """
        try:
            # [ password-realm扩展授权类型 ] 准备请求数据
            request_data = {
                "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
                "username": login_data.email,
                "password": login_data.password,
                "audience": self.audience,
                "scope": "openid profile email offline_access",
                "client_id": self.app_client_id,
                "client_secret": self.app_client_secret,
                "realm": self.connection  # 指定验证的realm（连接）
            }
    
            # 使用用户认证应用凭据
            response = requests.post(
                f"https://{self.domain}/oauth/token",
                json=request_data
            )
            
            # 获取响应内容
            try:
                response_json = response.json()
            except Exception as e:
                print(f"无法解析响应JSON: {str(e)}")
                print(f"原始响应: {response.text}")
                
            if response.status_code != 200:
                error_detail = "登录失败，用户名或密码不正确"
                try:
                    if "error_description" in response_json:
                        error_detail = f"登录失败: {response_json['error_description']}"
                except:
                    pass
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_detail
                )
                
            token_data = response.json()
            # 验证返回数据是否包含必要字段
            if "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Auth0 返回数据格式错误"
                )
                
            # 返回完整的令牌信息
            import time
            
            # 获取当前时间戳（秒）
            current_time = int(time.time())
            
            # 计算绝对过期时间
            # 和第三方登录返回的内容统一
            expires_in = token_data.get("expires_in", 0)
            expires_at = current_time + expires_in if expires_in else None
            
            return {
                "access_token": token_data["access_token"],
                "id_token": token_data.get("id_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": expires_at
            }
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"异常信息: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登录处理失败: {str(e)}"
            )
        
    async def update_auth0_user(self, auth0_user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新Auth0用户信息
        
        Args:
            auth0_user_id: Auth0用户ID
            update_data: 要更新的数据
            
        Returns:
            Dict: 更新后的Auth0用户信息
            
        Raises:
            HTTPException: 当更新失败时抛出
        """
        try:
            # 获取管理API令牌
            token = self.get_management_token()
            
            # 准备Auth0支持的字段
            auth0_update_data = {}
            
            # 映射本地字段到Auth0字段
            field_mapping = {
                "name": "name",
                "email": "email", 
                "phone": "phone_number",
                "picture": "user_metadata.picture",
                "bio": "user_metadata.bio",  # 自定义字段放在user_metadata中
            }
            
            # 构建更新数据
            user_metadata = {}
            app_metadata = {}
            
            for local_field, auth0_field in field_mapping.items():
                if local_field in update_data and update_data[local_field] is not None:
                    if auth0_field.startswith("user_metadata."):
                        # 自定义字段
                        metadata_key = auth0_field.replace("user_metadata.", "")
                        user_metadata[metadata_key] = update_data[local_field]
                    elif auth0_field.startswith("app_metadata."):
                        # 应用元数据
                        metadata_key = auth0_field.replace("app_metadata.", "")
                        app_metadata[metadata_key] = update_data[local_field]
                    else:
                        # 标准字段
                        auth0_update_data[auth0_field] = update_data[local_field]
            
            # 添加元数据
            if user_metadata:
                auth0_update_data["user_metadata"] = user_metadata
            if app_metadata:
                auth0_update_data["app_metadata"] = app_metadata
            
            # 如果有密码更新
            if "password" in update_data and update_data["password"]:
                auth0_update_data["password"] = update_data["password"]
                auth0_update_data["connection"] = self.connection
            
            logger.info(f"更新Auth0用户: {auth0_user_id}, 数据: {auth0_update_data}")
            
            # 调用Auth0 API更新用户
            response = requests.patch(
                f"https://{self.domain}/api/v2/users/{auth0_user_id}",
                json=auth0_update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code not in (200, 201):
                error_detail = f"Auth0用户更新失败: {response.text}"
                logger.error(error_detail)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
            
            updated_user = response.json()
            logger.info(f"Auth0用户更新成功: {auth0_user_id}")
            return updated_user
        
        except HTTPException:
            # 直接重新抛出HTTP异常
            raise
        except Exception as e:
            # 转换其他异常为HTTP异常
            error_msg = f"Auth0用户更新失败: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
