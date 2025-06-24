# app/core/dependencies.py
from typing import Optional
from fastapi import HTTPException
from ..core.config import settings
from ..services.youtube_service import YouTubeService
from ..services.langgraph_service import LangGraphService

# 싱글톤 서비스 인스턴스들
_youtube_service: Optional[YouTubeService] = None
_langgraph_service: Optional[LangGraphService] = None


def get_youtube_service() -> YouTubeService:
    """YouTube 서비스 의존성"""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service


def get_langgraph_service() -> LangGraphService:
    """LangGraph 서비스 의존성"""
    global _langgraph_service
    if _langgraph_service is None:
        _langgraph_service = LangGraphService()
    return _langgraph_service


def validate_youtube_url(url: str) -> str:
    """YouTube URL 검증"""
    import re

    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/embed/[\w-]+'
    ]

    if not any(re.match(pattern, url) for pattern in youtube_patterns):
        raise HTTPException(
            status_code=400,
            detail="올바른 YouTube URL 형식이 아닙니다."
        )

    return url