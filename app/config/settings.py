from dataclasses import dataclass
import os
import warnings


@dataclass
class LLMConfig:
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    region: str = "us-west-2"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class APIConfig:
    vidcap_api_key: str = None
    openai_api_key: str = None
    aws_region: str = None
    s3_bucket: str = None

    def __post_init__(self):
        """초기화 후 환경 변수에서 값 로드"""
        self.vidcap_api_key = os.getenv("VIDCAP_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")

        # 경고 발생 (환경 검증에서 이미 체크했지만 추가 안전장치)
        if not self.vidcap_api_key:
            warnings.warn("VIDCAP_API_KEY가 설정되지 않았습니다.")
        if not self.openai_api_key:
            warnings.warn("OPENAI_API_KEY가 설정되지 않았습니다.")
        if not self.aws_region:
            warnings.warn("AWS_REGION이 설정되지 않았습니다.")
        if not self.s3_bucket:
            warnings.warn("S3_BUCKET_NAME이 설정되지 않았습니다.")


# 싱글톤 인스턴스
llm_config = LLMConfig()
api_config = APIConfig()