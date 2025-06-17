from dataclasses import dataclass
import os
import warnings


@dataclass
class LLMConfig:
    model_id: str = None
    region: str = None
    temperature: float = 0.7
    max_tokens: int = 4096

    def __post_init__(self):
        """환경 변수에서 값 로드"""
        self.model_id = os.getenv("AWS_BEDROCK_MODEL_ID")
        self.region = os.getenv("AWS_REGION")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))


@dataclass
class APIConfig:
    # YouTube 자막 관련
    vidcap_api_key: str = None
    vidcap_api_url: str = None

    # OpenAI 관련
    openai_api_key: str = None
    dalle_model: str = None
    dalle_image_size: str = None

    # AWS 관련
    aws_region: str = None
    s3_bucket: str = None

    def __post_init__(self):
        """초기화 후 환경 변수에서 값 로드"""
        # YouTube 자막 설정
        self.vidcap_api_key = os.getenv("VIDCAP_API_KEY")
        self.vidcap_api_url = os.getenv("VIDCAP_API_URL", "https://vidcap.xyz/api/v1/youtube/caption")

        # OpenAI 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.dalle_model = os.getenv("DALLE_MODEL", "dall-e-3")
        self.dalle_image_size = os.getenv("DALLE_IMAGE_SIZE", "1024x1024")

        # AWS 설정
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