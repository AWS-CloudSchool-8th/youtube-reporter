import os
import requests
from dotenv import load_dotenv
from langchain.agents import Tool

load_dotenv()

VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === 1. 일반 함수 정의 ===

def extract_youtube_caption_tool(youtube_url: str) -> str:
    """
    Use this function to extract Korean subtitles from a YouTube video
    using the Vidcap.xyz API. It returns the full Korean transcript as plain text.
    """
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": "ko"}
    headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
    response = requests.get(api_url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("content", "")

def structure_report(caption: str) -> str:
    return (
        "당신은 유튜브 자막을 체계적인 보고서로 재작성하는 AI입니다.\n\n"
        "다음 규칙을 반드시 따르세요:\n"
        "1. 원문 자막은 그대로 복사하지 말고, 완전히 서술형 보고서로 바꿔주세요.\n"
        "2. 전체 내용을 주제별로 나누어 3개 이상의 문단으로 정리하세요.\n"
        "3. 각 문단의 첫 문장은 핵심 요약, 이후에는 상세 설명을 자연스럽게 이어주세요.\n"
        "4. 최소 300~500자 이상의 충분한 분량을 확보해주세요.\n"
        "5. 가능한 한 예시나 배경 설명을 추가하여 읽기 쉽게 구성해주세요.\n\n"
        f"다음은 자막 내용입니다:\n\n{caption}"
    )

    
def generate_visuals(prompt: str) -> str:
    """
    Generates a simple visual (chart or diagram) using DALL·E 3
    based on the given sentence or prompt. Returns the image URL.
    """
    dalle_api = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": (
            "Create a simple and clear visual such as a chart or diagram "
            f"based on this sentence:\n\n{prompt}"
        ),
        "n": 1,
        "size": "1024x1024"
    }
    response = requests.post(dalle_api, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [{}])[0].get("url", "[Image generation failed]")

def parse_report_to_json(content: str) -> dict:
    """
    Parses a Korean report into a JSON structure for frontend rendering.
    Wraps the report into a basic section-paragraph JSON format.
    """
    return {
        # "report": content,
        "format": "json",
        "sections": [
            {"type": "paragraph", "content": content}
        ]
    }

# === 2. LangChain Tool 객체 변환 ===

caption_tool = Tool.from_function(
    func=extract_youtube_caption_tool,
    name="ExtractCaption",
    description=(
        "Use this tool to extract Korean captions from a YouTube video. "
        "Returns the full subtitle text. The tool will access the vidcap.xyz API."
    )
)

report_tool = Tool.from_function(
    func=structure_report,
    name="StructureReport",
    description=(
        "Use this tool ONLY IF you want to transform a spoken Korean transcript into a formal written report. "
        "You MUST provide the full transcript text as input. "
        "The output will be in fluent Korean in paragraph format. "
        "Do NOT summarize or skip sentences. This tool calls a built-in LLM function."
    )
)

visual_tool = Tool.from_function(
    func=generate_visuals,
    name="GenerateVisuals",
    description=(
        "Use this tool to create a visual (chart, graph, diagram) based on a sentence. "
        "Returns an image URL from DALL·E 3."
    )
)

parse_tool = Tool.from_function(
    func=parse_report_to_json,
    name="ParseToJson",
    description=(
        "Use this tool to convert a final report into structured JSON for frontend rendering. "
        "Do not generate JSON yourself. This tool handles it automatically. Input should be a full paragraph text."
    )
)

# === Export ===

tools = [caption_tool, report_tool, visual_tool, parse_tool]
__all__ = ["tools", "caption_tool", "report_tool", "visual_tool", "parse_tool"]
