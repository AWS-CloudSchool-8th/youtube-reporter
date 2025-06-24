# app/models/request.py - Pydantic v2 호환 버전
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

    # Pydantic v2에서는 Config 클래스 대신 model_config 사용
    model_config = {
        "json_schema_extra": {  # schema_extra → json_schema_extra
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "options": {
                    "include_timestamp": True,
                    "detailed_analysis": True
                }
            }
        }
    }