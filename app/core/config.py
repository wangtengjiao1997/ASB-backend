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
    
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "wx78a6328bda6d1b87")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "23008719bb083537d11d8d66068fb535")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_DB: str = os.getenv("REDIS_DB", "0")
    REDIS_USERNAME: str = os.getenv("REDIS_USERNAME", "")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_PREFIX: str = os.getenv("REDIS_PREFIX", "undefined:")
    
    # DeepSeek AI配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # FCM配置
    FCM_CREDENTIALS_PATH: str = os.getenv("FCM_CREDENTIALS_PATH", "")
    
    class Config:
        case_sensitive = True

settings = Settings() 