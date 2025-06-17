import requests
from config.settings import api_config
from utils.exceptions import CaptionError
from utils.error_handler import safe_execute


def _extract_caption_impl(youtube_url: str) -> str:
    """실제 자막 추출 로직 (내부용)"""
    response = requests.get(
        api_config.vidcap_api_url,  # 하드코딩 제거
        params={"url": youtube_url, "locale": "ko"},
        headers={"Authorization": f"Bearer {api_config.vidcap_api_key}"}
    )
    response.raise_for_status()

    content = response.json().get("data", {}).get("content", "")
    if not content:
        raise CaptionError("Caption content is empty", "extract_youtube_caption")

    return content


def extract_youtube_caption(youtube_url: str) -> str:
    """안전한 자막 추출 (에러 처리 포함)"""
    return safe_execute(
        _extract_caption_impl,
        youtube_url,
        context="extract_youtube_caption",
        default_return=""
    )