from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReportInfo(BaseModel):
    report_id: str = Field(..., description="Report ID")
    filename: str = Field(..., description="File name")
    content_type: str = Field(..., description="File type")
    size: int = Field(..., description="File size (bytes)")
    s3_key: str = Field(..., description="S3 object key")
    created_at: datetime = Field(..., description="Created time")

class ReportListResponse(BaseModel):
    reports: List[ReportInfo] = Field(..., description="List of reports")
    total_count: int = Field(..., description="Total number of reports")
    next_token: Optional[str] = Field(None, description="Next page token")

