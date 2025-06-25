# app/models/response.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class JobStatus(BaseModel):
    """작업 상태 모델"""
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class VisualizationData(BaseModel):
    """시각화 데이터 모델"""
    type: str  # chart, diagram, table, advanced
    library: Optional[str] = None  # chartjs, mermaid, d3, etc.
    config: Optional[Dict[str, Any]] = None
    code: Optional[str] = None  # For mermaid diagrams
    headers: Optional[List[str]] = None  # For tables
    rows: Optional[List[List[Any]]] = None  # For tables
    visualization_type: Optional[str] = None  # Specific viz type
    data: Optional[Dict[str, Any]] = None  # Generic data


class ReportSection(BaseModel):
    """리포트 섹션 모델"""
    id: str
    title: str
    type: str  # text, visualization
    content: Optional[str] = None  # For text sections
    level: Optional[int] = None  # 1: 대제목, 2: 중제목, 3: 소제목
    keywords: Optional[List[str]] = []

    # For visualization sections
    visualization_type: Optional[str] = None
    data: Optional[Union[VisualizationData, Dict[str, Any]]] = None
    insight: Optional[str] = None
    purpose: Optional[str] = None
    user_benefit: Optional[str] = None
    error: Optional[str] = None


class ProcessVideoResponse(BaseModel):
    """비디오 처리 응답 모델"""
    job_id: str
    status: str
    message: str


class ReportResult(BaseModel):
    """최종 리포트 결과 모델"""
    success: bool
    title: str
    summary: str  # Brief summary
    sections: List[ReportSection]
    statistics: Dict[str, int]  # total_sections, text_sections, visualizations
    process_info: Dict[str, Any]  # youtube_url, caption_length, etc.
    created_at: Optional[datetime] = None