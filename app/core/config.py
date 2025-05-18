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
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "your-domain.auth0.com")
    AUTH0_API_AUDIENCE: str = os.getenv("AUTH0_API_AUDIENCE", "https://api.example.com")
    AUTH0_ALGORITHMS: str = os.getenv("AUTH0_ALGORITHMS", "RS256")
    AUTH0_ISSUER: str = os.getenv("AUTH0_ISSUER", f"https://{os.getenv('AUTH0_DOMAIN', 'your-domain.auth0.com')}/")
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_CONNECTION: str = os.getenv("AUTH0_CONNECTION", "Username-Password-Authentication")
    AUTH0_MANAGEMENT_CLIENT_ID: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", "")
    AUTH0_MANAGEMENT_CLIENT_SECRET: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", "")
    
    class Config:
        case_sensitive = True

settings = Settings() 