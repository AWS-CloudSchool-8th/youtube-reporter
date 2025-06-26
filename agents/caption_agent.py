# app/agents/caption_agent.py
import requests
from langchain_core.runnables import Runnable
from app.core.config import settings
from app.services.state_manager import state_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaptionAgent(Runnable):
    def __init__(self):
        self.api_key = settings.VIDCAP_API_KEY
        self.api_url = "https://vidcap.xyz/api/v1/youtube/caption"

    def invoke(self, state: dict, config=None):
        youtube_url = state.get("youtube_url")
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info(f"🎬 자막 추출 시작: {youtube_url}")

        # 진행률 업데이트
        if job_id:
            try:
                state_manager.update_progress(job_id, 20, "📝 자막 추출 중...")
            except Exception as e:
                logger.warning(f"진행률 업데이트 실패 (무시됨): {e}")

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

            logger.info(f"✅ 자막 추출 완료: {len(caption)}자")
            return {**state, "caption": caption}

        except Exception as e:
            error_msg = f"자막 추출 실패: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": error_msg}