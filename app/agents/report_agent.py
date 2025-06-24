# app/agents/report_agent.py
import json
import boto3
from typing import Dict, List, Any
from datetime import datetime
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from ..core.config import settings  # settings import 추가
from ..models.response import ReportSection, ReportStatistics, ProcessInfo, VisualizationData
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReportAgent(Runnable):
    """요약과 시각화를 결합하여 최종 리포트를 생성하는 에이전트"""

    def __init__(self):
        # 환경변수에서 LLM 설정 가져오기 (리포트는 일관성이 중요하므로 온도 낮춤)
        llm_config = settings.get_llm_config().copy()
        llm_config["temperature"] = max(llm_config["temperature"] - 0.1, 0.0)  # 리포트는 더 일관성 있게

        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.aws_region),
            model_id=settings.bedrock_model_id,
            model_kwargs=llm_config  # 환경변수 사용!
        )

        logger.info(f"📋 ReportAgent 초기화 - 온도: {llm_config['temperature']}, 최대토큰: {llm_config['max_tokens']}")

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """요약과 시각화를 결합하여 최종 리포트 생성"""
        summary = state.get("summary", "")
        visual_sections = state.get("visual_sections", [])
        youtube_url = state.get("youtube_url", "")
        caption = state.get("caption", "")

        if not summary or "[오류]" in summary:
            logger.warning("유효한 요약이 없습니다.")
            return {**state, "report_result": self._create_error_report("요약을 생성할 수 없습니다.")}

        try:
            logger.info("📋 최종 리포트 생성 중...")

            # 1. 요약을 섹션으로 구조화
            logger.info("📝 요약을 섹션으로 구조화 중...")
            structured_sections = self._structure_summary(summary)

            # 2. 시각화를 적절한 위치에 삽입
            logger.info(f"🎨 {len(visual_sections)}개의 시각화를 배치 중...")
            final_sections = self._merge_visualizations(structured_sections, visual_sections)

            # 3. 제목과 요약 추출
            title = self._extract_title(summary)
            brief_summary = self._create_brief_summary(summary)

            # 4. 통계 정보 생성
            statistics = ReportStatistics(
                total_sections=len(final_sections),
                text_sections=len([s for s in final_sections if s.get("type") == "text"]),
                visualizations=len([s for s in final_sections if s.get("type") == "visualization"])
            )

            # 5. 처리 정보 생성
            process_info = ProcessInfo(
                youtube_url=youtube_url,
                caption_length=len(caption),
                summary_length=len(summary)
            )

            # 6. 최종 리포트 구성
            report_result = {
                "success": True,
                "title": title,
                "summary": brief_summary,
                "sections": final_sections,
                "statistics": statistics.dict(),
                "process_info": process_info.dict(),
                "created_at": datetime.now()
            }

            logger.info(f"✅ 리포트 생성 완료: {len(final_sections)}개 섹션")
            return {**state, "report_result": report_result}

        except Exception as e:
            error_msg = f"리포트 생성 실패: {str(e)}"
            logger.error(error_msg)
            return {**state, "report_result": self._create_error_report(error_msg)}

    def _structure_summary(self, summary: str) -> List[Dict[str, Any]]:
        """요약을 논리적 섹션으로 구조화"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """주어진 요약을 논리적인 섹션으로 구조화해주세요.

**구조화 원칙:**
1. 각 섹션은 하나의 주제나 개념을 다룹니다
2. 섹션 제목은 명확하고 구체적이어야 합니다
3. 내용의 흐름이 자연스럽게 이어져야 합니다
4. 너무 짧거나 긴 섹션은 피합니다 (이상적: 100-400자)
5. 마크다운 헤더(#, ##, ###)를 기준으로 계층 구조를 파악합니다

**응답 형식 (JSON):**
{
  "sections": [
    {
      "id": "section_1",
      "title": "섹션 제목",
      "type": "text",
      "content": "섹션 내용",
      "level": 1,  // 1: 대제목(#), 2: 중제목(##), 3: 소제목(###)
      "keywords": ["키워드1", "키워드2"]  // 이 섹션의 핵심 키워드
    }
  ]
}

JSON만 출력하세요."""),
            ("human", "{summary}")
        ])

        try:
            response = self.llm.invoke(prompt.format_messages(summary=summary))
            content = response.content.strip()

            # JSON 추출
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                result = json.loads(json_str)
                return result.get('sections', [])
            else:
                # 폴백: 마크다운 헤더 기반 파싱
                return self._parse_markdown_sections(summary)

        except Exception as e:
            logger.error(f"섹션 구조화 오류: {e}")
            return self._parse_markdown_sections(summary)

    def _parse_markdown_sections(self, summary: str) -> List[Dict[str, Any]]:
        """마크다운 헤더를 기반으로 섹션 파싱 (폴백)"""
        lines = summary.split('\n')
        sections = []
        current_section = None
        section_counter = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 헤더 감지
            if line.startswith('#'):
                # 이전 섹션 저장
                if current_section and current_section['content'].strip():
                    sections.append(current_section)

                # 새 섹션 시작
                section_counter += 1
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()

                current_section = {
                    "id": f"section_{section_counter}",
                    "title": title,
                    "type": "text",
                    "content": "",
                    "level": min(level, 3),  # 최대 레벨 3
                    "keywords": []
                }
            elif current_section:
                # 내용 추가
                if current_section['content']:
                    current_section['content'] += '\n'
                current_section['content'] += line

        # 마지막 섹션 저장
        if current_section and current_section['content'].strip():
            sections.append(current_section)

        # 섹션이 없으면 전체를 하나의 섹션으로
        if not sections:
            sections.append({
                "id": "section_1",
                "title": "분석 내용",
                "type": "text",
                "content": summary,
                "level": 1,
                "keywords": []
            })

        return sections

    def _merge_visualizations(self, text_sections: List[Dict], visual_sections: List[Dict]) -> List[Dict]:
        """텍스트 섹션과 시각화를 적절히 병합"""
        if not visual_sections:
            return text_sections

        # 시각화를 위치 정보로 정렬
        sorted_visuals = sorted(
            visual_sections,
            key=lambda x: x.get('position', {}).get('after_paragraph', 999)
        )

        final_sections = []
        visual_index = 0

        for i, text_section in enumerate(text_sections):
            # 텍스트 섹션 추가
            final_sections.append(text_section)

            # 이 위치에 삽입할 시각화 확인
            while (visual_index < len(sorted_visuals) and
                   sorted_visuals[visual_index].get('position', {}).get('after_paragraph', 999) <= i):

                visual = sorted_visuals[visual_index]

                # 시각화 데이터 변환
                viz_data = None
                if visual.get('data'):
                    viz_data = VisualizationData(**visual['data'])

                final_sections.append({
                    "id": f"visual_{visual_index + 1}",
                    "title": visual.get('title', '시각화'),
                    "type": "visualization",
                    "visualization_type": visual.get('visualization_type'),
                    "data": viz_data.dict() if viz_data else None,
                    "insight": visual.get('insight', ''),
                    "purpose": visual.get('purpose', ''),
                    "user_benefit": visual.get('user_benefit', '')
                })
                visual_index += 1

        # 남은 시각화 추가
        while visual_index < len(sorted_visuals):
            visual = sorted_visuals[visual_index]

            viz_data = None
            if visual.get('data'):
                viz_data = VisualizationData(**visual['data'])

            final_sections.append({
                "id": f"visual_{visual_index + 1}",
                "title": visual.get('title', '시각화'),
                "type": "visualization",
                "visualization_type": visual.get('visualization_type'),
                "data": viz_data.dict() if viz_data else None,
                "insight": visual.get('insight', ''),
                "purpose": visual.get('purpose', ''),
                "user_benefit": visual.get('user_benefit', '')
            })
            visual_index += 1

        return final_sections

    def _extract_title(self, summary: str) -> str:
        """요약에서 적절한 제목 추출"""
        lines = summary.split('\n')

        # 첫 번째 헤더를 제목으로 사용
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                if title and len(title) < 100:
                    return title

        # 첫 문장을 제목으로 사용
        first_line = lines[0].strip() if lines else "YouTube 영상 분석"
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        return first_line or "YouTube 영상 분석"

    def _create_brief_summary(self, summary: str) -> str:
        """전체 요약의 간단한 요약 생성 (2-3문장)"""
        # 개요 섹션 찾기
        lines = summary.split('\n')
        overview_content = ""

        in_overview = False
        for line in lines:
            line = line.strip()
            if '개요' in line and line.startswith('#'):
                in_overview = True
                continue
            elif line.startswith('#') and in_overview:
                break
            elif in_overview and line:
                overview_content += line + ' '

        if overview_content:
            # 첫 2-3문장만 추출
            sentences = overview_content.split('.')
            brief = '. '.join(sentences[:3]).strip()
            if brief and not brief.endswith('.'):
                brief += '.'
            return brief

        # 폴백: 전체 요약의 첫 부분
        sentences = summary.replace('\n', ' ').split('.')
        important_sentences = []

        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                important_sentences.append(sentence)
                if len(important_sentences) >= 2:
                    break

        brief = '. '.join(important_sentences)
        if brief and not brief.endswith('.'):
            brief += '.'

        return brief or "YouTube 영상의 핵심 내용을 분석한 리포트입니다."

    def _create_error_report(self, error_message: str) -> Dict[str, Any]:
        """오류 발생 시 기본 리포트 생성"""
        return {
            "success": False,
            "title": "리포트 생성 실패",
            "summary": f"리포트 생성 중 오류가 발생했습니다: {error_message}",
            "sections": [
                {
                    "id": "error_section",
                    "title": "오류 정보",
                    "type": "text",
                    "content": f"죄송합니다. 리포트 생성 중 다음과 같은 오류가 발생했습니다:\n\n{error_message}\n\n다시 시도해 주시거나, 다른 영상으로 시도해 보세요.",
                    "level": 1,
                    "keywords": ["오류", "실패"]
                }
            ],
            "statistics": {
                "total_sections": 1,
                "text_sections": 1,
                "visualizations": 0
            },
            "process_info": {
                "youtube_url": "",
                "caption_length": 0,
                "summary_length": 0,
                "error": error_message
            },
            "created_at": datetime.now()
        }