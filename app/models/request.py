# app/models/request.py
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, Dict, Any


class ProcessVideoRequest(BaseModel):
    """YouTube 영상 처리 요청 모델"""
    youtube_url: HttpUrl
    options: Optional[Dict[str, Any]] = {}

    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        """YouTube URL 형식 검증"""
        url_str = str(v)
        if not ('youtube.com' in url_str or 'youtu.be' in url_str):
            raise ValueError('올바른 YouTube URL이 아닙니다.')
        return v

    class Config:
        schema_extra = {
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "options": {
                    "include_timestamp": True,
                    "detailed_analysis": True
                }
            }
        }