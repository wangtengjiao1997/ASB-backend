from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "undefined backend"
    API_V1_STR: str = "/api/v1"
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "undefined")
    
    # Auth0配置
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "undefined.auth0.com")
    AUTH0_API_AUDIENCE: str = os.getenv("AUTH0_API_AUDIENCE", "https://api.example.com")
    AUTH0_ALGORITHMS: str = os.getenv("AUTH0_ALGORITHMS", "RS256")
    AUTH0_ISSUER: str = os.getenv("AUTH0_ISSUER", f"https://{os.getenv('AUTH0_DOMAIN', 'undefined.auth0.com')}/")
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_CONNECTION: str = os.getenv("AUTH0_CONNECTION", "Username-Password-Authentication")
    AUTH0_MANAGEMENT_CLIENT_ID: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", "")
    AUTH0_MANAGEMENT_CLIENT_SECRET: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", "")
    
    AUTH0_APP_CLIENT_ID: str = os.getenv("AUTH0_APP_CLIENT_ID", "")
    AUTH0_APP_CLIENT_SECRET: str = os.getenv("AUTH0_APP_CLIENT_SECRET", "")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_DB: str = os.getenv("REDIS_DB", "0")
    REDIS_USERNAME: str = os.getenv("REDIS_USERNAME", "")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_PREFIX: str = os.getenv("REDIS_PREFIX", "undefined:")
    
    # AI服务配置
    AI_SERVICE_BOT_BASE_URL: str = os.getenv("AI_SERVICE_BOT_BASE_URL", "")
    AI_INFO_BOT_BASE_URL: str = os.getenv("AI_INFO_BOT_BASE_URL", "")
    AI_DISCORD_BOT_BASE_URL: str = os.getenv("AI_DISCORD_BOT_BASE_URL", "")
    AI_SERVICE_BASE_URL: str = os.getenv("AI_SERVICE_BASE_URL", "")
    AI_CONTENT_CREATION_BOT_BASE_URL: str = os.getenv("AI_CONTENT_CREATION_BOT_BASE_URL", "")
    AI_LIVE_CARD_CREATION_BOT_BASE_URL: str = os.getenv("AI_LIVE_CARD_CREATION_BOT_BASE_URL", "")

    # aws文件上传配置
    AWS_ACCOUNT_ID: str = os.getenv("AWS_ACCOUNT_ID", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "")

    # 邮件服务配置
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "")
    EMAIL_SES_REGION: str = os.getenv("EMAIL_SES_REGION", "us-east-1")
    AWS_SES_SMTP_PASSWORD: str = os.getenv("AWS_SES_SMTP_PASSWORD", "")
    AWS_SES_SMTP_USERNAME: str = os.getenv("AWS_SES_SMTP_USERNAME", "")
    
    # FCM配置
    FCM_CREDENTIALS_PATH: str = os.getenv("FCM_CREDENTIALS_PATH", "")
    
    class Config:
        case_sensitive = True

settings = Settings() 