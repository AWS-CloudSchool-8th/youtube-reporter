import os
from dotenv import load_dotenv

load_dotenv()

VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")