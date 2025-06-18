# services/smart_visualization_service.py
from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
from utils.exceptions import VisualizationError
from utils.error_handler import safe_execute
import json
import re
from typing import List, Dict, Tuple
from enum import Enum


class VisualizationType(Enum):
    # 텍스트
    PARAGRAPH = "paragraph"
    HEADING = "heading"

    # 기본 차트
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"

    # 고급 시각화
    MINDMAP = "mindmap"  # 개념 관계도
    FLOWCHART = "flowchart"  # 프로세스/단계
    TIMELINE = "timeline"  # 시간순 진행
    NETWORK = "network"  # 관계/연결
    TREE = "tree"  # 계층구조
    COMPARISON = "comparison"  # 비교표
    PROCESS = "process"  # 단계별 프로세스
    HIERARCHY = "hierarchy"  # 조직도/구조
    CYCLE = "cycle"  # 순환 구조
    MATRIX = "matrix"  # 매트릭스/격자


class SmartVisualizationService:
    def __init__(self):
        self.llm = create_llm()
        self._setup_prompts()
        self._setup_content_patterns()

    def _setup_prompts(self):
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 YouTube 영상 내용을 분석하여 최적의 시각화 방법을 제안하는 전문가입니다.

            영상 내용을 분석하고 다음과 같은 시각화 타입 중 가장 적절한 것들을 선택하세요:

            **텍스트 기반:**
            - paragraph: 일반 설명 텍스트
            - heading: 제목/소제목

            **차트 기반:**
            - bar_chart: 수치 비교 (판매량, 점수, 순위 등)
            - line_chart: 시간별 변화 (추세, 성장률, 변화량 등)
            - pie_chart: 비율/구성 (점유율, 분포, 할당 등)

            **고급 시각화:**
            - mindmap: 개념 연결, 아이디어 맵, 주제 확장
            - flowchart: 알고리즘, 의사결정, 업무 프로세스
            - timeline: 역사, 일정, 순차적 사건
            - network: 관계도, 소셜 네트워크, 연결구조
            - tree: 분류체계, 조직도, 계층구조
            - comparison: 제품비교, 장단점, vs 구조
            - process: 단계별 진행, 파이프라인, 워크플로우
            - hierarchy: 순위, 레벨, 상하구조
            - cycle: 생명주기, 순환과정, 반복구조
            - matrix: 2차원 분류, 사분면, 좌표계

            **분석 기준:**
            1. 영상에서 다루는 주제의 성격
            2. 데이터의 형태 (수치, 관계, 시간, 구조)
            3. 설명하려는 개념의 복잡도
            4. 시청자 이해도 향상에 도움되는 형태

            JSON 형식으로 응답하세요:
            {
              "content_type": "영상 주제 분류 (교육/리뷰/뉴스/요리/기술/등)",
              "recommended_visualizations": [
                {
                  "type": "시각화_타입",
                  "reason": "선택 이유",
                  "priority": 1-5 (우선순위),
                  "position": "적절한 위치 (시작/중간/끝)"
                }
              ]
            }
            """),
            ("human", "영상 자막:\n{caption}\n\n보고서:\n{report}")
        ])

        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            지정된 시각화 타입에 맞는 실제 데이터를 생성하세요.
            영상 내용을 바탕으로 구체적이고 의미있는 데이터를 만들어야 합니다.

            시각화 타입별 데이터 구조:

            **차트 타입 (bar_chart, line_chart, pie_chart):**
            ```json
            {
              "type": "chart_type",
              "title": "차트 제목", 
              "data": {
                "labels": ["라벨1", "라벨2", "라벨3"],
                "datasets": [{
                  "label": "데이터셋명",
                  "data": [값1, 값2, 값3],
                  "backgroundColor": "색상"
                }]
              }
            }
            ```

            **마인드맵 (mindmap):**
            ```json
            {
              "type": "mindmap",
              "title": "마인드맵 제목",
              "data": {
                "center": "중심 주제",
                "branches": [
                  {
                    "label": "주 가지1",
                    "children": ["세부1", "세부2", "세부3"]
                  },
                  {
                    "label": "주 가지2", 
                    "children": ["세부A", "세부B"]
                  }
                ]
              }
            }
            ```

            **플로우차트 (flowchart):**
            ```json
            {
              "type": "flowchart",
              "title": "프로세스 흐름",
              "data": {
                "nodes": [
                  {"id": "1", "label": "시작", "type": "start"},
                  {"id": "2", "label": "단계1", "type": "process"},
                  {"id": "3", "label": "결정", "type": "decision"},
                  {"id": "4", "label": "결과", "type": "end"}
                ],
                "edges": [
                  {"from": "1", "to": "2"},
                  {"from": "2", "to": "3"},
                  {"from": "3", "to": "4"}
                ]
              }
            }
            ```

            **타임라인 (timeline):**
            ```json
            {
              "type": "timeline",
              "title": "시간순 진행",
              "data": {
                "events": [
                  {"time": "2020", "title": "사건1", "description": "설명1"},
                  {"time": "2021", "title": "사건2", "description": "설명2"},
                  {"time": "2022", "title": "사건3", "description": "설명3"}
                ]
              }
            }
            ```

            **비교표 (comparison):**
            ```json
            {
              "type": "comparison",
              "title": "비교 분석",
              "data": {
                "items": ["항목A", "항목B", "항목C"],
                "criteria": ["기준1", "기준2", "기준3"],
                "values": [
                  ["A의 기준1", "A의 기준2", "A의 기준3"],
                  ["B의 기준1", "B의 기준2", "B의 기준3"],
                  ["C의 기준1", "C의 기준2", "C의 기준3"]
                ]
              }
            }
            ```

            **계층구조 (tree/hierarchy):**
            ```json
            {
              "type": "tree",
              "title": "구조도",
              "data": {
                "root": "최상위",
                "children": [
                  {
                    "label": "레벨1-1",
                    "children": [
                      {"label": "레벨2-1"},
                      {"label": "레벨2-2"}
                    ]
                  },
                  {
                    "label": "레벨1-2",
                    "children": [
                      {"label": "레벨2-3"}
                    ]
                  }
                ]
              }
            }
            ```

            영상 내용을 반영한 실제적인 데이터를 생성하세요.
            """),
            ("human", "시각화 타입: {viz_type}\n영상 내용: {content}\n관련 부분: {relevant_text}")
        ])

    def _setup_content_patterns(self):
        """콘텐츠 패턴별 시각화 매핑"""
        self.content_patterns = {
            # 교육/강의 영상
            "교육": ["mindmap", "flowchart", "hierarchy", "process"],
            "강의": ["mindmap", "timeline", "comparison", "tree"],
            "학습": ["flowchart", "mindmap", "process", "hierarchy"],

            # 리뷰/비교 영상
            "리뷰": ["comparison", "bar_chart", "pie_chart", "matrix"],
            "비교": ["comparison", "bar_chart", "matrix"],
            "추천": ["comparison", "hierarchy", "bar_chart"],

            # 요리/레시피 영상
            "요리": ["flowchart", "process", "timeline", "tree"],
            "레시피": ["process", "flowchart", "timeline"],
            "만들기": ["process", "flowchart", "timeline"],

            # 기술/개발 영상
            "프로그래밍": ["flowchart", "tree", "network", "mindmap"],
            "개발": ["flowchart", "process", "hierarchy", "network"],
            "코딩": ["flowchart", "tree", "process"],

            # 뉴스/분석 영상
            "뉴스": ["timeline", "bar_chart", "line_chart", "network"],
            "분석": ["comparison", "matrix", "bar_chart", "network"],
            "정치": ["network", "timeline", "comparison"],

            # 역사/다큐멘터리
            "역사": ["timeline", "network", "tree", "mindmap"],
            "다큐": ["timeline", "network", "comparison"],

            # 비즈니스/경제
            "비즈니스": ["hierarchy", "network", "comparison", "flowchart"],
            "경제": ["line_chart", "bar_chart", "network", "comparison"],
            "투자": ["line_chart", "comparison", "matrix"],

            # 게임/엔터테인먼트
            "게임": ["hierarchy", "tree", "comparison", "network"],
            "엔터": ["network", "timeline", "comparison"]
        }

    async def analyze_and_generate_visualizations(self, caption: str, report_text: str) -> List[Dict]:
        """영상 내용 분석 후 적절한 시각화 생성"""

        # 1단계: 내용 분석 및 시각화 타입 추천
        analysis = await self._analyze_content_type(caption, report_text)

        # 2단계: 추천된 시각화별 데이터 생성
        visualizations = []

        # 보고서를 섹션별로 분할
        report_sections = self._split_report_into_sections(report_text)

        # 각 섹션에 적절한 시각화 배치
        for i, section in enumerate(report_sections):
            # 텍스트 섹션 추가
            visualizations.append({
                "type": "paragraph",
                "title": section.get("title", f"섹션 {i + 1}"),
                "content": section.get("content", ""),
                "position": len(visualizations)
            })

            # 해당 섹션에 적절한 시각화 선택
            suitable_viz = self._select_visualization_for_section(
                section, analysis, caption
            )

            if suitable_viz:
                viz_data = await self._generate_visualization_data(
                    suitable_viz, section.get("content", ""), caption
                )
                if viz_data:
                    viz_data["position"] = len(visualizations)
                    visualizations.append(viz_data)

        return visualizations

    async def _analyze_content_type(self, caption: str, report: str) -> Dict:
        """내용 분석 및 시각화 추천"""
        try:
            messages = self.analysis_prompt.format_messages(
                caption=caption[:1500],  # 길이 제한
                report=report[:1500]
            )
            response = self.llm.invoke(messages)

            if response and response.content:
                # JSON 파싱 시도
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()

                analysis = json.loads(content)
                print(f"📊 내용 분석 결과: {analysis.get('content_type', 'Unknown')}")
                return analysis

        except Exception as e:
            print(f"⚠️ 내용 분석 실패: {e}")

        # 기본값 반환
        return {
            "content_type": "general",
            "recommended_visualizations": [
                {"type": "mindmap", "reason": "일반적인 개념 정리", "priority": 3, "position": "중간"},
                {"type": "bar_chart", "reason": "기본 데이터 표현", "priority": 2, "position": "끝"}
            ]
        }

    def _split_report_into_sections(self, report_text: str) -> List[Dict]:
        """보고서를 의미 단위로 분할"""
        sections = []

        # 제목별로 분할 시도
        lines = report_text.split('\n')
        current_section = {"title": "", "content": ""}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 제목 패턴 감지
            if (line.startswith('#') or
                    line.endswith(':') or
                    any(keyword in line for keyword in ['요약', '주요', '결론', '개요', '분석'])):

                # 이전 섹션 저장
                if current_section["content"]:
                    sections.append(current_section)

                # 새 섹션 시작
                current_section = {
                    "title": line.replace('#', '').replace(':', '').strip(),
                    "content": ""
                }
            else:
                current_section["content"] += line + " "

        # 마지막 섹션 저장
        if current_section["content"]:
            sections.append(current_section)

        # 최소 1개 섹션 보장
        if not sections:
            sections = [{"title": "영상 내용", "content": report_text}]

        print(f"📄 보고서를 {len(sections)}개 섹션으로 분할")
        return sections

    def _select_visualization_for_section(self, section: Dict, analysis: Dict, caption: str) -> str:
        """섹션 내용에 가장 적합한 시각화 타입 선택"""
        content = section.get("content", "").lower()
        title = section.get("title", "").lower()

        # 키워드 기반 시각화 선택
        if any(word in content or word in title for word in ['단계', '과정', '방법', '절차']):
            return "flowchart"
        elif any(word in content or word in title for word in ['개념', '관계', '연결', '구조']):
            return "mindmap"
        elif any(word in content or word in title for word in ['시간', '순서', '역사', '발전']):
            return "timeline"
        elif any(word in content or word in title for word in ['비교', '차이', '대비', 'vs']):
            return "comparison"
        elif any(word in content or word in title for word in ['조직', '계층', '분류', '체계']):
            return "tree"
        elif re.search(r'\d+%|\d+점|\d+위', content):  # 수치 데이터
            return "bar_chart"
        elif any(word in content for word in ['증가', '감소', '변화', '추세']):
            return "line_chart"
        elif any(word in content for word in ['비율', '분포', '구성', '점유']):
            return "pie_chart"

        # 분석 결과 기반 선택
        recommended = analysis.get("recommended_visualizations", [])
        if recommended:
            return recommended[0].get("type", "mindmap")

        return "mindmap"  # 기본값

    async def _generate_visualization_data(self, viz_type: str, content: str, caption: str) -> Dict:
        """특정 시각화 타입의 데이터 생성"""
        try:
            messages = self.generation_prompt.format_messages(
                viz_type=viz_type,
                content=caption[:800],  # 전체 맥락
                relevant_text=content[:400]  # 관련 부분
            )
            response = self.llm.invoke(messages)

            if response and response.content:
                content_text = response.content.strip()
                if content_text.startswith("```json"):
                    content_text = content_text.replace("```json", "").replace("```", "").strip()

                viz_data = json.loads(content_text)
                print(f"📊 {viz_type} 시각화 데이터 생성 완료")
                return viz_data

        except Exception as e:
            print(f"⚠️ {viz_type} 시각화 생성 실패: {e}")

        # 실패 시 기본 시각화 생성
        return self._create_fallback_visualization(viz_type, content)

    def _create_fallback_visualization(self, viz_type: str, content: str) -> Dict:
        """기본 시각화 데이터 생성"""
        # 내용에서 키워드 추출
        keywords = re.findall(r'[가-힣]{2,}', content)
        top_keywords = list(set(keywords))[:4]

        if not top_keywords:
            top_keywords = ["주제1", "주제2", "주제3", "주제4"]

        fallback_data = {
            "mindmap": {
                "type": "mindmap",
                "title": "주요 개념",
                "data": {
                    "center": "핵심 주제",
                    "branches": [
                        {"label": keyword, "children": [f"{keyword} 세부1", f"{keyword} 세부2"]}
                        for keyword in top_keywords[:3]
                    ]
                }
            },
            "flowchart": {
                "type": "flowchart",
                "title": "진행 과정",
                "data": {
                    "nodes": [
                        {"id": "1", "label": "시작", "type": "start"},
                        {"id": "2", "label": top_keywords[0] if len(top_keywords) > 0 else "단계1", "type": "process"},
                        {"id": "3", "label": top_keywords[1] if len(top_keywords) > 1 else "단계2", "type": "process"},
                        {"id": "4", "label": "완료", "type": "end"}
                    ],
                    "edges": [
                        {"from": "1", "to": "2"},
                        {"from": "2", "to": "3"},
                        {"from": "3", "to": "4"}
                    ]
                }
            },
            "comparison": {
                "type": "comparison",
                "title": "비교 분석",
                "data": {
                    "items": top_keywords[:3],
                    "criteria": ["특징1", "특징2", "특징3"],
                    "values": [
                        ["우수", "보통", "좋음"],
                        ["좋음", "우수", "보통"],
                        ["보통", "좋음", "우수"]
                    ]
                }
            },
            "timeline": {
                "type": "timeline",
                "title": "시간순 진행",
                "data": {
                    "events": [
                        {"time": "1단계", "title": top_keywords[0] if len(top_keywords) > 0 else "시작",
                         "description": "첫 번째 단계"},
                        {"time": "2단계", "title": top_keywords[1] if len(top_keywords) > 1 else "진행",
                         "description": "두 번째 단계"},
                        {"time": "3단계", "title": top_keywords[2] if len(top_keywords) > 2 else "완료",
                         "description": "세 번째 단계"}
                    ]
                }
            }
        }

        return fallback_data.get(viz_type, {
            "type": "bar_chart",
            "title": "데이터 분석",
            "data": {
                "labels": top_keywords,
                "datasets": [{
                    "label": "중요도",
                    "data": [85, 75, 65, 55],
                    "backgroundColor": "#6366f1"
                }]
            }
        })