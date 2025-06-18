# services/youtube_service.py
import requests
from config.settings import api_config
from utils.exceptions import CaptionError
from utils.error_handler import safe_execute


class YouTubeService:
    def __init__(self):
        self.api_key = api_config.vidcap_api_key
        self.api_url = api_config.vidcap_api_url

    async def extract_caption(self, youtube_url: str) -> str:
        """YouTube 자막 추출"""
        return safe_execute(
            self._extract_caption_impl,
            youtube_url,
            context="youtube_service.extract_caption",
            default_return=""
        )

    def _extract_caption_impl(self, youtube_url: str) -> str:
        response = requests.get(
            self.api_url,
            params={"url": youtube_url, "locale": "ko"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()

        content = response.json().get("data", {}).get("content", "")
        if not content:
            raise CaptionError("Caption content is empty", "extract_caption")

        return content