# app/utils/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Config:
    # 필수 환경 변수
    VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_BEDROCK_MODEL_ID = os.getenv("AWS_BEDROCK_MODEL_ID")

    # 선택적 환경 변수
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """필수 환경 변수 검증"""
        required_vars = [
            "VIDCAP_API_KEY",
            "AWS_REGION",
            "AWS_BEDROCK_MODEL_ID"
        ]

        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            raise ValueError(f"필수 환경 변수가 설정되지 않음: {', '.join(missing)}")

        print("✅ 환경 변수 검증 완료")
