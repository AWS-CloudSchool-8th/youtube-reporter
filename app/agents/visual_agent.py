# app/agents/visual_agent.py
import json
import boto3
from typing import Dict, List, Any, Optional
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from ..core.config import settings  # settings import 추가
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VisualAgent(Runnable):
    """스마트 시각화 생성 에이전트"""

    def __init__(self):
        # 환경변수에서 LLM 설정 가져오기 (시각화는 더 창의적이므로 온도 약간 높임)
        llm_config = settings.get_llm_config().copy()
        llm_config["temperature"] = min(llm_config["temperature"] + 0.2, 1.0)  # 시각화는 더 창의적으로

        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.aws_region),
            model_id=settings.bedrock_model_id,
            model_kwargs=llm_config  # 환경변수 사용!
        )
        
        # 시각화 타입별 기본 색상 팔레트 설정
        self.color_palettes = {
            "default": ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f", "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"],
            "sequential": ["#d3d3d3", "#a8a8a8", "#7e7e7e", "#545454", "#2a2a2a"],
            "diverging": ["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
            "categorical": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
            "emphasis": ["#c7c7c7", "#c7c7c7", "#c7c7c7", "#ff5722", "#c7c7c7", "#c7c7c7"]
        }
        
        # 시각화 타입별 최적 차트 매핑
        self.visualization_mapping = {
            "comparison": ["bar", "radar", "table"],
            "distribution": ["pie", "doughnut", "bar"],
            "trend": ["line", "bar"],
            "correlation": ["scatter", "line"],
            "hierarchy": ["diagram", "mindmap"],
            "process": ["flowchart", "diagram"],
            "timeline": ["timeline", "line"]
        }

        logger.info(f"🎨 VisualAgent 초기화 - 온도: {llm_config['temperature']}, 최대토큰: {llm_config['max_tokens']}")
        logger.info(f"📊 지원 시각화 타입: {len(self.visualization_mapping)} 종류, 색상 팔레트: {len(self.color_palettes)} 종류")

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """스마트 시각화 생성"""
        summary = state.get("summary", "")
        youtube_url = state.get("youtube_url", "")

        if not summary or "[오류]" in summary:
            logger.warning("유효한 요약이 없습니다.")
            return {**state, "visual_sections": []}

        try:
            logger.info("🎨 스마트 시각화 분석 시작...")

            # 1단계: 컨텍스트 분석
            context = self._analyze_context(summary)
            if not context or "error" in context:
                logger.error(f"컨텍스트 분석 실패: {context}")
                return {**state, "visual_sections": []}

            # 2단계: 시각화 기회별로 최적의 시각화 생성
            opportunities = context.get('visualization_opportunities', [])
            logger.info(f"🎯 {len(opportunities)}개의 시각화 기회 발견")
            
            # 기회가 없는 경우 기본 시각화 생성 고려
            if not opportunities and summary:
                logger.info("시각화 기회가 발견되지 않았습니다. 기본 시각화 생성 고려 중...")
                default_opportunities = self._generate_default_opportunities(summary, context)
                if default_opportunities:
                    opportunities = default_opportunities
                    logger.info(f"💡 {len(opportunities)}개의 기본 시각화 기회 생성")

            visual_sections = []
            for i, opportunity in enumerate(opportunities):
                logger.info(f"🎨 시각화 {i + 1}/{len(opportunities)} 생성 중...")

                visualization = self._generate_smart_visualization(context, opportunity)
                if visualization and "error" not in visualization:
                    # 적절한 위치 찾기
                    position = self._find_best_position(summary, opportunity)

                    visual_section = {
                        "position": position,
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

            # 3단계: 시각화 품질 검사 및 최적화
            if visual_sections:
                visual_sections = self._optimize_visualizations(visual_sections, summary)
                logger.info(f"🔧 시각화 최적화 완료")

            logger.info(f"📊 총 {len(visual_sections)}개의 시각화 생성 완료")
            return {**state, "visual_sections": visual_sections}

        except Exception as e:
            error_msg = f"시각화 생성 중 오류: {str(e)}"
            logger.error(error_msg)
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
각 시각화는 명확한 목적과 사용자 가치를 가져야 합니다.

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
      "location_hint": "요약 내 대략적 위치 (beginning/middle/end)",
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

**당신의 임무:**
1. 이 내용을 가장 명확하고 직관적으로 표현할 시각화 방법 결정
2. 실제 데이터를 추출하거나 합리적으로 생성
3. 구체적인 시각화 설정 제공

**사용 가능한 시각화 유형:**

1. **Chart.js 차트**
   - bar: 항목 간 비교, 순위
   - line: 시간에 따른 변화, 추세
   - pie/doughnut: 구성 비율, 점유율
   - radar: 다차원 비교
   - scatter: 상관관계, 분포

2. **Mermaid 다이어그램**
   - flowchart: 프로세스, 의사결정 흐름
   - timeline: 시간 순서, 역사적 사건
   - mindmap: 개념 구조, 분류 체계
   - gantt: 프로젝트 일정

3. **HTML 테이블**
   - 정확한 수치 비교
   - 다양한 속성을 가진 항목들
   - 체크리스트, 기능 비교표

**응답 형식 (반드시 다음 중 하나):**

**옵션 1 - Chart.js 차트:**
{
  "type": "chart",
  "library": "chartjs",
  "title": "명확한 제목",
  "chart_type": "bar|line|pie|radar|scatter",
  "data": {
    "labels": ["레이블1", "레이블2", ...],
    "datasets": [
      {
        "label": "데이터셋 이름",
        "data": [숫자1, 숫자2, ...],
        "backgroundColor": ["색상1", "색상2", ...]
      }
    ]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "title": { "display": true, "text": "차트 제목" },
      "legend": { "position": "top" }
    }
  },
  "insight": "이 차트가 보여주는 핵심 인사이트"
}

**옵션 2 - Mermaid 다이어그램:**
{
  "type": "diagram",
  "library": "mermaid",
  "title": "명확한 제목",
  "diagram_type": "flowchart|timeline|mindmap",
  "code": "Mermaid 다이어그램 코드",
  "insight": "이 다이어그램이 설명하는 핵심 내용"
}

**옵션 3 - HTML 테이블:**
{
  "type": "table",
  "title": "명확한 제목",
  "headers": ["열1", "열2", "열3"],
  "rows": [
    ["데이터1-1", "데이터1-2", "데이터1-3"],
    ["데이터2-1", "데이터2-2", "데이터2-3"]
  ],
  "styling": {
    "highlight_column": 0,
    "sortable": true
  },
  "insight": "이 표가 보여주는 핵심 정보"
}

**중요 지침:**
- 내용에서 실제 데이터를 추출하세요
- 데이터가 없다면 내용을 기반으로 합리적으로 생성하세요
- 색상은 의미를 담아 선택하세요 (증가=녹색, 감소=빨강 등)
- 제목과 레이블은 명확하고 구체적으로
- insight는 단순 설명이 아닌 "발견"이어야 합니다

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
                return json.loads(json_str)
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
            
            # 키워드 매칭 점수 계산
            keyword_score = sum(1 for keyword in keywords if keyword in paragraph_lower)
            
            # 위치 힌트에 따른 가중치 적용
            position_weight = 1.0
            if location_hint == 'beginning' and i < total_paragraphs // 3:
                position_weight = 1.5
            elif location_hint == 'middle' and total_paragraphs // 3 <= i < 2 * total_paragraphs // 3:
                position_weight = 1.5
            elif location_hint == 'end' and i >= 2 * total_paragraphs // 3:
                position_weight = 1.5
                
            # 최종 점수 계산
            score = keyword_score * position_weight
            
            # 최고 점수 갱신
            if score > max_score:
                max_score = score
                best_position = i
        
        # 위치 정보 반환
        return {
            "after_paragraph": best_position,
            "score": max_score,
            "total_paragraphs": total_paragraphs
        }
        
    def _standardize_visualization_data(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """시각화 데이터를 표준 형식으로 변환"""
        viz_type = visualization.get('type', '')
        
        if viz_type == 'chart':
            # Chart.js 차트 데이터 표준화
            chart_type = visualization.get('chart_type', 'bar')
            data = visualization.get('data', {})
            options = visualization.get('options', {})
            
            # 색상 팔레트 적용 및 데이터 개선
            enhanced_data = self._enhance_chart_data(data, chart_type)
            enhanced_options = self._enhance_chart_options(options, chart_type)
            
            return {
                "type": "chart",
                "library": "chartjs",
                "config": {
                    "type": chart_type,
                    "data": enhanced_data,
                    "options": enhanced_options
                }
            }
            
        elif viz_type == 'diagram':
            # Mermaid 다이어그램 데이터 표준화
            diagram_type = visualization.get('diagram_type', 'flowchart')
            code = visualization.get('code', '')
            
            # Mermaid 코드 개선
            enhanced_code = self._enhance_mermaid_code(code, diagram_type)
            
            return {
                "type": "diagram",
                "library": "mermaid",
                "diagram_type": diagram_type,
                "code": enhanced_code
            }
            
        elif viz_type == 'table':
            # HTML 테이블 데이터 표준화
            headers = visualization.get('headers', [])
            rows = visualization.get('rows', [])
            styling = visualization.get('styling', {})
            
            # 테이블 스타일링 개선
            enhanced_styling = self._enhance_table_styling(styling)
            
            return {
                "type": "table",
                "headers": headers,
                "rows": rows,
                "styling": enhanced_styling
            }
            
        else:
            # 알 수 없는 타입의 경우 원본 반환
            logger.warning(f"알 수 없는 시각화 타입: {viz_type}")
            return visualization
            
    def _enhance_chart_data(self, data: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """차트 데이터 개선 - 색상 팔레트 적용 등"""
        if not data:
            return data
            
        # 데이터셋이 없는 경우 기본 구조 생성
        if 'datasets' not in data:
            data['datasets'] = []
            
        # 차트 타입에 따라 적절한 색상 팔레트 선택
        palette_key = "default"
        if chart_type in ['pie', 'doughnut']:
            palette_key = "categorical"
        elif chart_type == 'line':
            palette_key = "sequential"
        elif chart_type == 'bar' and len(data.get('datasets', [])) > 1:
            palette_key = "categorical"
            
        palette = self.color_palettes.get(palette_key, self.color_palettes["default"])
        
        # 각 데이터셋에 색상 적용
        for i, dataset in enumerate(data.get('datasets', [])):
            if chart_type in ['pie', 'doughnut']:
                # 파이/도넛 차트는 각 데이터에 다른 색상 적용
                if 'backgroundColor' not in dataset:
                    dataset['backgroundColor'] = [palette[i % len(palette)] for i in range(len(dataset.get('data', [])))]                    
            else:
                # 다른 차트는 각 데이터셋에 하나의 색상 적용
                if 'backgroundColor' not in dataset:
                    dataset['backgroundColor'] = palette[i % len(palette)]
                if 'borderColor' not in dataset and chart_type == 'line':
                    dataset['borderColor'] = palette[i % len(palette)]
                    dataset['fill'] = False
                    
        return data
        
    def _enhance_chart_options(self, options: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """차트 옵션 개선 - 가독성 및 사용자 경험 향상"""
        if not options:
            options = {}
            
        # 기본 옵션 설정
        if 'responsive' not in options:
            options['responsive'] = True
            
        if 'maintainAspectRatio' not in options:
            options['maintainAspectRatio'] = False
            
        # plugins 설정
        if 'plugins' not in options:
            options['plugins'] = {}
            
        plugins = options['plugins']
        
        # 범례 설정
        if 'legend' not in plugins:
            plugins['legend'] = {'position': 'top'}
            
        # 툴팁 설정
        if 'tooltip' not in plugins:
            plugins['tooltip'] = {'mode': 'index', 'intersect': False}
            
        # 차트 타입별 추가 설정
        if chart_type == 'bar':
            if 'scales' not in options:
                options['scales'] = {
                    'y': {
                        'beginAtZero': True
                    }
                }
        elif chart_type == 'line':
            if 'scales' not in options:
                options['scales'] = {
                    'y': {
                        'beginAtZero': True
                    }
                }
            if 'elements' not in options:
                options['elements'] = {
                    'line': {
                        'tension': 0.4  # 스무스한 라인
                    }
                }
                
        return options
        
    def _enhance_mermaid_code(self, code: str, diagram_type: str) -> str:
        """머메이드 다이어그램 코드 개선"""
        if not code:
            return code
            
        # 다이어그램 타입이 없는 경우 추가
        if not code.strip().startswith(diagram_type):
            code = f"{diagram_type}\n{code}"
            
        # 플로우차트 개선
        if diagram_type == 'flowchart' and 'TD' not in code and 'LR' not in code:
            code = code.replace('flowchart', 'flowchart TD')
            
        # 스타일 설정이 없는 경우 기본 스타일 추가
        if '%%{' not in code:
            style_config = "%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#5D8AA8', 'lineColor': '#5D8AA8', 'textColor': '#333' }}}%%\n"
            code = style_config + code
            
        return code
        
    def _enhance_table_styling(self, styling: Dict[str, Any]) -> Dict[str, Any]:
        """테이블 스타일링 개선"""
        if not styling:
            styling = {}
            
        # 기본 정렬 기능 활성화
        if 'sortable' not in styling:
            styling['sortable'] = True
            
        # 기본 스트라이프 테이블 설정
        if 'striped' not in styling:
            styling['striped'] = True
            
        # 기본 테두리 설정
        if 'bordered' not in styling:
            styling['bordered'] = True
            
        # 기본 하이라이트 설정
        if 'hover' not in styling:
            styling['hover'] = True
            
        return styling
        
    def _generate_default_opportunities(self, summary: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """기본 시각화 기회 생성 - 분석에서 기회가 발견되지 않은 경우"""
        opportunities = []
        main_topic = context.get('main_topic', '')
        key_concepts = context.get('key_concepts', [])
        content_structure = context.get('content_structure', {})
        
        # 1. 주요 개념 구조화 - 마인드맵
        if key_concepts and len(key_concepts) >= 3:
            opportunities.append({
                "content": f"{main_topic}의 주요 개념과 관계",
                "location_hint": "beginning",
                "purpose": "overview",
                "why_necessary": "주요 개념의 관계를 한눈에 파악하기 위해",
                "user_benefit": "전체 내용의 구조를 쉽게 이해할 수 있습니다",
                "suggested_type": "diagram",
                "key_elements": key_concepts
            })
        
        # 2. 프로세스 플로우차트 - 단계적 과정이 있는 경우
        if content_structure.get('has_process', False):
            opportunities.append({
                "content": f"{main_topic}의 프로세스 흐름도",
                "location_hint": "middle",
                "purpose": "process",
                "why_necessary": "단계적 과정을 시각적으로 표현하기 위해",
                "user_benefit": "복잡한 프로세스를 쉽게 이해할 수 있습니다",
                "suggested_type": "diagram",
                "key_elements": ["Step 1", "Step 2", "Step 3", "Step 4"]
            })
        
        # 3. 비교 차트 - 비교 요소가 있는 경우
        if content_structure.get('has_comparison', False):
            opportunities.append({
                "content": f"{main_topic}의 주요 요소 비교",
                "location_hint": "middle",
                "purpose": "comparison",
                "why_necessary": "주요 요소들의 차이와 유사점을 비교하기 위해",
                "user_benefit": "요소들 간의 차이를 한눈에 파악할 수 있습니다",
                "suggested_type": "chart",
                "key_elements": key_concepts[:5] if key_concepts else ["Item 1", "Item 2", "Item 3"]
            })
        
        # 4. 타임라인 - 시간 흐름이 있는 경우
        if content_structure.get('has_timeline', False):
            opportunities.append({
                "content": f"{main_topic}의 시간적 발전",
                "location_hint": "end",
                "purpose": "timeline",
                "why_necessary": "시간에 따른 변화를 시각화하기 위해",
                "user_benefit": "시간적 흐름을 한눈에 파악할 수 있습니다",
                "suggested_type": "diagram",
                "key_elements": ["Event 1", "Event 2", "Event 3", "Event 4"]
            })
        
        # 5. 요약 테이블 - 데이터가 있는 경우
        if content_structure.get('has_data', False):
            opportunities.append({
                "content": f"{main_topic}의 주요 데이터 요약",
                "location_hint": "end",
                "purpose": "data",
                "why_necessary": "중요한 데이터를 구조화하여 제시하기 위해",
                "user_benefit": "중요한 수치와 통계를 한눈에 파악할 수 있습니다",
                "suggested_type": "table",
                "key_elements": ["Category", "Value", "Description"]
            })
        
        # 최대 3개만 선택
        return opportunities[:3]
        
    def _optimize_visualizations(self, visual_sections: List[Dict[str, Any]], summary: str) -> List[Dict[str, Any]]:
        """시각화 최적화 - 중복 제거, 위치 조정, 품질 개선"""
        if not visual_sections:
            return []
            
        # 1. 중복 시각화 필터링
        unique_sections = []
        titles = set()
        
        for section in visual_sections:
            title = section.get('title', '')
            if title and title not in titles:
                titles.add(title)
                unique_sections.append(section)
            elif not title:
                unique_sections.append(section)
                
        # 2. 위치 최적화 - 너무 가까운 시각화들 사이에 간격 주기
        if len(unique_sections) > 1:
            # 위치순 정렬
            unique_sections.sort(key=lambda x: x.get('position', {}).get('after_paragraph', 0))
            
            # 가까운 시각화들 사이에 간격 주기
            paragraphs = summary.split('\n\n')
            total_paragraphs = len(paragraphs)
            min_gap = max(1, total_paragraphs // (len(unique_sections) * 3))  # 최소 간격
            
            for i in range(1, len(unique_sections)):
                prev_pos = unique_sections[i-1].get('position', {}).get('after_paragraph', 0)
                curr_pos = unique_sections[i].get('position', {}).get('after_paragraph', 0)
                
                if curr_pos - prev_pos < min_gap:
                    # 간격이 너무 작으면 조정
                    new_pos = min(prev_pos + min_gap, total_paragraphs - 1)
                    unique_sections[i]['position']['after_paragraph'] = new_pos
        
        # 3. 시각화 타입 밸런스 조정 - 다양한 타입이 있는지 확인
        chart_count = sum(1 for s in unique_sections if s.get('data', {}).get('type') == 'chart')
        diagram_count = sum(1 for s in unique_sections if s.get('data', {}).get('type') == 'diagram')
        table_count = sum(1 for s in unique_sections if s.get('data', {}).get('type') == 'table')
        
        # 너무 한 타입에 치우치지 않도록 조정 (예: 차트만 3개 이상이면 일부를 제거)
        if len(unique_sections) > 3 and chart_count > 2 and diagram_count == 0 and table_count == 0:
            # 차트만 너무 많은 경우 일부 제거
            chart_sections = [s for s in unique_sections if s.get('data', {}).get('type') == 'chart']
            chart_sections.sort(key=lambda x: x.get('position', {}).get('score', 0), reverse=True)
            
            # 점수가 낮은 차트 일부 제거
            sections_to_remove = chart_sections[2:]
            unique_sections = [s for s in unique_sections if s not in sections_to_remove]
        
        # 4. 시각화 수가 너무 많은 경우 점수가 낮은 것들 제거
        if len(unique_sections) > 5:
            # 점수순 정렬
            unique_sections.sort(key=lambda x: x.get('position', {}).get('score', 0), reverse=True)
            # 상위 5개만 유지
            unique_sections = unique_sections[:5]
            # 다시 위치순 정렬
            unique_sections.sort(key=lambda x: x.get('position', {}).get('after_paragraph', 0))
        
        return unique_sections