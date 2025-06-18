# app/services/claude_service.py (간단한 버전)
from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import ReportGenerationError
from utils.error_handler import safe_execute


class ClaudeService:
    def __init__(self):
        self.llm = create_llm()
        self._setup_prompts()

    def _setup_prompts(self):
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            너는 YouTube 영상 자막을 분석하여 구조화된 보고서를 작성하는 AI야.
            다음 형식으로 응답해야 해:

            제목: [간결한 제목]

            요약: [핵심 내용 요약]

            주요 내용:
            1. [첫 번째 포인트]
            2. [두 번째 포인트]
            3. [세 번째 포인트]

            결론: [마무리 정리]
            """),
            ("human", "{caption}")
        ])

    async def generate_report(self, caption: str) -> str:
        """보고서 텍스트 생성"""
        return safe_execute(
            self._generate_report_impl,
            caption,
            context="claude_service.generate_report",
            default_return=""
        )

    def _generate_report_impl(self, caption: str) -> str:
        if not caption:
            raise ReportGenerationError("Empty caption", "generate_report")

        messages = self.report_prompt.format_messages(caption=caption)
        response = self.llm.invoke(messages)

        if not response or not response.content:
            raise ReportGenerationError("Empty response", "generate_report")

        return response.content.strip()