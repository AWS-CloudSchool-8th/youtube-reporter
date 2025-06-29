from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class YouTubeSearchRequest(BaseModel):
    """YouTube search request"""
    query: str = Field(..., description="Search keyword")
    max_results: int = Field(10, description="Maximum number of results")

class YouTubeVideoInfo(BaseModel):
    video_id: str = Field(..., description="Video ID")
    title: str = Field(..., description="Title")
    description: str = Field(..., description="Description")
    channel_title: str = Field(..., description="Channel name")
    published_at: datetime = Field(..., description="Published date")
    view_count: int = Field(..., description="View count")
    like_count: int = Field(..., description="Like count")
    comment_count: int = Field(..., description="Comment count")
    duration: str = Field(..., description="Duration")
    thumbnail_url: str = Field(..., description="Thumbnail URL")

class YouTubeSearchResponse(BaseModel):
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total number of results")
    videos: List[YouTubeVideoInfo] = Field(..., description="List of found videos")
    next_page_token: Optional[str] = Field(None, description="Next page token")

class YouTubeAnalysisRequest(BaseModel):
    video_id: str = Field(..., description="Video ID to analyze")
    include_comments: bool = Field(True, description="Whether to include comment analysis")
    include_transcript: bool = Field(True, description="Whether to include transcript analysis")
    max_comments: int = Field(100, description="Maximum number of comments to analyze")

class YouTubeAnalysisResponse(BaseModel):
    video_info: YouTubeVideoInfo = Field(..., description="Video metadata")
    analysis_results: Dict[str, Any] = Field(..., description="Analysis results")
    comments_analysis: Optional[Dict[str, Any]] = Field(None, description="Comment analysis")
    transcript_analysis: Optional[Dict[str, Any]] = Field(None, description="Transcript analysis")
    created_at: datetime = Field(..., description="Analysis start time")
    completed_at: datetime = Field(..., description="Analysis completion time")

