from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import ReportGenerationError
from utils.error_handler import safe_execute

# LLM 인스턴스는 함수 호출 시 생성
llm = create_llm()

structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 유튜브 영상 자막을 바탕으로 명확하고 논리적인 보고서를 작성하는 AI야. 자막은 대화체일 수 있으니 이를 잘 정제하고 요약해서 보고서 형식으로 바꿔야 해. 보고서는 다음 구조를 따라야 해:

1. 제목 (Title)
2. 요약 (Summary)
3. 주요 내용 정리 (Key Points) - 항목별로 정리
4. 결론 (Conclusion)

가능하다면 자막의 흐름에 따라 논리적 전개가 자연스럽게 되도록 구성해. 친절하고 간결한 어조를 유지하되, 정보는 정확하게 전달해."""),
    ("human", "{input}")
])


def _generate_report_impl(caption: str) -> str:
    """실제 보고서 생성 로직 (내부용)"""
    if not caption or caption.startswith("[Error"):
        raise ReportGenerationError("Invalid caption input", "generate_report")

    messages = structure_prompt.format_messages(input=caption)
    response = llm.invoke(messages)

    if not response or not response.content:
        raise ReportGenerationError("Empty response from LLM", "generate_report")

    return response.content.strip()


def generate_report(caption: str) -> str:
    """안전한 보고서 생성 (에러 처리 포함)"""
    return safe_execute(
        _generate_report_impl,
        caption,
        context="generate_report",
        default_return=""
    )