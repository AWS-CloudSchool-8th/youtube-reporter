# app/core/dependencies.py
from functools import lru_cache
from ..services.youtube_service import YouTubeService
from ..services.langgraph_service import LangGraphService


@lru_cache()
def get_youtube_service() -> YouTubeService:
    """YouTube 서비스 싱글톤 인스턴스 반환"""
    return YouTubeService()


@lru_cache()
def get_langgraph_service() -> LangGraphService:
    """LangGraph 서비스 싱글톤 인스턴스 반환"""
    return LangGraphService()