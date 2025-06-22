import boto3
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket_name = settings.S3_BUCKET_NAME

    def generate_report_id(self, content: str) -> str:
        """보고서 내용 기반 고유 ID 생성"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

    def sanitize_filename(self, filename: str) -> str:
        """파일명에서 특수문자 제거"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', filename)

    async def upload_report(self, report_content: str, job_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """보고서를 S3에 업로드"""
        try:
            report_id = self.generate_report_id(report_content)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON 형태로 보고서 저장
            report_data = {
                "job_id": job_id,
                "report_id": report_id,
                "content": report_content,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "word_count": len(report_content.split()),
                "character_count": len(report_content)
            }
            
            # S3 키 생성
            s3_key = f"reports/{timestamp}_{job_id}_{report_id}.json"
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(report_data, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={
                    'job-id': job_id,
                    'report-id': report_id,
                    'created-at': timestamp,
                    'content-type': 'analysis-report'
                }
            )
            
            # 텍스트 파일도 별도 저장
            text_s3_key = f"reports/text/{timestamp}_{job_id}_{report_id}.txt"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=text_s3_key,
                Body=report_content.encode('utf-8'),
                ContentType='text/plain; charset=utf-8'
            )
            
            return {
                "success": True,
                "report_id": report_id,
                "s3_key": s3_key,
                "text_s3_key": text_s3_key,
                "bucket": self.bucket_name,
                "url": f"s3://{self.bucket_name}/{s3_key}",
                "size": len(json.dumps(report_data, ensure_ascii=False))
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """S3에서 보고서 조회"""
        try:
            # S3에서 보고서 검색
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"reports/",
                MaxKeys=1000
            )
            
            for obj in response.get('Contents', []):
                if report_id in obj['Key'] and obj['Key'].endswith('.json'):
                    # 보고서 다운로드
                    file_response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                    content = file_response['Body'].read().decode('utf-8')
                    return {
                        "success": True,
                        "data": json.loads(content),
                        "s3_key": obj['Key'],
                        "last_modified": obj['LastModified'].isoformat()
                    }
            
            raise HTTPException(status_code=404, detail=f"보고서 ID {report_id}를 찾을 수 없습니다")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 조회 실패: {str(e)}")

    async def list_reports(self, limit: int = 20) -> Dict[str, Any]:
        """S3에 저장된 보고서 목록 조회"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="reports/",
                MaxKeys=limit
            )
            
            reports = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.json'):
                    try:
                        head_response = self.s3_client.head_object(Bucket=self.bucket_name, Key=obj['Key'])
                        metadata = head_response.get('Metadata', {})
                        
                        reports.append({
                            "s3_key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "job_id": metadata.get('job-id', 'unknown'),
                            "report_id": metadata.get('report-id', 'unknown'),
                            "created_at": metadata.get('created-at', 'unknown')
                        })
                    except Exception as e:
                        print(f"메타데이터 조회 실패: {e}")
                        continue
            
            return {
                "total_reports": len(reports),
                "reports": sorted(reports, key=lambda x: x["last_modified"], reverse=True),
                "bucket": self.bucket_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 보고서 목록 조회 실패: {str(e)}")

    async def delete_report(self, s3_key: str) -> bool:
        """S3에서 보고서 삭제"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"보고서 삭제 실패: {str(e)}")

s3_service = S3Service() 