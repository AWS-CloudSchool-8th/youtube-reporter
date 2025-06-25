import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv("VIDCAP_API_KEY")
    
    def extract_caption(self, youtube_url: str) -> str:
        """YouTube 자막 추출"""
        try:
            api_url = "https://vidcap.xyz/api/v1/youtube/caption"
            params = {"url": youtube_url, "locale": "ko"}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", {}).get("content", "")
        except Exception as e:
            logger.error(f"자막 추출 오류: {e}")
            return f"[자막 추출 실패: {str(e)}]"