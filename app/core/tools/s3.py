import boto3
import os
from mimetypes import guess_type
from config.settings import api_config
from utils.exceptions import S3UploadError
from utils.error_handler import safe_execute


def _upload_to_s3_impl(file_path: str, object_name: str = None, content_type: str = None) -> str:
    """실제 S3 업로드 로직 (내부용)"""
    if not os.path.exists(file_path):
        raise S3UploadError(f"File not found: {file_path}", "upload_to_s3")

    if not api_config.s3_bucket:
        raise S3UploadError("S3 bucket name not configured", "upload_to_s3")

    s3 = boto3.client("s3", region_name=api_config.aws_region)
    bucket_name = api_config.s3_bucket
    object_name = object_name or os.path.basename(file_path)
    content_type = content_type or guess_type(file_path)[0] or "application/octet-stream"

    s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={
        "ACL": "public-read",
        "ContentType": content_type
    })

    return f"https://{bucket_name}.s3.{api_config.aws_region}.amazonaws.com/{object_name}"


def upload_to_s3(file_path: str, object_name: str = None, content_type: str = None) -> str:
    """안전한 S3 업로드 (에러 처리 포함)"""
    return safe_execute(
        _upload_to_s3_impl,
        file_path,
        object_name=object_name,
        content_type=content_type,
        context="upload_to_s3",
        default_return=""
    )