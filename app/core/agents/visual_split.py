from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import VisualSplitError
from utils.error_handler import safe_execute
import json

# LLM 인스턴스는 함수 호출 시 생성
llm = create_llm()

split_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 보고서를 분석해 각 문단을 시각화 가능한 정보 블록으로 나누는 역할을 해. 각 블록은 다음 형식을 따라야 해:

[
  {{
    "type": "bar_chart | line_chart | pie_chart | timeline | text | image",
    "text": "시각화할 내용에 대한 설명",
    "title": "블록 제목 (선택사항)",
    "data": "필요한 경우 시각화에 사용될 데이터 설명"
  }},
  ...
]

중요한 점:
- "type" 필드는 필수이며, 적절한 시각화 타입을 선택해야 함
- "text" 필드는 시각화 생성에 사용될 설명문
- 숫자 데이터가 있으면 "bar_chart", "line_chart", "pie_chart" 중 선택
- 시간 순서가 있으면 "timeline"
- 개념 설명이나 일반 텍스트는 "text"
- 이미지가 필요한 내용은 "image"

문단 내용을 바탕으로 적절한 시각화 타입을 판단하고, "text" 필드에 시각화 생성에 필요한 명확한 설명을 포함해.

반드시 유효한 JSON 배열 형태로만 응답해야 합니다.
"""),
    ("human", "{input}")
])


def _extract_visual_blocks_impl(text: str) -> list:
    """실제 시각화 블록 추출 로직 (내부용)"""
    if not text or text.startswith("[Error"):
        raise VisualSplitError("Invalid text input", "extract_visual_blocks")

    result = llm.invoke(split_prompt.format_messages(input=text))

    if not result or not result.content:
        raise VisualSplitError("Empty response from LLM", "extract_visual_blocks")

    try:
        # JSON 파싱 전에 내용 정리
        content = result.content.strip()

        # 코드 블록 마커 제거 (```json ... ``` 형태)
        if content.startswith("```"):
            lines = content.split('\n')
            if len(lines) > 2:
                content = '\n'.join(lines[1:-1])

        parsed = json.loads(content)
        if not isinstance(parsed, list):
            raise VisualSplitError("Response is not a list", "extract_visual_blocks")

        # 데이터 형식 검증 및 정리
        cleaned_blocks = []
        for i, block in enumerate(parsed):
            if not isinstance(block, dict):
                continue

            # 필수 필드 확인 및 기본값 설정
            cleaned_block = {
                "type": block.get("type", "text"),
                "text": block.get("text", block.get("title", f"Block {i + 1}"))
            }

            # 선택적 필드 추가
            if "title" in block:
                cleaned_block["title"] = block["title"]
            if "data" in block:
                cleaned_block["data"] = block["data"]

            cleaned_blocks.append(cleaned_block)

        return cleaned_blocks

    except json.JSONDecodeError as e:
        # JSON 파싱 실패 시 디버깅 정보 포함
        raise VisualSplitError(f"JSON parsing failed: {e}. Content: {content[:200]}...", "extract_visual_blocks")


def extract_visual_blocks(text: str) -> list:
    """안전한 시각화 블록 추출 (에러 처리 포함)"""
    return safe_execute(
        _extract_visual_blocks_impl,
        text,
        context="extract_visual_blocks",
        default_return=[]
    )