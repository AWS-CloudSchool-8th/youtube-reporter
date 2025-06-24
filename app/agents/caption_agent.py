# app/agents/caption_agent.py - 비동기 버전
import asyncio
import httpx
from typing import Dict, Any
from langchain_core.runnables import Runnable
from ..core.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CaptionAgent(Runnable):
    """YouTube 자막 추출 에이전트 (비동기)"""

    def __init__(self):
        self.api_key = settings.vidcap_api_key
        self.api_url = settings.vidcap_api_url

        # 비동기 HTTP 클라이언트 설정
        self.http_client = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 재사용을 위한 지연 초기화"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.http_client

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.http_client:
            await self.http_client.aclose()

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """동기 인터페이스 (호환성 유지)"""
        return asyncio.run(self.ainvoke(state, config))

    async def ainvoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """비동기 자막 추출 실행"""
        youtube_url = state.get("youtube_url")

        if not youtube_url:
            return {**state, "caption": "YouTube URL이 제공되지 않았습니다."}

        try:
            logger.info(f"🎬 자막 추출 시작: {youtube_url}")

            client = await self._get_http_client()

            response = await client.get(
                self.api_url,
                params={"url": youtube_url, "locale": "ko"}
            )
            response.raise_for_status()

            data = response.json()
            caption = data.get("data", {}).get("content", "")

            if not caption:
                logger.warning("자막을 찾을 수 없습니다.")
                return {**state, "caption": "자막을 찾을 수 없습니다."}

            logger.info(f"✅ 자막 추출 완료: {len(caption)}자")
            return {**state, "caption": caption}

        except httpx.TimeoutException:
            error_msg = "자막 추출 시간 초과"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

        except httpx.HTTPStatusError as e:
            error_msg = f"자막 추출 API 오류: HTTP {e.response.status_code}"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

        except httpx.RequestError as e:
            error_msg = f"자막 추출 네트워크 오류: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

        except Exception as e:
            error_msg = f"자막 추출 예상치 못한 오류: {str(e)}"
            logger.error(error_msg)
            return {**state, "caption": f"[오류] {error_msg}"}

    async def close(self):
        """리소스 정리"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None