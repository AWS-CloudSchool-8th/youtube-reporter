# app/agents/visual_agent.py
import os
import json
import boto3
from typing import Dict, List, Any, Optional
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from app.core.config import settings
from app.services.state_manager import state_manager

logger = get_logger(__name__)


class SmartVisualAgent(Runnable):
    """요약 내용을 분석하여 최적의 시각화를 자동 생성하는 스마트 에이전트 - taeho 백엔드 통합 버전"""

    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            model_kwargs={"temperature": 0.7, "max_tokens": 4096}
        )

    def invoke(self, state: dict, config=None) -> dict:
        """요약을 분석하여 시각화 생성"""
        summary = state.get("summary", "")
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info("🎯 스마트 시각화 생성 시작...")

        # 진행률 업데이트
        if job_id:
            try:
                state_manager.update_progress(job_id, 60, "🎨 스마트 시각화 생성 중...")
            except Exception as e:
                logger.warning(f"진행률 업데이트 실패 (무시됨): {e}")

        if not summary or len(summary) < 100:
            logger.warning("유효한 요약이 없습니다.")
            return {**state, "visual_sections": []}

        try:
            # 1단계: 컨텍스트 분석
            logger.info("🧠 1단계: 컨텍스트 분석 시작...")
            context = self._analyze_context(summary)

            if not context or "error" in context:
                logger.error(f"컨텍스트 분석 실패: {context}")
                return {**state, "visual_sections": []}

            # 2단계: 시각화 기회별로 최적의 시각화 생성
            logger.info(f"🎯 2단계: {len(context.get('visualization_opportunities', []))}개의 시각화 기회 발견")
            visual_sections = []

            for i, opportunity in enumerate(context.get('visualization_opportunities', [])):
                logger.info(f"🎨 시각화 {i + 1} 생성 중...")
                visualization = self._generate_smart_visualization(context, opportunity)

                if visualization and "error" not in visualization:
                    # 요약 내 적절한 위치 찾기
                    position = self._find_best_position(summary, opportunity)

                    visual_section = {
                        "position": position,
                        "type": "visualization",
                        "title": visualization.get('title', opportunity.get('content', '시각화')[:50]),
                        "visualization_type": visualization.get('type'),
                        "data": self._standardize_visualization_data(visualization),
                        "insight": visualization.get('insight', ''),
                        "purpose": opportunity.get('purpose', ''),
                        "user_benefit": opportunity.get('user_benefit', '')
                    }
                    visual_sections.append(visual_section)
                    logger.info(f"✅ 시각화 생성 성공: {visualization.get('type')}")
                else:
                    logger.warning(f"⚠️ 시각화 {i + 1} 생성 실패")

            logger.info(f"📊 총 {len(visual_sections)}개의 시각화 생성 완료")
            return {**state, "visual_sections": visual_sections}

        except Exception as e:
            logger.error(f"시각화 생성 중 오류: {str(e)}")
            return {**state, "visual_sections": []}

    def _analyze_context(self, summary: str) -> Dict[str, Any]:
        """요약 내용의 맥락을 깊이 분석"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 텍스트를 분석하여 시각화가 필요한 부분을 찾아내는 전문가입니다.

주어진 요약을 분석하여 독자의 이해를 크게 향상시킬 수 있는 시각화 기회를 찾아주세요.

**분석 기준:**
1. **복잡한 개념**: 텍스트만으로는 이해하기 어려운 추상적 개념
2. **프로세스/절차**: 단계별 과정이나 흐름
3. **비교/대조**: 여러 항목 간의 차이점이나 유사점
4. **데이터/수치**: 통계, 비율, 추세 등 수치 정보
5. **관계/구조**: 요소들 간의 연결이나 계층 구조
6. **시간 흐름**: 시간에 따른 변화나 타임라인

**중요**: 시각화는 "있으면 좋은" 것이 아니라 "반드시 필요한" 경우에만 제안하세요.

**응답 형식 (JSON):**
{
  "main_topic": "전체 주제",
  "key_concepts": ["핵심개념1", "핵심개념2", "핵심개념3"],
  "content_structure": {
    "has_process": true/false,
    "has_comparison": true/false,
    "has_data": true/false,
    "has_timeline": true/false,
    "has_hierarchy": true/false
  },
  "visualization_opportunities": [
    {
      "content": "시각화할 구체적 내용",
      "location_hint": "요약 내 대략적 위치 (처음/중간/끝)",
      "purpose": "overview|detail|comparison|process|data|timeline|structure",
      "why_necessary": "왜 이 시각화가 필수적인지",
      "user_benefit": "독자가 얻을 구체적 이익",
      "suggested_type": "chart|diagram|table|mindmap|timeline|flowchart",
      "key_elements": ["포함해야 할 핵심 요소들"]
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
                return json.loads(json_str)
            else:
                return {"error": "JSON 파싱 실패"}

        except Exception as e:
            logger.error(f"컨텍스트 분석 오류: {e}")
            return {"error": str(e)}

    def _generate_smart_visualization(self, context: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """주어진 기회에 대해 최적의 시각화 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 주어진 내용을 가장 효과적으로 시각화하는 전문가입니다.

**상황:**
- 주제: {main_topic}
- 시각화 목적: {purpose}
- 필요한 이유: {why_necessary}
- 사용자 이익: {user_benefit}

**시각화할 내용:**
{content}

**핵심 요소:**
{key_elements}

**사용 가능한 시각화 유형:**

1. **차트 (Chart.js)**
   - bar: 항목 간 비교, 순위
   - line: 시간에 따른 변화, 추세
   - pie/doughnut: 구성 비율, 점유율
   - radar: 다차원 비교
   - scatter: 상관관계, 분포

2. **네트워크 다이어그램 (vis.js)**
   - network: 관계도, 연결망 시각화
   - hierarchy: 계층 구조 표현

3. **플로우 차트 (React Flow)**
   - flowchart: 프로세스, 의사결정 흐름
   - workflow: 작업 흐름도

4. **테이블 (HTML)**
   - 정확한 수치 비교
   - 다양한 속성을 가진 항목들

**응답 형식 (JSON):**
{
  "type": "chart|network|flow|table",
  "title": "명확한 제목",
  "data": { 적절한 데이터 구조 },
  "options": { 설정 옵션 },
  "insight": "이 시각화가 보여주는 핵심 인사이트"
}

JSON만 출력하세요."""),
            ("human", "시각화를 생성해주세요.")
        ])

        try:
            # 컨텍스트 정보 포맷팅
            formatted_prompt = prompt.format_messages(
                main_topic=context.get('main_topic', ''),
                purpose=opportunity.get('purpose', ''),
                why_necessary=opportunity.get('why_necessary', ''),
                user_benefit=opportunity.get('user_benefit', ''),
                content=opportunity.get('content', ''),
                key_elements=', '.join(opportunity.get('key_elements', []))
            )

            response = self.llm.invoke(formatted_prompt)
            content = response.content.strip()

            # JSON 추출
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                result = json.loads(json_str)
                return result
            else:
                return {"error": "JSON 파싱 실패"}

        except Exception as e:
            logger.error(f"시각화 생성 오류: {e}")
            return {"error": str(e)}

    def _find_best_position(self, summary: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """요약 내에서 시각화를 배치할 최적의 위치 찾기"""
        content = opportunity.get('content', '')
        location_hint = opportunity.get('location_hint', 'middle')

        # 간단한 휴리스틱으로 위치 결정
        paragraphs = summary.split('\n\n')
        total_paragraphs = len(paragraphs)

        # 관련 키워드 찾기
        keywords = content.lower().split()[:5]  # 처음 5개 단어

        best_position = 0
        max_score = 0

        for i, paragraph in enumerate(paragraphs):
            paragraph_lower = paragraph.lower()
            score = sum(1 for keyword in keywords if keyword in paragraph_lower)

            # 위치 힌트에 따른 가중치
            if location_hint == "beginning" and i < total_paragraphs // 3:
                score += 2
            elif location_hint == "middle" and total_paragraphs // 3 <= i < 2 * total_paragraphs // 3:
                score += 2
            elif location_hint == "end" and i >= 2 * total_paragraphs // 3:
                score += 2

            if score > max_score:
                max_score = score
                best_position = i

        return {
            "after_paragraph": best_position,
            "relevance_score": max_score
        }

    def _standardize_visualization_data(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """다양한 시각화 형식을 표준화"""
        viz_type = visualization.get('type')

        if viz_type == 'chart':
            return {
                "type": "chart",
                "config": {
                    "type": visualization.get('chart_type', 'bar'),
                    "data": visualization.get('data', {}),
                    "options": visualization.get('options', {})
                }
            }

        elif viz_type == 'network':
            return {
                "type": "network",
                "data": visualization.get('data', {}),
                "options": visualization.get('options', {})
            }

        elif viz_type == 'flow':
            return {
                "type": "flow",
                "data": visualization.get('data', {}),
                "options": visualization.get('options', {})
            }

        elif viz_type == 'table':
            return {
                "type": "table",
                "headers": visualization.get('headers', []),
                "rows": visualization.get('rows', []),
                "styling": visualization.get('styling', {})
            }

        else:
            return visualization