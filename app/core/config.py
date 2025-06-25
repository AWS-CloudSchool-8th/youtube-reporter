import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    VIDCAP_API_KEY: str = os.getenv("VIDCAP_API_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-west-2")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # LangSmith 설정
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "youtube-reporter")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")

settings = Settings()