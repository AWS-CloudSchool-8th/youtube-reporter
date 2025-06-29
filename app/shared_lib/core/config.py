import os
from dotenv import load_dotenv
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Analysis API"
    VERSION: str = "1.0.0"

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    AWS_S3_BUCKET: Optional[str] = None

    POLLY_VOICE_ID: str = "Seoyeon"

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    API_V1_STR: str = "/api/v1"
    S3_BUCKET_NAME: str = "content-analysis-reports"

    VIDCAP_API_KEY: str = ""

    YOUTUBE_API_KEY: Optional[str] = None

    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_ENDPOINT: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None
    LANGCHAIN_TRACING_V2: Optional[str] = None

    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_CLIENT_ID: Optional[str] = None
    COGNITO_CLIENT_SECRET: Optional[str] = None
    
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/backend_final"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 

