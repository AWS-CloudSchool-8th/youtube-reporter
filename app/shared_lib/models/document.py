from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentInfo(BaseModel):
    filename: str
    content_type: str
    size: int
    pages: Optional[int] = None
    word_count: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class DocumentAnalysisRequest(BaseModel):
    include_audio: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    status: str
    document_info: DocumentInfo
    analysis_result: Optional[Dict[str, Any]] = None
    s3_info: Optional[Dict[str, Any]] = None
    audio_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None 
