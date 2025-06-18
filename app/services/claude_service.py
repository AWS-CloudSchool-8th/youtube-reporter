# services/claude_service.py - 요약 품질 개선
from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import ReportGenerationError
from utils.error_handler import safe_execute


class ClaudeService:
    def __init__(self):
        self.llm = create_llm()
        self._setup_improved_prompts()

    def _setup_improved_prompts(self):
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 YouTube 영상 내용을 분석하여 구조화된 보고서를 작성하는 전문가입니다.

            📋 보고서 작성 원칙:
            1. 영상의 실제 내용만 사용하세요
            2. 제목 중복을 피하세요  
            3. 각 섹션은 명확히 구분하세요
            4. 구체적이고 유용한 정보를 포함하세요

            📝 보고서 구조:
            ```
            제목: [영상의 핵심 주제를 간결하게]

            요약: [영상의 핵심 메시지를 2-3문장으로]

            주요 내용:
            1. [첫 번째 핵심 포인트]
               - 세부사항 1
               - 세부사항 2
            2. [두 번째 핵심 포인트] 
               - 세부사항 1
               - 세부사항 2
            3. [세 번째 핵심 포인트]
               - 세부사항 1
               - 세부사항 2

            결론: [영상의 의의나 중요성을 1-2문장으로]
            ```

            ⚠️ 주의사항:
            - 제목을 본문에 반복하지 마세요
            - 각 섹션은 서로 다른 내용이어야 합니다
            - 구체적인 예시나 수치를 포함하세요
            - 학습자에게 도움되는 실용적 정보를 제공하세요
            """),
            ("human", "다음 YouTube 영상의 자막을 분석하여 위 형식에 맞는 보고서를 작성하세요:\n\n{caption}")
        ])

    async def generate_report(self, caption: str) -> str:
        """개선된 보고서 생성"""
        return safe_execute(
            self._generate_report_impl,
            caption,
            context="claude_service.generate_report",
            default_return=""
        )

    def _generate_report_impl(self, caption: str) -> str:
        if not caption:
            raise ReportGenerationError("Empty caption", "generate_report")

        # 자막 길이 제한 (너무 길면 품질 저하)
        limited_caption = caption[:3000] if len(caption) > 3000 else caption

        messages = self.report_prompt.format_messages(caption=limited_caption)
        response = self.llm.invoke(messages)

        if not response or not response.content:
            raise ReportGenerationError("Empty response", "generate_report")

        # 후처리: 제목 중복 제거
        content = response.content.strip()
        content = self._remove_title_duplication(content)

        return content

    def _remove_title_duplication(self, content: str) -> str:
        """제목 중복 제거"""
        lines = content.split('\n')
        cleaned_lines = []

        title_line = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 제목 라인 감지
            if line.startswith('제목:'):
                if title_line is None:  # 첫 번째 제목만 유지
                    title_line = line
                    cleaned_lines.append(line)
                # 두 번째 제목부터는 무시
                continue

            # 제목과 동일한 내용 제거
            if title_line:
                title_content = title_line.replace('제목:', '').strip()
                if title_content in line and len(line) < len(title_content) + 20:
                    continue  # 제목과 유사한 짧은 라인 제거

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)