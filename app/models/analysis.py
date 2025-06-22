from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class VideoInfo(BaseModel):
    """비디오 정보"""
    video_id: str = Field(..., description="비디오 ID")
    title: str = Field(..., description="제목")
    description: str = Field(..., description="설명")
    channel_title: str = Field(..., description="채널명")
    published_at: datetime = Field(..., description="게시일")
    view_count: int = Field(..., description="조회수")
    like_count: int = Field(..., description="좋아요 수")
    comment_count: int = Field(..., description="댓글 수")
    duration: str = Field(..., description="재생 시간")
    thumbnail_url: str = Field(..., description="썸네일 URL")

class SearchRequest(BaseModel):
    """검색 요청"""
    query: str = Field(..., description="검색어")
    max_results: int = Field(10, description="최대 결과 수")
    exclude_shorts: bool = Field(False, description="쇼츠 제외 여부")

class AnalysisRequest(BaseModel):
    """분석 요청 기본 모델"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")

class AnalysisResponse(BaseModel):
    """분석 응답 기본 모델"""
    id: str = Field(..., description="분석 ID")
    status: str = Field(..., description="분석 상태")
    analysis_results: Dict[str, Any] = Field(..., description="분석 결과")
    s3_info: Optional[Dict[str, str]] = Field(None, description="S3 저장 정보")
    audio_info: Optional[Dict[str, str]] = Field(None, description="음성 변환 정보")
    error: Optional[str] = Field(None, description="에러 메시지")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")

class YouTubeAnalysisRequest(AnalysisRequest):
    """YouTube 분석 요청"""
    video_id: str = Field(..., description="YouTube 비디오 ID")
    include_comments: bool = Field(True, description="댓글 분석 포함 여부")
    include_transcript: bool = Field(True, description="자막 분석 포함 여부")
    max_comments: int = Field(100, description="최대 댓글 수")

class DocumentAnalysisRequest(AnalysisRequest):
    """문서 분석 요청"""
    file_name: str = Field(..., description="파일 이름")
    file_type: str = Field(..., description="파일 타입")
    file_size: int = Field(..., description="파일 크기")

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