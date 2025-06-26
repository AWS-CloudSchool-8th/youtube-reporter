import boto3
import json
from typing import Dict, Any, List
from datetime import datetime
from app.core.config import settings

class UserS3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def _get_user_path(self, user_id: str, file_type: str) -> str:
        """����ں� S3 ��� ����"""
        return f"users/{user_id}/{file_type}/"
    
    def upload_user_report(self, user_id: str, job_id: str, content: str, file_type: str = "json") -> str:
        """����ں� ���� ���ε�"""
        try:
            path = self._get_user_path(user_id, "reports")
            key = f"{path}{job_id}_report.{file_type}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=f"application/{file_type}",
                Metadata={
                    "user_id": user_id,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return key
        except Exception as e:
            raise Exception(f"���� ���ε� ����: {str(e)}")
    
    def upload_user_audio(self, user_id: str, job_id: str, audio_data: bytes) -> str:
        """����ں� ����� ���� ���ε�"""
        try:
            path = self._get_user_path(user_id, "audio")
            key = f"{path}{job_id}_audio.mp3"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=audio_data,
                ContentType="audio/mpeg",
                Metadata={
                    "user_id": user_id,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return key
        except Exception as e:
            raise Exception(f"����� ���ε� ����: {str(e)}")
    
    def upload_user_visual(self, user_id: str, job_id: str, visual_data: bytes, visual_name: str) -> str:
        """����ں� �ð�ȭ ���� ���ε�"""
        try:
            path = self._get_user_path(user_id, "visuals")
            key = f"{path}{job_id}_{visual_name}.png"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=visual_data,
                ContentType="image/png",
                Metadata={
                    "user_id": user_id,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return key
        except Exception as e:
            raise Exception(f"�ð�ȭ ���ε� ����: {str(e)}")
    
    def get_user_files(self, user_id: str, file_type: str = None) -> List[Dict]:
        """����� ���� ��� ��ȸ"""
        try:
            if file_type:
                prefix = self._get_user_path(user_id, file_type)
            else:
                prefix = f"users/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                # ��Ÿ������ ��ȸ
                metadata_response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=obj['Key']
                )
                
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "metadata": metadata_response.get('Metadata', {})
                })
            
            return files
        except Exception as e:
            raise Exception(f"���� ��� ��ȸ ����: {str(e)}")
    
    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """���� ����� URL ����"""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
        except Exception as e:
            raise Exception(f"URL ���� ����: {str(e)}")
    
    def delete_user_file(self, s3_key: str):
        """����� ���� ����"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
        except Exception as e:
            raise Exception(f"���� ���� ����: {str(e)}")

user_s3_service = UserS3Service()