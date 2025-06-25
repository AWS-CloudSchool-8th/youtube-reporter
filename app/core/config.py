# app/core/config.py
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "YouTube Reporter"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API 키
    vidcap_api_key: str = ""
    aws_region: str = "us-west-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # LLM 설정
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002"
    ]
    
    # VidCap API 설정
    vidcap_api_url: str = "https://vidcap.xyz/api/v1/youtube/caption"
    
    # 성능 설정
    max_concurrent_jobs: int = 5
    job_timeout: int = 300
    cleanup_interval_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# 전역 설정 인스턴스
settings = Settings()


def validate_settings():
    """필수 설정 검증"""
    required_settings = [
        ("VIDCAP_API_KEY", settings.vidcap_api_key),
        ("AWS_REGION", settings.aws_region),
        ("AWS_BEDROCK_MODEL_ID", settings.bedrock_model_id)
    ]
    
    missing = []
    for name, value in required_settings:
        if not value:
            missing.append(name)
    
    if missing:
        raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}")