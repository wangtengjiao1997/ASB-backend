from fastapi_auth0 import Auth0
from app.core.config import settings


auth = Auth0(
    domain=settings.AUTH0_DOMAIN,
    api_audience=settings.AUTH0_API_AUDIENCE,
    scopes={
        'read:users': '读取用户信息的权限',
        'write:users': '修改用户信息的权限',
        'delete:users': '删除用户的权限'
    }
)

