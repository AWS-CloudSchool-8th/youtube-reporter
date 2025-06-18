# models/report.py (수정됨)
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from .base_model import BaseModel

class VisualizationType(Enum):
    PARAGRAPH = "paragraph"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    TIMELINE = "timeline"
    IMAGE = "image"

@dataclass
class VisualizationData:
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportSection(BaseModel):
    # BaseModel의 필드들이 기본값을 가지므로 모든 필드에 기본값 필요
    type: VisualizationType = VisualizationType.PARAGRAPH
    position: int = 0
    title: Optional[str] = None
    content: Optional[str] = None  # 텍스트용
    visualization_data: Optional[VisualizationData] = None  # 차트용

@dataclass
class Report(BaseModel):
    # BaseModel의 필드들이 기본값을 가지므로 모든 필드에 기본값 필요
    title: str = ""
    youtube_url: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    status: str = "processing"  # processing, completed, failed
    error_message: Optional[str] = None