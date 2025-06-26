from typing import List, Optional, Dict, Any
from datetime import datetime
import boto3
from fastapi import HTTPException
from app.models.report import ReportInfo, ReportListResponse
from app.core.config import settings

class ReportService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    async def list_reports(self, prefix: str = "reports/", max_keys: int = 100,
                         continuation_token: Optional[str] = None) -> ReportListResponse:
        """S3에 저장된 리포트 목록 조회"""
        try:
            # S3 객체 목록 조회
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
                ContinuationToken=continuation_token
            )

            # 리포트 정보 변환
            reports = []
            for item in response.get("Contents", []):
                report = ReportInfo(
                    report_id=item["Key"].split("/")[-1].split(".")[0],
                    filename=item["Key"].split("/")[-1],
                    content_type=self._get_content_type(item["Key"]),
                    size=item["Size"],
                    s3_key=item["Key"],
                    created_at=item["LastModified"]
                )
                reports.append(report)

            return ReportListResponse(
                reports=reports,
                total_count=response.get("KeyCount", 0),
                next_token=response.get("NextContinuationToken")
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"S3 리포트 목록 조회 실패: {str(e)}")

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """리포트 다운로드 URL 생성"""
        try:
            # 리포트 메타데이터 조회
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=f"reports/{report_id}.pdf"
            )

            # 다운로드 URL 생성
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': f"reports/{report_id}.pdf"
                },
                ExpiresIn=3600  # 1시간
            )

            return {
                "report_id": report_id,
                "filename": f"{report_id}.pdf",
                "content_type": "application/pdf",
                "size": response["ContentLength"],
                "download_url": url,
                "expires_at": datetime.now().timestamp() + 3600
            }

        except self.s3_client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
            raise HTTPException(status_code=500, detail=f"S3 리포트 조회 실패: {str(e)}")

    def _get_content_type(self, key: str) -> str:
        """파일 확장자에 따른 Content-Type 반환"""
        ext = key.split(".")[-1].lower()
        content_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "txt": "text/plain"
        }
        return content_types.get(ext, "application/octet-stream")

report_service = ReportService() 