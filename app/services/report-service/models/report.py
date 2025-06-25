from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReportInfo(BaseModel):
    report_id: str = Field(..., description="리포트 ID")
    filename: str = Field(..., description="파일명")
    content_type: str = Field(..., description="파일 형식")
    size: int = Field(..., description="파일 크기 (bytes)")
    s3_key: str = Field(..., description="S3 저장 경로")
    created_at: datetime = Field(..., description="생성 시간")

class ReportListResponse(BaseModel):
    reports: List[ReportInfo] = Field(..., description="리포트 목록")
    total_count: int = Field(..., description="전체 리포트 수")
    next_token: Optional[str] = Field(None, description="다음 페이지 토큰") 
