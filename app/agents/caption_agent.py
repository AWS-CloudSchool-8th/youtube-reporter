# app/agents/caption_agent.py
import requests
from typing import Dict, Any
from langchain_core.runnables import Runnable
from ..core.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CaptionAgent(Runnable):
    """YouTube 자막 추출 에이전트"""

    def __init__(self):
        self.api_key = settings.vidcap_api_key
        self.api_url = settings.vidcap_api_url

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """자막 추출 실행"""
        youtube_url = state.get("youtube_url")

        if not youtube_url:
            return {**state, "caption": "YouTube URL이 제공되지 않았습니다."}

        try:
            logger.info(f"🎬 자막 추출 시작: {youtube_url}")

            response = requests.get(
                self.api_url,
                params={"url": youtube_url, "locale": "ko"},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            caption = data.get("data", {}).get("content", "")

            if not caption:
                logger.warning("자막을 찾을 수 없습니다.")
                return {**state, "caption": "자막을 찾을 수 없습니다."}

            logger.info(f"✅ 자막 추출 완료: {len(caption)}자")
            return {**state, "caption": caption}

        except requests.exceptions.Timeout:
            error_msg = "자막 추출 시간 초과"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

        except requests.exceptions.RequestException as e:
            error_msg = f"자막 추출 API 오류: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

        except Exception as e:
            error_msg = f"자막 추출 예상치 못한 오류: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}