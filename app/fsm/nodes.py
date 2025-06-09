import json
from app.utils.caption import get_caption_from_vidcap
from app.utils.prompt import build_analysis_prompt
from app.fsm.types import ReportState
from app.agents.visual_agent import VisualAgent

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

def analyze_paragraphs(state: ReportState, agent: VisualAgent) -> ReportState:
    prompt = build_analysis_prompt(state["caption"])
    res = agent.agent.run(prompt)
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

def generate_visuals(state: ReportState, agent: VisualAgent) -> ReportState:
    for sec in state["sections"]:
        for p in sec["paragraphs"]:
            vt = p["visual_type"]
            prompt = p.get("visual_prompt", "")
            if vt in ["image", "chart", "table"]:
                visual = agent.create_visual(vt, prompt)
                if visual:
                    p["visual_url"] = getattr(visual, "url", None)
                    p["visual_data"] = getattr(visual, "data", None)
    return state

def finalize_report(state: ReportState) -> ReportState:
    return state

