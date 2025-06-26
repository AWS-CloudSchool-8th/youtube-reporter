import boto3
import os
from shared_lib.core.config import settings

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3', 
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        self.bucket_name = settings.AWS_S3_BUCKET or settings.S3_BUCKET_NAME
        
        
        print(f" S3 initialization: bucket={self.bucket_name}, region={settings.AWS_REGION}")
    
    def upload_file(self, file_path, object_name=None, content_type=None, acl="public-read"):
        try:
            if object_name is None:
                object_name = os.path.basename(file_path)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"can't find files: {file_path}")
            
            file_size = os.path.getsize(file_path)
            
            extra_args = {"ACL": acl}
            if content_type:
                extra_args["ContentType"] = content_type
            
            print(f"Start uploading to S3: {file_path} to {object_name} (Size: {file_size} byte)")
            
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    object_name,
                    ExtraArgs=extra_args
                )
            
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            print(f"Success uploacing to S3: {url}")
            return url
            
        except Exception as e:
            error_msg = f"S3 upload failed: {str(e)}"
            print(error_msg)
            return f"[S3 upload failed: {str(e)}]"
    
    def list_objects(self, prefix="", max_keys=100):
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                return response['Contents']
            return []
            
        except Exception as e:
            print(f"S3 search failed: {str(e)}")
            return []

    def get_file_content(self, object_name: str) -> str:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            content = response['Body'].read().decode('utf-8')
            print(f"Success to read S3: {object_name}")
            return content
            
        except Exception as e:
            print(f"fail to read S3: {object_name} - {str(e)}")
            return None

s3_service = S3Service()