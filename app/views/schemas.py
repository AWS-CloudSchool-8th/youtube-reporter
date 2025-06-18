# views/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime

class ProcessVideoRequest(BaseModel):
    youtube_url: HttpUrl
    options: Optional[Dict[str, Any]] = {}

class VisualizationResponse(BaseModel):
    id: str
    type: str
    title: Optional[str]
    content: Optional[str]
    data: Optional[Dict[str, Any]]
    position: int

class ReportResponse(BaseModel):
    id: str
    title: str
    youtube_url: str
    status: str
    sections: List[VisualizationResponse]
    created_at: datetime
    error_message: Optional[str] = None

class ProcessVideoResponse(BaseModel):
    job_id: str
    report_id: str
    status: str
    message: str