import boto3
from app.config import S3_BUCKET_NAME

_s3 = boto3.client("s3")

def upload_bytes(content: bytes, key: str) -> str:
    _s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=content)
    return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{key}"