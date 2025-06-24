# app/models/request_models.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any


class ProcessVideoRequest(BaseModel):
    """비디오 처리 요청 모델"""
    youtube_url: str
    options: Optional[Dict[str, Any]] = {}


