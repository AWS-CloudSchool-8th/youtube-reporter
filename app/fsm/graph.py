from uuid import uuid4
from app.utils.caption import extract_video_id

def generate_report_from_url(youtube_url: str):
    from app.fsm.graph import get_graph  # ❗️import를 함수 내부로 옮김

    vid = extract_video_id(youtube_url)
    thread = str(uuid4())

    with get_graph() as graph:
        state = graph.invoke(
            {"video_id": vid},
            config={"configurable": {"thread_id": thread}}
        )

    return {
        "title": "유튜브 자동 요약 리포트",
        "videoId": vid,
        "sections": state["sections"]
    }

