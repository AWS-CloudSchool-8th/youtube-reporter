# services/claude_service.py (수정됨)
from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import ReportGenerationError
from utils.error_handler import safe_execute
import json
from typing import List, Dict


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

        # 시각화 데이터 추출용 프롬프트 (차트 생성 강화)
        self.visualization_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            다음 보고서 텍스트를 분석하여 시각화 가능한 부분을 찾아주세요.

            반드시 다음 JSON 형식으로만 응답하세요:
            [
              {
                "type": "paragraph",
                "title": "요약",
                "content": "텍스트 내용...",
                "position": 0
              },
              {
                "type": "bar_chart",
                "title": "해결 단계별 진행도",
                "data": {
                  "labels": ["문제 분석", "방법 탐색", "작도 실행", "계산 완료"],
                  "datasets": [{
                    "label": "진행률",
                    "data": [100, 80, 90, 100],
                    "backgroundColor": "#6366f1",
                    "borderColor": "#4f46e5",
                    "borderWidth": 2
                  }]
                },
                "position": 1
              },
              {
                "type": "paragraph",
                "title": "주요 내용",
                "content": "텍스트 내용...",
                "position": 2
              },
              {
                "type": "pie_chart",
                "title": "기하학적 요소 비중",
                "data": {
                  "labels": ["달물선 작도", "닮음비 계산", "접점 연결", "기타"],
                  "datasets": [{
                    "data": [40, 30, 20, 10],
                    "backgroundColor": ["#6366f1", "#ec4899", "#10b981", "#f59e0b"],
                    "borderWidth": 2
                  }]
                },
                "position": 3
              }
            ]

            중요: 
            - 텍스트 내용에 맞는 의미있는 차트 데이터 생성
            - paragraph와 차트를 섞어서 구성
            - Chart.js 형식에 맞는 data 구조 사용
            - 설명 없이 JSON만 출력
            """),
            ("human", "{report_text}")
        ])

    async def generate_report(self, caption: str) -> str:
        """보고서 텍스트 생성"""
        return safe_execute(
            self._generate_report_impl,
            caption,
            context="claude_service.generate_report",
            default_return=""
        )

    async def extract_visualizations(self, report_text: str) -> List[Dict]:
        """보고서에서 시각화 데이터 추출"""
        return safe_execute(
            self._extract_visualizations_impl,
            report_text,
            context="claude_service.extract_visualizations",
            default_return=[]
        )

    def _generate_report_impl(self, caption: str) -> str:
        if not caption:
            raise ReportGenerationError("Empty caption", "generate_report")

        messages = self.report_prompt.format_messages(caption=caption)
        response = self.llm.invoke(messages)

        if not response or not response.content:
            raise ReportGenerationError("Empty response", "generate_report")

        return response.content.strip()

    def _extract_visualizations_impl(self, report_text: str) -> List[Dict]:
        if not report_text:
            print("⚠️ 빈 보고서 텍스트")
            return self._create_fallback_sections(report_text)

        try:
            print(f"🔍 Claude에게 시각화 추출 요청...")
            messages = self.visualization_prompt.format_messages(report_text=report_text)
            response = self.llm.invoke(messages)

            if not response or not response.content:
                print("⚠️ Claude 응답이 비어있음")
                return self._create_fallback_sections(report_text)

            content = response.content.strip()
            print(f"📝 Claude 응답: {content[:200]}...")

            # JSON 파싱 시도
            parsed_data = self._parse_json_response(content)

            if parsed_data and isinstance(parsed_data, list):
                print(f"✅ {len(parsed_data)}개 섹션 추출 성공")
                return self._validate_sections(parsed_data)
            else:
                print("⚠️ 파싱된 데이터가 리스트가 아님")
                return self._create_fallback_sections(report_text)

        except Exception as e:
            print(f"❌ 시각화 추출 실패: {e}")
            return self._create_fallback_sections(report_text)

    def _parse_json_response(self, content: str) -> List[Dict]:
        """JSON 응답 파싱"""
        try:
            # JSON 마커 제거
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1])

            # JSON 파싱
            parsed = json.loads(content)
            return parsed if isinstance(parsed, list) else []

        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            print(f"파싱 시도 내용: {content[:500]}...")
            return []

    def _validate_sections(self, sections: List[Dict]) -> List[Dict]:
        """섹션 데이터 검증 및 정리"""
        validated = []

        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                print(f"⚠️ 섹션 {i}가 딕셔너리가 아님: {type(section)}")
                continue

            # 필수 필드 확인 및 기본값 설정
            clean_section = {
                "type": str(section.get("type", "paragraph")),
                "title": str(section.get("title", f"섹션 {i + 1}")),
                "content": str(section.get("content", "")),
                "position": int(section.get("position", i))
            }

            # 차트 데이터가 있다면 추가
            if "data" in section and isinstance(section["data"], dict):
                clean_section["data"] = section["data"]

            validated.append(clean_section)

        return validated

    def _create_fallback_sections(self, report_text: str) -> List[Dict]:
        """실패시 기본 섹션 생성"""
        if not report_text:
            return [{
                "type": "paragraph",
                "title": "오류",
                "content": "보고서 생성에 실패했습니다.",
                "position": 0
            }]

        # 보고서를 문단별로 나누기
        paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]
        sections = []

        for i, paragraph in enumerate(paragraphs[:5]):  # 최대 5개 문단
            # 제목 추출 시도
            lines = paragraph.split('\n')
            title = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]

            sections.append({
                "type": "paragraph",
                "title": title,
                "content": paragraph,
                "position": i
            })

        print(f"📄 폴백으로 {len(sections)}개 문단 생성")
        return sections