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
  {
    "title": "블록 제목",
    "summary": "핵심 내용 요약",
    "visual_type": "bar_chart | line_chart | pie_chart | timeline | text | image",
    "data": { 필요한 경우 시각화에 사용될 데이터 (예: 숫자 목록, 시간별 값 등) }
  },
  ...
]

문단 내용을 바탕으로 적절한 시각화 타입을 판단하고, 가능하면 데이터도 함께 구성해. 시각화가 어려운 문단은 'text' 타입으로 처리해.
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
        parsed = json.loads(result.content)
        if not isinstance(parsed, list):
            raise VisualSplitError("Response is not a list", "extract_visual_blocks")
        return parsed
    except json.JSONDecodeError as e:
        raise VisualSplitError(f"JSON parsing failed: {e}", "extract_visual_blocks")


def extract_visual_blocks(text: str) -> list:
    """안전한 시각화 블록 추출 (에러 처리 포함)"""
    return safe_execute(
        _extract_visual_blocks_impl,
        text,
        context="extract_visual_blocks",
        default_return=[]
    )