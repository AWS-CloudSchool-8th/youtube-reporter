from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from .base_model import BaseModel


class VisualizationType(Enum):
    # 기존 타입
    PARAGRAPH = "paragraph"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    TIMELINE = "timeline"
    IMAGE = "image"

    # 🔑 새로 추가: 고급 시각화 타입들
    MINDMAP = "mindmap"
    FLOWCHART = "flowchart"
    COMPARISON = "comparison"
    TREE = "tree"
    HIERARCHY = "hierarchy"
    NETWORK = "network"
    PROCESS = "process"
    MATRIX = "matrix"
    CYCLE = "cycle"
    HEADING = "heading"


@dataclass
class VisualizationData:
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    # 🔑 고급 시각화용 범용 데이터 필드 추가
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection(BaseModel):
    type: VisualizationType = VisualizationType.PARAGRAPH
    position: int = 0
    title: Optional[str] = None
    content: Optional[str] = None
    visualization_data: Optional[VisualizationData] = None


@dataclass
class Report(BaseModel):
    title: str = ""
    youtube_url: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    status: str = "processing"
    error_message: Optional[str] = None