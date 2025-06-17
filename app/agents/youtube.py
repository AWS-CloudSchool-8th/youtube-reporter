import os
import requests

def extract_youtube_caption(youtube_url: str) -> str:
    try:
        response = requests.get(
            "https://vidcap.xyz/api/v1/youtube/caption",
            params={"url": youtube_url, "locale": "ko"},
            headers={"Authorization": f"Bearer {os.getenv('VIDCAP_API_KEY')}"}
        )
        response.raise_for_status()
        return response.json().get("data", {}).get("content", "")
    except Exception as e:
        return f"[Error fetching caption: {e}]"