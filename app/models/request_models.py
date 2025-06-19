# app/models/request_models.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any

class ProcessVideoRequest(BaseModel):
    youtube_url: HttpUrl
    options: Optional[Dict[str, Any]] = {}

