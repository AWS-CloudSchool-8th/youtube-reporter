# app/models/response.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """작업 상태"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VisualizationType(str, Enum):
    """시각화 타입"""
    CHART = "chart"
    DIAGRAM = "diagram"
    TABLE = "table"
    ADVANCED = "advanced"


class SectionType(str, Enum):
    """섹션 타입"""
    TEXT = "text"
    VISUALIZATION = "visualization"


class ProcessVideoResponse(BaseModel):
    """영상 처리 응답"""
    job_id: str
    status: JobStatus
    message: str
    created_at: datetime = datetime.now()


class JobStatusResponse(BaseModel):
    """작업 상태 응답"""
    job_id: str
    status: JobStatus
    progress: int
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class VisualizationData(BaseModel):
    """시각화 데이터"""
    type: VisualizationType
    library: Optional[str] = None  # chartjs, mermaid, etc.
    config: Optional[Dict[str, Any]] = None
    code: Optional[str] = None  # Mermaid 코드
    headers: Optional[List[str]] = None  # 테이블 헤더
    rows: Optional[List[List[Any]]] = None  # 테이블 데이터


class ReportSection(BaseModel):
    """리포트 섹션"""
    id: str
    title: str
    type: SectionType

    # 텍스트 섹션용
    content: Optional[str] = None
    level: Optional[int] = None  # 1: 대제목, 2: 중제목, 3: 소제목
    keywords: Optional[List[str]] = []

    # 시각화 섹션용
    visualization_type: Optional[str] = None
    data: Optional[VisualizationData] = None
    insight: Optional[str] = None
    purpose: Optional[str] = None
    user_benefit: Optional[str] = None
    error: Optional[str] = None


class ReportStatistics(BaseModel):
    """리포트 통계"""
    total_sections: int = 0
    text_sections: int = 0
    visualizations: int = 0


class ProcessInfo(BaseModel):
    """처리 정보"""
    youtube_url: str
    caption_length: int = 0
    summary_length: int = 0
    processing_time: Optional[float] = None
    error: Optional[str] = None


class ReportResult(BaseModel):
    """최종 리포트 결과"""
    success: bool
    title: str
    summary: str  # 간단한 요약
    sections: List[ReportSection]
    statistics: ReportStatistics
    process_info: ProcessInfo
    created_at: datetime = datetime.now()


class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now()