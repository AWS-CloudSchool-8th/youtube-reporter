import boto3
import os
from app.core.config import settings

class S3Service:
    def __init__(self):
        # ��������� �ڰ� ���� ����
        self.s3_client = boto3.client(
            's3', 
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # AWS_S3_BUCKET�� �켱 ����ϰ�, ������ S3_BUCKET_NAME ���
        self.bucket_name = settings.AWS_S3_BUCKET or settings.S3_BUCKET_NAME
        
        # �ʱ�ȭ �� ��Ŷ ���� ���
        print(f"?? S3 ���� �ʱ�ȭ: ��Ŷ={self.bucket_name}, ����={settings.AWS_REGION}")
    
    def upload_file(self, file_path, object_name=None, content_type=None, acl="public-read"):
        """������ S3�� ���ε�"""
        try:
            # ��ü �̸��� �������� ���� ��� ���� �̸� ���
            if object_name is None:
                object_name = os.path.basename(file_path)
            
            # ���� ���� Ȯ��
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"������ ã�� �� ����: {file_path}")
            
            # ���� ũ�� Ȯ��
            file_size = os.path.getsize(file_path)
            
            # ���ε� �ɼ� ����
            extra_args = {"ACL": acl}
            if content_type:
                extra_args["ContentType"] = content_type
            
            # ���� ���ε�
            print(f"?? S3 ���ε� ����: {file_path} �� {object_name} (ũ��: {file_size} ����Ʈ)")
            
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    object_name,
                    ExtraArgs=extra_args
                )
            
            # ���ε� ���� �� URL ��ȯ
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            print(f"? S3 ���ε� ����: {url}")
            return url
            
        except Exception as e:
            error_msg = f"? S3 ���ε� ����: {str(e)}"
            print(error_msg)
            return f"[S3 upload failed: {str(e)}]"
    
    def list_objects(self, prefix="", max_keys=100):
        """S3 ��Ŷ �� ��ü ��� ��ȸ"""
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
            print(f"? S3 ��ü ��� ��ȸ ����: {str(e)}")
            return []

    def get_file_content(self, object_name: str) -> str:
        """S3���� ���� ������ ���ڿ��� �о����"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            # ���� ������ UTF-8�� ���ڵ�
            content = response['Body'].read().decode('utf-8')
            print(f"? S3 ���� ���� �б� ����: {object_name}")
            return content
            
        except Exception as e:
            print(f"? S3 ���� ���� �б� ����: {object_name} - {str(e)}")
            return None

# �̱��� �ν��Ͻ�
s3_service = S3Service()