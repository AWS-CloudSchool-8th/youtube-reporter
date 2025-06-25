import os
import requests
import json
from typing import TypedDict, List, Dict, Any, Optional
import boto3
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langsmith.run_helpers import traceable
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== 1. 상태 정의 (확장됨) ==========
class ImprovedGraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    tagged_report: str
    visualization_requests: List[Dict]
    generated_visualizations: List[Dict]
    final_output: Dict

# ========== 2. 환경 변수 로딩 ==========
load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

# ========== 3. 자막 추출 도구 ==========
def extract_youtube_caption_tool(youtube_url: str) -> str:
    """YouTube 자막 추출"""
    try:
        api_url = "https://vidcap.xyz/api/v1/youtube/caption"
        params = {"url": youtube_url, "locale": "ko"}
        headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get("data", {}).get("content", "")
    except Exception as e:
        logger.error(f"자막 추출 오류: {e}")
        return f"[자막 추출 실패: {str(e)}]"

# ========== 4. LLM 설정 ==========
llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name=AWS_REGION),
    model_id=BEDROCK_MODEL_ID,
    model_kwargs={"temperature": 0.0, "max_tokens": 4096}
)

# ========== 5. 개선된 보고서 생성 프롬프트 ==========
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 유튜브 자막을 상세하고 완전한 보고서로 재작성하는 AI야.

## 핵심 원칙
- **완전성**: 독자가 영상을 보지 않아도 100% 이해 가능해야 함
- **구체성**: 중요한 수치, 사례, 인용구는 반드시 포함
- **상세성**: 각 섹션은 충분히 자세하게 설명 (최소 500자 이상)

## 보고서 작성 지침

#### 1.1 표지 정보
- 보고서 제목: "[영상 제목] 분석 보고서"

#### 1.2 목차
- 각 섹션별 페이지 번호 포함
- 최소 5개 이상의 주요 섹션 구성

#### 1.3 필수 섹션 구성
1. **개요 (Executive Summary)**
- 영상의 핵심 내용 요약 (200-300자)
- 주요 키워드 및 핵심 메시지

2. **주요 내용 분석**
- 최소 3개 이상의 세부 문단
- 각 문단당 500자 이상
- 문단 구조: 소제목 + 요약 + 상세 설명

3. **핵심 인사이트**
- 영상에서 도출되는 주요 시사점
- 실무적/학술적 함의

4. **결론 및 제언**
- 전체 내용 종합
- 향후 방향성 또는 응용 가능성

5. **부록**
- 주요 인용구
- 참고 자료 (해당 시)

### 2. 작성 기준

#### 2.1 문체 및 형식
- **서술형 문장**: 구어체를 문어체로 완전 변환
- **객관적 어조**: 3인칭 관점에서 서술
- **전문적 표현**: 학술적/비즈니스 용어 활용
- **논리적 연결**: 문장 간 연결고리 명확화

#### 2.2 내용 구성
- **구체적 정보 필수 포함**:
  - 정확한 수치 (년도, 크기, 비율 등)
  - 구체적 사례와 예시
  - 중요한 인용구나 발언
  - 회사명, 제품명, 기술명 등

- **각 섹션 최소 500자 이상**:
  - 단순 요약이 아닌 상세한 설명
  - 배경 정보와 맥락 제공
  - 원인과 결과, 영향 분석

- **완전한 이해를 위한 서술**:
  - 전문 용어는 반드시 설명 추가
  - 복잡한 개념은 단계별로 설명
  - 독자가 추가 검색 없이도 이해 가능하도록

#### 2.3 품질 기준
- **일관성**: 전체 보고서의 어조와 형식 통일
- **완결성**: 각 섹션이 독립적으로도 이해 가능
- **정확성**: 원본 자막 내용 왜곡 없이 재구성
- **가독성**: 명확한 제목, 부제목, 단락 구분
- **완전성**: 영상의 모든 중요한 내용을 포함하여, 독자가 영상을 보지 않아도 전체 내용을 이해할 수 있도록 한다."""),
    ("human", "{input}")
])

def structure_report(caption: str) -> str:
    """자막을 구조화된 보고서로 변환"""
    try:
        messages = structure_prompt.format_messages(input=caption)
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        logger.error(f"보고서 생성 오류: {e}")
        return f"[보고서 생성 실패: {str(e)}]"

report_agent_executor_runnable = RunnableLambda(structure_report)

# ========== 6. 헬퍼 클래스들 ==========
class ToolAgent(Runnable):
    """단순 도구를 LangGraph 노드로 변환"""
    def __init__(self, tool_func, input_key: str, output_key: str):
        self.tool_func = tool_func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.tool_func(input_value)
        return {**state, self.output_key: result}

class LangGraphAgentNode(Runnable):
    """LangChain Runnable을 LangGraph 노드로 변환"""
    def __init__(self, runnable, input_key: str, output_key: str):
        self.runnable = runnable
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.runnable.invoke(input_value)
        return {**state, self.output_key: result}

# ========== 7. 개선된 맥락 분석 및 태깅 에이전트 ==========
IMPROVED_CONTEXT_AND_TAGGING_PROMPT = """
당신은 보고서를 분석하여 시각화가 필요한 부분을 식별하고 태그를 삽입하는 전문가입니다.

## 임무
1. 보고서 내용을 깊이 분석
2. 시각화가 효과적인 내용 전달에 도움될 부분 식별 
3. 시각화가 구조화된 내용 전달에 도움될 부분 식별 
4. 해당 위치에 간단한 숫자 태그 삽입
5. 각 태그별로 시각화와 관련된 **정확한 원본 텍스트 문단** 추출

## 보고서 분석
{report_text}

## 작업 단계
1. **전체 주제와 흐름 파악**
2. **시각화가 도움될 부분 식별** (비교, 과정, 개념, 데이터 등)
3. **각 부분에 [VIZ_1], [VIZ_2], [VIZ_3] 형태로 태그 삽입**
4. **태그별로 시각화와 직접 관련된 완전한 문단 추출**

## 중요 지침
- **related_content**에는 시각화와 직접 관련된 **완전한 문단**을 포함하세요
- 문장이 중간에 끊기지 않도록 **완성된 문장들**로 구성
- 시각화 주제와 **정확히 일치하는 내용**만 선택
- 최소 100자 이상의 의미 있는 텍스트 블록 제공

## 출력 형식
```json
{{
  "tagged_report": "태그가 삽입된 전체 보고서 텍스트",
  "visualization_requests": [
    {{
      "tag_id": "1",
      "purpose": "comparison|process|concept|overview|detail",
      "content_description": "시각화할 구체적 내용",
      "related_content": "시각화와 직접 관련된 완전한 원본 문단 (완성된 문장들로 구성)"
    }}
  ]
}}
```

## 예시
만약 VM과 Docker 비교 시각화라면:
```json
{{
  "tag_id": "1",
  "purpose": "comparison", 
  "content_description": "VM과 Docker 아키텍처 비교",
  "related_content": "가상머신은 하이퍼바이저를 통해 전체 운영체제를 가상화하는 방식으로 작동합니다. 각 VM은 독립적인 운영체제를 실행하며, 이로 인해 높은 격리성을 제공하지만 상당한 리소스 오버헤드가 발생합니다. 반면 Docker 컨테이너는 호스트 운영체제의 커널을 공유하면서 애플리케이션 레벨에서만 격리를 제공합니다. 이러한 구조적 차이로 인해 컨테이너는 VM 대비 훨씬 가벼운 리소스 사용량을 보이며, 시작 시간도 현저히 빠릅니다."
}}
```

JSON만 출력하세요.
"""

class ImprovedContextAndTaggingAgent(Runnable):
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        
        logger.info("🏷️ 개선된 맥락 분석 및 태깅 시작...")
        
        try:
            prompt = IMPROVED_CONTEXT_AND_TAGGING_PROMPT.format(report_text=report_text)
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = content[start_idx:end_idx+1]
                result = json.loads(json_part)
                
                logger.info(f"✅ 개선된 태깅 완료: {len(result.get('visualization_requests', []))}개 시각화 요청")
                
                # 추출된 텍스트 길이 확인
                for req in result.get('visualization_requests', []):
                    related_content = req.get('related_content', '')
                    logger.info(f"태그 {req.get('tag_id')}: 관련 텍스트 {len(related_content)}자 추출")
                
                return {
                    **state,
                    "tagged_report": result.get("tagged_report", report_text),
                    "visualization_requests": result.get("visualization_requests", [])
                }
            else:
                logger.error("JSON 파싱 실패")
                return {**state, "tagged_report": report_text, "visualization_requests": []}
                
        except Exception as e:
            logger.error(f"개선된 맥락 분석 및 태깅 실패: {e}")
            return {**state, "tagged_report": report_text, "visualization_requests": []}

# ========== 8. 타겟팅된 시각화 생성 에이전트 ==========
TARGETED_VISUALIZATION_PROMPT = """
당신은 특정 태그와 맥락 정보를 바탕으로 정확한 시각화를 생성하는 전문가입니다.

## 시각화 요청 정보
- **태그 ID**: {tag_id}
- **목적**: {purpose}
- **내용**: {content_description}
- **주변 맥락**: {position_context}
- **데이터 소스**: {data_source}
- **필요한 이유**: {why_helpful}

## 전체 자막 (추가 참고용)
{caption_context}

## 지침
1. 제공된 맥락과 데이터를 정확히 활용
2. 태그가 삽입될 위치에서 독자 이해를 최대화
3. 보고서에 언급된 실제 정보만 사용
4. 요청된 목적에 정확히 부합하는 시각화 생성

## 사용 가능한 시각화 타입
- **chartjs**: 데이터 비교, 트렌드, 비율
- **plotly**: 수학적/과학적 그래프, 복잡한 데이터
- **mermaid**: 프로세스, 플로우차트, 타임라인
- **markmap**: 개념 관계, 마인드맵, 분류 체계
- **table**: 구조화된 정보, 비교표

다음 중 하나의 형식으로 응답하세요:

**1. Chart.js 차트:**
{{
  "type": "chartjs",
  "chart_type": "bar|line|pie|radar|scatter",
  "title": "차트 제목",
  "config": {{
    "type": "bar",
    "data": {{
      "labels": ["항목1", "항목2", "항목3"],
      "datasets": [{{
        "label": "데이터셋 이름",
        "data": [10, 20, 30],
        "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
      }}]
    }},
    "options": {{
      "responsive": true,
      "maintainAspectRatio": false
    }}
  }},
  "insight": "이 차트를 통해 얻을 수 있는 인사이트"
}}

**2. Plotly 수학/과학:**
{{
  "type": "plotly", 
  "chart_type": "function|scatter|heatmap|3d",
  "title": "그래프 제목",
  "config": {{
    "data": [{{
      "x": [1, 2, 3, 4],
      "y": [10, 11, 12, 13],
      "type": "scatter",
      "mode": "lines+markers"
    }}],
    "layout": {{
      "title": "그래프 제목",
      "xaxis": {{"title": "X축"}},
      "yaxis": {{"title": "Y축"}}
    }}
  }},
  "insight": "이 그래프를 통해 얻을 수 있는 인사이트"
}}

**3. Mermaid 다이어그램:**
{{
  "type": "mermaid",
  "diagram_type": "flowchart|timeline",  
  "title": "다이어그램 제목",
  "code": "graph TD\\n    A[Start] --> B[Process]\\n    B --> C[End]",
  "insight": "이 다이어그램을 통해 얻을 수 있는 인사이트"
}}

**4. Markmap 마인드맵:**
{{
  "type": "markmap",
  "title": "마인드맵 제목",
  "markdown": "# 중심 주제\\n\\n## 큰 분류 1\\n\\n- 세부사항 1\\n- 세부사항 2\\n  - 하위 항목\\n\\n## 큰 분류 2\\n\\n- 세부사항 A\\n- 세부사항 B",
  "insight": "이 마인드맵을 통해 얻을 수 있는 인사이트"
}}

**5. HTML 테이블:**
{{
  "type": "table",
  "title": "표 제목", 
  "data": {{
    "headers": ["항목", "값", "설명"],
    "rows": [
      ["항목1", "값1", "설명1"],
      ["항목2", "값2", "설명2"]
    ]
  }},
  "insight": "이 표를 통해 얻을 수 있는 인사이트"
}}

**6. 창의적 제안:**
{{
  "type": "creative",
  "method": "제안하는 방법",
  "description": "어떻게 구현할지",
  "insight": "왜 이 방법이 최적인지"
}}

JSON만 출력하세요.
"""

class TargetedVisualizationAgent(Runnable):
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        visualization_requests = state.get("visualization_requests", [])
        caption_context = state.get("caption", "")
        
        if not visualization_requests:
            logger.info("❌ 시각화 요청이 없습니다.")
            return {**state, "generated_visualizations": []}
        
        logger.info(f"🎨 {len(visualization_requests)}개 시각화 생성 시작...")
        
        generated_visualizations = []
        
        for i, req in enumerate(visualization_requests):
            logger.info(f"🎯 시각화 {i+1}/{len(visualization_requests)} 생성 중... (태그: {req.get('tag_id', 'unknown')})")
            
            try:
                prompt = TARGETED_VISUALIZATION_PROMPT.format(
                    tag_id=req.get('tag_id', ''),
                    purpose=req.get('purpose', ''),
                    content_description=req.get('content_description', ''),
                    position_context=req.get('position_context', ''),
                    data_source=req.get('data_source', ''),
                    why_helpful=req.get('why_helpful', ''),
                    caption_context=caption_context[:1000]  # 길이 제한
                )
                
                response = llm.invoke(prompt)
                content = response.content.strip()
                
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_part = content[start_idx:end_idx+1]
                    viz_result = json.loads(json_part)
                    
                    generated_visualizations.append({
                        "tag_id": req.get('tag_id'),
                        "original_request": req,
                        "visualization": viz_result
                    })
                    
                    logger.info(f"✅ 태그 {req.get('tag_id')} 시각화 생성 성공")
                else:
                    logger.warning(f"⚠️ 태그 {req.get('tag_id')} JSON 파싱 실패")
                    
            except Exception as e:
                logger.error(f"❌ 태그 {req.get('tag_id')} 시각화 생성 실패: {e}")
        
        logger.info(f"🎨 시각화 생성 완료: {len(generated_visualizations)}/{len(visualization_requests)}개 성공")
        
        return {**state, "generated_visualizations": generated_visualizations}

# ========== 9. 최종 조립 에이전트 ==========
class SimplifiedFinalAssemblyAgent(Runnable):
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        tagged_report = state.get("tagged_report", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("🔧 간소화된 최종 보고서 조립 시작...")
        
        # 시각화를 태그 ID별로 매핑
        viz_by_tag = {viz["tag_id"]: viz["visualization"] for viz in generated_visualizations}
        
        # 최종 섹션 생성
        final_sections = []
        current_text = ""
        
        # 태그를 찾아서 교체하면서 섹션 생성
        tag_pattern = r'\[VIZ_(\d+)\]'
        
        last_end = 0
        for match in re.finditer(tag_pattern, tagged_report):
            tag_id = match.group(1)
            
            # 태그 이전의 텍스트 추가
            text_before = tagged_report[last_end:match.start()].strip()
            if text_before:
                current_text += text_before
            
            # 누적된 텍스트가 있으면 섹션으로 추가
            if current_text.strip():
                final_sections.append({
                    "type": "text",
                    "content": current_text.strip()
                })
                current_text = ""
            
            # 해당 태그의 시각화 추가 (있다면)
            if tag_id in viz_by_tag:
                # 원본 요청에서 관련 텍스트 추출
                original_request = next(
                    (viz["original_request"] for viz in generated_visualizations if viz["tag_id"] == tag_id), 
                    {}
                )
                
                # related_content만 사용
                related_content = original_request.get("related_content", "").strip()
                
                # 백업: related_content가 없으면 기존 로직 사용
                if not related_content or len(related_content) < 20:
                    position_context = original_request.get("position_context", "").strip()
                    if position_context and len(position_context) > 20:
                        related_content = position_context
                
                final_sections.append({
                    "type": "visualization",
                    "tag_id": tag_id,
                    "config": viz_by_tag[tag_id],
                    "original_request": original_request,
                    "original_text": related_content
                })
                logger.info(f"✅ 태그 {tag_id} 시각화 삽입 완료 (관련 텍스트: {len(related_content)}자)")
            else:
                logger.warning(f"⚠️ 태그 {tag_id}에 대한 시각화를 찾을 수 없음")
            
            last_end = match.end()
        
        # 마지막 남은 텍스트 추가
        remaining_text = tagged_report[last_end:].strip()
        if remaining_text:
            current_text += remaining_text
            if current_text.strip():
                final_sections.append({
                    "type": "text",
                    "content": current_text.strip()
                })
        
        # 통계 계산
        text_count = len([s for s in final_sections if s["type"] == "text"])
        viz_count = len([s for s in final_sections if s["type"] == "visualization"])
        
        final_output = {
            "format": "integrated_sequential",
            "sections": final_sections,
            "total_paragraphs": text_count,
            "total_visuals": viz_count,
            "assembly_stats": {
                "total_tags_found": len(re.findall(tag_pattern, tagged_report)),
                "visualizations_inserted": viz_count,
                "success_rate": f"{viz_count}/{len(re.findall(tag_pattern, tagged_report))}"
            }
        }
        
        logger.info(f"🔧 간소화된 조립 완료!")
        logger.info(f"📊 결과: 텍스트 {text_count}개, 시각화 {viz_count}개")
        
        return {**state, "final_output": final_output}

# ========== 10. 개선된 그래프 구성 ==========
def build_improved_graph():
    builder = StateGraph(state_schema=ImprovedGraphState)
    
    builder.add_node("caption_node", ToolAgent(extract_youtube_caption_tool, "youtube_url", "caption"))
    builder.add_node("report_node", LangGraphAgentNode(report_agent_executor_runnable, "caption", "report_text"))
    builder.add_node("tagging_node", ImprovedContextAndTaggingAgent())
    builder.add_node("visualization_node", TargetedVisualizationAgent())
    builder.add_node("assembly_node", SimplifiedFinalAssemblyAgent())
    
    builder.set_entry_point("caption_node")
    builder.add_edge("caption_node", "report_node")
    builder.add_edge("report_node", "tagging_node")
    builder.add_edge("tagging_node", "visualization_node")
    builder.add_edge("visualization_node", "assembly_node")
    builder.add_edge("assembly_node", "__end__")
    
    return builder.compile()

# 컴파일된 그래프
improved_compiled_graph = build_improved_graph()

# ========== 11. 실행 함수 ==========
@traceable(name="improved-sequential-youtube-report")
def run_improved_graph(youtube_url: str) -> Dict[str, Any]:
    """개선된 순차 통합 YouTube 보고서 생성"""
    logger.info("\n🚀 [Improved Sequential Graph] 실행 시작")
    logger.info(f"🎯 입력 URL: {youtube_url}")
    
    try:
        result = improved_compiled_graph.invoke({"youtube_url": youtube_url})
        logger.info("\n✅ [Improved Sequential Graph] 실행 완료")
        
        stats = result['final_output'].get('assembly_stats', {})
        logger.info(f"📦 최종 결과: 텍스트 {result['final_output']['total_paragraphs']}개, 시각화 {result['final_output']['total_visuals']}개")
        logger.info(f"📊 조립 성공률: {stats.get('success_rate', 'N/A')}")
        
        return result
    except Exception as e:
        logger.error(f"\n❌ [Improved Sequential Graph] 실행 실패: {e}")
        return {
            "youtube_url": youtube_url,
            "final_output": {
                "format": "error",
                "error": str(e),
                "sections": [],
                "total_paragraphs": 0,
                "total_visuals": 0
            }
        }

# 기존 호환성을 위한 별칭
run_graph = run_improved_graph