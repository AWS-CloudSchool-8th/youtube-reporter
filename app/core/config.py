# app/core/config.py
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 기본 설정
    app_name: str = "YouTube Reporter"
    app_version: str = "2.0.0"
    debug: bool = False

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    # API 키들
    vidcap_api_key: str
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-west-2"

    # AWS Bedrock 설정
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # S3 설정 (선택적)
    s3_bucket_name: Optional[str] = None

    # OpenAI 설정 (선택적)
    openai_api_key: Optional[str] = None

    # YouTube API 설정 (선택적)
    youtube_api_key: Optional[str] = None

    # LangSmith 추적 설정 (선택적)
    langchain_tracing_v2: bool = False
    langchain_project: str = "youtube-reporter"
    langchain_api_key: Optional[str] = None

    # 로깅 설정
    log_level: str = "INFO"

    # CORS 설정
    allowed_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]

    # VidCap API 설정
    vidcap_api_url: str = "https://vidcap.xyz/api/v1/youtube/caption"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_required_settings(self) -> None:
        """필수 설정 검증"""
        required_fields = [
            ("vidcap_api_key", "VIDCAP_API_KEY"),
            ("aws_region", "AWS_REGION"),
            ("bedrock_model_id", "BEDROCK_MODEL_ID"),
        ]

        missing = []
        for field, env_var in required_fields:
            if not getattr(self, field):
                missing.append(env_var)

        if missing:
            raise ValueError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}"
            )


# 전역 설정 인스턴스
settings = Settings()

# 설정 검증
try:
    settings.validate_required_settings()
    print("✅ 환경 변수 검증 완료")
except ValueError as e:
    print(f"❌ 설정 오류: {e}")
    import sys

    sys.exit(1)