from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class YouTubeSearchRequest(BaseModel):
    """YouTube 검색 요청"""
    query: str = Field(..., description="검색어")
    max_results: int = Field(10, description="최대 결과 수")

class YouTubeVideoInfo(BaseModel):
    video_id: str = Field(..., description="비디오 ID")
    title: str = Field(..., description="비디오 제목")
    description: str = Field(..., description="비디오 설명")
    channel_title: str = Field(..., description="채널 제목")
    published_at: datetime = Field(..., description="게시일")
    view_count: int = Field(..., description="조회수")
    like_count: int = Field(..., description="좋아요 수")
    comment_count: int = Field(..., description="댓글 수")
    duration: str = Field(..., description="재생 시간")
    thumbnail_url: str = Field(..., description="썸네일 URL")

class YouTubeSearchResponse(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    total_results: int = Field(..., description="전체 검색 결과 수")
    videos: List[YouTubeVideoInfo] = Field(..., description="검색된 비디오 목록")
    next_page_token: Optional[str] = Field(None, description="다음 페이지 토큰")

class YouTubeAnalysisRequest(BaseModel):
    video_id: str = Field(..., description="분석할 비디오 ID")
    include_comments: bool = Field(True, description="댓글 분석 포함 여부")
    include_transcript: bool = Field(True, description="자막 분석 포함 여부")
    max_comments: int = Field(100, description="분석할 최대 댓글 수")

class YouTubeAnalysisResponse(BaseModel):
    video_info: YouTubeVideoInfo = Field(..., description="비디오 정보")
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")
    comments_analysis: Optional[Dict[str, Any]] = Field(None, description="댓글 분석 결과")
    transcript_analysis: Optional[Dict[str, Any]] = Field(None, description="자막 분석 결과")
    created_at: datetime = Field(..., description="분석 시작 시간")
    completed_at: datetime = Field(..., description="분석 완료 시간") 
