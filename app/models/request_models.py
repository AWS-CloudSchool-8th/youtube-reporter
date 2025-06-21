# app/models/request_models.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, Literal

class ProcessVideoRequest(BaseModel):
    youtube_url: HttpUrl
    summary_level: Optional[Literal["simple", "detailed", "expert"]] = "detailed"
    options: Optional[Dict[str, Any]] = {}

