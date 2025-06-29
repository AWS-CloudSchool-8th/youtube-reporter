from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class VideoInfo(BaseModel):
    """Video information"""
    video_id: str = Field(..., description="Video ID")
    title: str = Field(..., description="Title")
    description: str = Field(..., description="Description")
    channel_title: str = Field(..., description="Channel name")
    published_at: datetime = Field(..., description="Published date")
    view_count: int = Field(..., description="View count")
    like_count: int = Field(..., description="Like count")
    comment_count: int = Field(..., description="Comment count")
    duration: str = Field(..., description="Playback duration")
    thumbnail_url: str = Field(..., description="Thumbnail URL")

class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., description="Search keyword")
    max_results: int = Field(10, description="Maximum number of results")
    exclude_shorts: bool = Field(False, description="Exclude YouTube Shorts")

class AnalysisRequest(BaseModel):
    """Base analysis request"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AnalysisResponse(BaseModel):
    """Base analysis response"""
    id: str = Field(..., description="Analysis ID")
    status: str = Field(..., description="Analysis status")
    analysis_results: Dict[str, Any] = Field(..., description="Analysis results")
    s3_info: Optional[Dict[str, str]] = Field(None, description="S3 storage info")
    audio_info: Optional[Dict[str, str]] = Field(None, description="Audio conversion info")
    error: Optional[str] = Field(None, description="Error message")
    created_at: datetime = Field(..., description="Creation time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")

class YouTubeAnalysisRequest(AnalysisRequest):
    """YouTube analysis request"""
    video_id: str = Field(..., description="YouTube video ID")
    include_comments: bool = Field(True, description="Include comment analysis")
    include_transcript: bool = Field(True, description="Include transcript analysis")
    max_comments: int = Field(100, description="Maximum number of comments")

class DocumentAnalysisRequest(AnalysisRequest):
    """Document analysis request"""
    file_name: str = Field(..., description="File name")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., description="File size")

class AnalysisState(BaseModel):
    input_type: str
    source_data: Any
    extracted_content: Optional[str] = None
    structured_report: Optional[str] = None
    visual_candidates: Optional[List[Dict[str, Any]]] = None
    visual_assets: Optional[List[Dict[str, Any]]] = None
    final_output: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    s3_info: Optional[Dict[str, Any]] = None
    audio_info: Optional[Dict[str, Any]] = None

