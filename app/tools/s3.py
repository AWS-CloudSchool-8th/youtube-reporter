import boto3
import os
from mimetypes import guess_type

def upload_to_s3(file_path: str, object_name: str = None, content_type: str = None) -> str:
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    bucket_name = os.getenv("S3_BUCKET_NAME")
    object_name = object_name or os.path.basename(file_path)
    content_type = content_type or guess_type(file_path)[0] or "application/octet-stream"

    s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={
        "ACL": "public-read",
        "ContentType": content_type
    })

    return f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"