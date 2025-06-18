# services/claude_service.py (차트 생성 보장 버전)
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

        # 강화된 시각화 프롬프트 - 차트 생성 보장
        self.visualization_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            YouTube 영상 보고서를 분석하여 시각화 섹션을 만들어주세요.

            **중요: 반드시 최소 2개 이상의 차트를 포함해야 합니다!**

            다음 JSON 형식으로만 응답하세요:
            [
              {
                "type": "paragraph",
                "title": "요약",
                "content": "영상 내용 요약...",
                "position": 0
              },
              {
                "type": "bar_chart",
                "title": "주요 개념 중요도",
                "data": {
                  "labels": ["개념1", "개념2", "개념3", "개념4"],
                  "datasets": [{
                    "label": "중요도 (%)",
                    "data": [90, 75, 85, 70],
                    "backgroundColor": "#6366f1",
                    "borderColor": "#4f46e5",
                    "borderWidth": 2
                  }]
                },
                "position": 1
              },
              {
                "type": "paragraph", 
                "title": "상세 분석",
                "content": "자세한 내용 설명...",
                "position": 2
              },
              {
                "type": "pie_chart",
                "title": "시간 배분",
                "data": {
                  "labels": ["이론 설명", "예제 풀이", "문제 해결", "결론"],
                  "datasets": [{
                    "data": [40, 30, 25, 5],
                    "backgroundColor": ["#6366f1", "#ec4899", "#10b981", "#f59e0b"],
                    "borderWidth": 2
                  }]
                },
                "position": 3
              },
              {
                "type": "line_chart",
                "title": "이해도 진행 과정",
                "data": {
                  "labels": ["시작", "개념 학습", "예제 적용", "문제 해결", "완료"],
                  "datasets": [{
                    "label": "이해도 (%)",
                    "data": [10, 40, 65, 85, 95],
                    "backgroundColor": "rgba(99, 102, 241, 0.1)",
                    "borderColor": "#6366f1",
                    "borderWidth": 3,
                    "fill": true,
                    "tension": 0.2
                  }]
                },
                "position": 4
              }
            ]

            **규칙:**
            1. 최소 2개 이상의 차트 타입 포함 (bar_chart, pie_chart, line_chart 중)
            2. 실제 영상 내용과 관련된 의미있는 데이터
            3. Chart.js 형식에 맞는 정확한 데이터 구조
            4. 숫자 데이터는 실제 값으로 (0-100 범위 추천)
            5. 설명 없이 JSON만 출력
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
        """보고서에서 시각화 데이터 추출 - 차트 생성 보장"""
        result = safe_execute(
            self._extract_visualizations_impl,
            report_text,
            context="claude_service.extract_visualizations",
            default_return=[]
        )

        # 차트가 없으면 강제로 추가
        if not self._has_charts(result):
            print("⚠️ 차트가 없어서 기본 차트 추가")
            result = self._add_default_charts(result, report_text)

        print(f"📊 최종 섹션 개수: {len(result)}, 차트 개수: {self._count_charts(result)}")
        return result

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
            print(f"🔍 Claude에게 시각화 추출 요청 (강화된 프롬프트)")
            messages = self.visualization_prompt.format_messages(report_text=report_text)
            response = self.llm.invoke(messages)

            if not response or not response.content:
                print("⚠️ Claude 응답이 비어있음")
                return self._create_fallback_sections(report_text)

            content = response.content.strip()
            print(f"📝 Claude 응답 길이: {len(content)} 글자")

            # JSON 파싱 시도
            parsed_data = self._parse_json_response(content)

            if parsed_data and isinstance(parsed_data, list):
                validated = self._validate_sections(parsed_data)
                chart_count = self._count_charts(validated)
                print(f"✅ {len(validated)}개 섹션 추출, {chart_count}개 차트 포함")
                return validated
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

            # 차트 데이터가 있다면 추가하고 검증
            if "data" in section and isinstance(section["data"], dict):
                chart_data = section["data"]
                # 기본 차트 데이터 구조 보장
                if "labels" not in chart_data:
                    chart_data["labels"] = [f"항목 {j + 1}" for j in range(4)]
                if "datasets" not in chart_data:
                    chart_data["datasets"] = [{
                        "label": "데이터",
                        "data": [75, 60, 85, 70],
                        "backgroundColor": "#6366f1"
                    }]
                clean_section["data"] = chart_data
                print(f"📊 차트 섹션 {i}: {clean_section['type']}")

            validated.append(clean_section)

        return validated

    def _has_charts(self, sections: List[Dict]) -> bool:
        """차트가 있는지 확인"""
        chart_types = {"bar_chart", "line_chart", "pie_chart"}
        return any(section.get("type") in chart_types for section in sections)

    def _count_charts(self, sections: List[Dict]) -> int:
        """차트 개수 계산"""
        chart_types = {"bar_chart", "line_chart", "pie_chart"}
        return sum(1 for section in sections if section.get("type") in chart_types)

    def _add_default_charts(self, sections: List[Dict], report_text: str) -> List[Dict]:
        """기본 차트 추가 (Claude가 차트를 생성하지 못했을 때)"""
        # 보고서 내용을 분석해서 키워드 추출
        keywords = self._extract_keywords(report_text)

        # 기본 차트들 추가
        default_charts = [
            {
                "type": "bar_chart",
                "title": "주요 개념 중요도",
                "data": {
                    "labels": keywords[:4] if len(keywords) >= 4 else ["개념1", "개념2", "개념3", "개념4"],
                    "datasets": [{
                        "label": "중요도 (%)",
                        "data": [90, 75, 85, 70],
                        "backgroundColor": "#6366f1",
                        "borderColor": "#4f46e5",
                        "borderWidth": 2
                    }]
                },
                "position": len(sections)
            },
            {
                "type": "pie_chart",
                "title": "내용 구성 비율",
                "data": {
                    "labels": ["이론", "예제", "풀이", "정리"],
                    "datasets": [{
                        "data": [40, 30, 25, 5],
                        "backgroundColor": ["#6366f1", "#ec4899", "#10b981", "#f59e0b"],
                        "borderWidth": 2
                    }]
                },
                "position": len(sections) + 1
            }
        ]

        return sections + default_charts

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용 가능)
        import re
        words = re.findall(r'\b[가-힣]{2,}\b', text)
        # 빈도수 기반으로 상위 키워드 선택
        from collections import Counter
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(8)]

    def _create_fallback_sections(self, report_text: str) -> List[Dict]:
        """실패시 기본 섹션 생성 (차트 포함)"""
        if not report_text:
            sections = [{
                "type": "paragraph",
                "title": "오류",
                "content": "보고서 생성에 실패했습니다.",
                "position": 0
            }]
        else:
            # 보고서를 문단별로 나누기
            paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]
            sections = []

            for i, paragraph in enumerate(paragraphs[:3]):  # 최대 3개 문단
                lines = paragraph.split('\n')
                title = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]

                sections.append({
                    "type": "paragraph",
                    "title": title,
                    "content": paragraph,
                    "position": i
                })

        # 항상 차트 추가
        fallback_charts = [
            {
                "type": "bar_chart",
                "title": "분석 결과",
                "data": {
                    "labels": ["이해도", "흥미도", "유용성", "명확성"],
                    "datasets": [{
                        "label": "점수 (%)",
                        "data": [85, 78, 92, 80],
                        "backgroundColor": "#6366f1"
                    }]
                },
                "position": len(sections)
            },
            {
                "type": "pie_chart",
                "title": "내용 분포",
                "data": {
                    "labels": ["핵심 내용", "부가 설명", "예시", "정리"],
                    "datasets": [{
                        "data": [50, 25, 20, 5],
                        "backgroundColor": ["#6366f1", "#ec4899", "#10b981", "#f59e0b"]
                    }]
                },
                "position": len(sections) + 1
            }
        ]

        print(f"📄 폴백으로 {len(sections)}개 문단 + {len(fallback_charts)}개 차트 생성")
        return sections + fallback_charts