from pydantic import BaseModel

class RunRequest(BaseModel):
    youtube_url: str