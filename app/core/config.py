# app/core/config.py - 정리된 설정
import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # ===== 기본 설정 =====
    app_name: str = "YouTube Reporter"
    app_version: str = "2.0.0"
    debug: bool = False

    # ===== 서버 설정 =====
    host: str = "0.0.0.0"
    port: int = 8000

    # ===== 필수 API 키들 =====
    vidcap_api_key: str = Field(..., description="VidCap API 키 (필수)")
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-west-2"

    # ===== AWS Bedrock 설정 =====
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # ===== LLM 설정 (복원됨!) =====
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="LLM 온도 설정")
    llm_max_tokens: int = Field(default=4096, ge=1, le=8192, description="LLM 최대 토큰 수")

    # ===== 선택적 설정 =====
    s3_bucket_name: Optional[str] = None
    openai_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None

    # ===== LangSmith 추적 설정 =====
    langchain_tracing_v2: bool = False
    langchain_project: str = "youtube-reporter"
    langchain_api_key: Optional[str] = None

    # ===== 로깅 설정 =====
    log_level: str = "INFO"

    # ===== CORS 설정 =====
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]

    # ===== VidCap API 설정 =====
    vidcap_api_url: str = "https://vidcap.xyz/api/v1/youtube/caption"

    # ===== 개발 설정 =====
    auto_reload: bool = True

    # ===== 성능 설정 (실제 사용되는 것만) =====
    max_concurrent_jobs: int = 5
    job_timeout: int = 300  # 5분
    cleanup_interval_hours: int = 24

    # Pydantic v2 설정
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # 추가 필드 무시
        "validate_assignment": True,
    }

    @validator('allowed_origins', pre=True)
    def parse_origins(cls, v):
        """CORS origins 파싱"""
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return [origin.strip() for origin in v.split(',')]
        return v

    @validator('vidcap_api_key')
    def validate_api_key(cls, v):
        """API 키 검증"""
        if not v or v == "your_vidcap_api_key_here":
            raise ValueError("VIDCAP_API_KEY는 반드시 설정해야 합니다")
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """로그 레벨 검증"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL은 다음 중 하나여야 합니다: {valid_levels}")
        return v.upper()

    @validator('llm_temperature')
    def validate_temperature(cls, v):
        """LLM 온도 검증"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("LLM_TEMPERATURE는 0.0-2.0 사이여야 합니다")
        return v

    @validator('llm_max_tokens')
    def validate_max_tokens(cls, v):
        """LLM 최대 토큰 검증"""
        if not 1 <= v <= 8192:
            raise ValueError("LLM_MAX_TOKENS는 1-8192 사이여야 합니다")
        return v

    def validate_required_settings(self) -> None:
        """필수 설정 검증"""
        required_fields = [
            ("vidcap_api_key", "VIDCAP_API_KEY"),
            ("aws_region", "AWS_REGION"),
            ("bedrock_model_id", "BEDROCK_MODEL_ID"),
        ]

        missing = []
        for field, env_var in required_fields:
            value = getattr(self, field)
            if not value or value == f"your_{field}_here":
                missing.append(env_var)

        if missing:
            raise ValueError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}"
            )

    def get_llm_config(self) -> dict:
        """LLM 설정 반환"""
        return {
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens
        }

    def get_masked_config(self) -> dict:
        """민감한 정보를 마스킹한 설정 반환"""
        config = self.model_dump()
        sensitive_keys = [
            'vidcap_api_key', 'aws_access_key_id', 'aws_secret_access_key',
            'openai_api_key', 'youtube_api_key', 'langchain_api_key'
        ]

        for key in sensitive_keys:
            if key in config and config[key]:
                config[key] = f"{config[key][:4]}***"

        return config


# 전역 설정 인스턴스
settings = Settings()


# 설정 검증 (로거 사용)
def validate_and_log_settings():
    """설정 검증 및 로깅"""
    from ..utils.logger import get_logger
    logger = get_logger(__name__)

    try:
        settings.validate_required_settings()
        logger.info("✅ 환경 변수 검증 완료")

        # 마스킹된 설정 로깅 (중요한 것만)
        logger.info("📋 주요 설정:")
        logger.info(f"  - 앱: {settings.app_name} v{settings.app_version}")
        logger.info(f"  - 디버그 모드: {settings.debug}")
        logger.info(f"  - 서버: {settings.host}:{settings.port}")
        logger.info(f"  - AWS 리전: {settings.aws_region}")
        logger.info(f"  - LLM 온도: {settings.llm_temperature}")
        logger.info(f"  - LLM 최대 토큰: {settings.llm_max_tokens}")
        logger.info(f"  - VidCap API: {'✅' if settings.vidcap_api_key else '❌'}")
        logger.info(f"  - AWS 설정: {'✅' if settings.aws_access_key_id else '❌'}")
        logger.info(f"  - LangSmith 추적: {'✅' if settings.langchain_tracing_v2 else '❌'}")

    except ValueError as e:
        logger.error(f"❌ 설정 오류: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 예상치 못한 설정 오류: {e}")
        import sys
        sys.exit(1)


# 설정 검증 실행 (초기화 시)
if __name__ != "__main__":  # 테스트나 직접 실행이 아닐 때만
    validate_and_log_settings()