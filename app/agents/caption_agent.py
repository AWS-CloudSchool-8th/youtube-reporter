# app/agents/caption_agent.py
import requests
import os
from langchain_core.runnables import Runnable


class CaptionAgent(Runnable):
    def __init__(self):
        self.api_key = os.getenv("VIDCAP_API_KEY")
        self.api_url = "https://vidcap.xyz/api/v1/youtube/caption"

    def invoke(self, state: dict, config=None):
        youtube_url = state.get("youtube_url")

        try:
            response = requests.get(
                self.api_url,
                params={"url": youtube_url, "locale": "ko"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()

            caption = response.json().get("data", {}).get("content", "")
            if not caption:
                caption = "자막을 찾을 수 없습니다."

            return {**state, "caption": caption}

        except Exception as e:
            return {**state, "caption": f"자막 추출 실패: {str(e)}"}
