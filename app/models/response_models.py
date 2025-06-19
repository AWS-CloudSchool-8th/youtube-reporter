# app/models/response_models.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class VisualizationSection(BaseModel):
    type: str  # paragraph, heading, bar_chart, line_chart, pie_chart, mindmap
    title: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    position: int = 0

class ReportResult(BaseModel):
    title: str
    sections: List[VisualizationSection]
    created_at: datetime

class ProcessVideoResponse(BaseModel):
    job_id: str
    status: str
    message: str