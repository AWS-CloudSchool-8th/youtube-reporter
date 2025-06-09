import json
from app.utils.caption import get_caption_from_vidcap
from app.utils.prompt import build_analysis_prompt
from app.utils.image import generate_image
from app.utils.chart import generate_chart
from app.utils.s3 import upload_bytes
from app.agents.visual_agent import agent
from app.fsm.types import ReportState

def try_parse_table(prompt: str):
    try:
        return json.loads(prompt)
    except (json.JSONDecodeError, TypeError):
        return None

def extract_caption(state: ReportState, youtube_url: str) -> ReportState:
    cap = get_caption_from_vidcap(youtube_url)
    state["caption"] = cap
    state["retry_count"] = 0
    return state

def analyze_paragraphs(state: ReportState) -> ReportState:
    prompt = build_analysis_prompt(state["caption"])
    res = agent.run(prompt)
    try:
        arr = json.loads(res)
    except json.JSONDecodeError:
        raise ValueError("Claude 응답이 JSON 형식이 아닙니다.")

    structured_sections = []
    for sec in arr:
        paragraphs = []
        for p in sec.get("paragraphs", []):
            visual_type = p.get("visual_type", "none")
            visual_prompt = p.get("visual_prompt", "")
            visual_data = try_parse_table(visual_prompt) if visual_type == "table" else None
            paragraphs.append({
                "text": p.get("text", ""),
                "visual_type": visual_type,
                "visual_prompt": visual_prompt,
                "visual_url": None,
                "visual_data": visual_data
            })
        structured_sections.append({
            "heading": sec.get("heading", "제목 없음"),
            "paragraphs": paragraphs
        })

    state["sections"] = structured_sections
    return state

def generate_visuals(state: ReportState) -> ReportState:
    for sec in state["sections"]:
        for p in sec["paragraphs"]:
            vt = p["visual_type"]
            prompt = p.get("visual_prompt", "")
            if vt == "image":
                p["visual_url"] = generate_image(prompt)
            elif vt == "chart":
                # 진짜 데이터를 Claude에서 받을 수도 있음
                x = ["A", "B", "C"]
                y = [10, 20, 15]
                p["visual_url"] = generate_chart(x, y, prompt)
            # table은 visual_data에 이미 들어있음
    return state

def finalize_report(state: ReportState) -> ReportState:
    return state