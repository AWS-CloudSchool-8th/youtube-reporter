import requests
from app.config import VIDCAP_API_KEY

def extract_video_id(youtube_url: str) -> str:
    return youtube_url.split("v=")[-1].split("&")[0]

def get_caption_from_vidcap(youtube_url: str, locale="ko") -> str:
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": locale}
    headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
    resp = requests.get(api_url, params=params, headers=headers)
    resp.raise_for_status()
    text = resp.json().get("data",{}).get("content","")
    if not text.strip():
        raise ValueError("자막이 비어 있습니다.")
    return text