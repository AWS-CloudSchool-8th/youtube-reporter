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

# ========== 1. 상태 정의 ==========
class ImprovedGraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
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
    model_kwargs={"temperature": 0.0, "max_tokens": 8000}
)

# ========== 5. 보고서 생성 프롬프트 ==========
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

# ========== 7. 시각화 요청 분석 에이전트 ==========
CONTEXT_ANALYSIS_PROMPT = """
당신은 보고서를 분석하여 시각화가 필요한 부분을 식별하는 전문가입니다.

## 임무
1. 보고서 내용을 깊이 분석
2. 시각화가 효과적인 내용 전달에 도움될 부분 식별 
3. 시각화와 관련된 **정확한 원본 텍스트 문단** 추출

## 보고서 분석
{report_text}

## 작업 단계
1. **전체 주제와 흐름 파악**
2. **시각화가 도움될 부분 식별** (비교, 과정, 개념, 데이터, 구조, 흐름 등)
3. **시각화와 직접 관련된 완전한 문단 추출**

## 중요 지침
- **related_content**에는 시각화와 직접 관련된 **완전한 문단**을 포함하세요
- 문장이 중간에 끊기지 않도록 **완성된 문장들**로 구성
- 시각화 주제와 **정확히 일치하는 내용**만 선택
- 최소 100자 이상의 의미 있는 텍스트 블록 제공

## 출력 형식
```json
{{
  "visualization_requests": [
    {{
      "purpose": "comparison|process|concept|overview|detail",
      "content_description": "시각화할 구체적 내용",
      "related_content": "시각화와 직접 관련된 완전한 원본 문단"
    }}
  ]
}}
```

JSON만 출력하세요.
"""

class ContextAnalysisAgent(Runnable):
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        
        logger.info("🏷️ 시각화 요청 분석 시작...")
        
        try:
            prompt = CONTEXT_ANALYSIS_PROMPT.format(report_text=report_text)
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = content[start_idx:end_idx+1]
                result = json.loads(json_part)
                
                viz_requests = result.get('visualization_requests', [])
                logger.info(f"✅ 분석 완료: {len(viz_requests)}개 시각화 요청")
                
                for i, req in enumerate(viz_requests):
                    content_len = len(req.get('related_content', ''))
                    logger.info(f"   요청 {i+1}: {req.get('purpose', 'unknown')} - {content_len}자")
                
                return {**state, "visualization_requests": viz_requests}
            else:
                logger.error("JSON 파싱 실패")
                return {**state, "visualization_requests": []}
                
        except Exception as e:
            logger.error(f"시각화 요청 분석 실패: {e}")
            return {**state, "visualization_requests": []}

# ========== 8. 시각화 생성 에이전트 ==========
VISUALIZATION_GENERATION_PROMPT = """
당신은 특정 태그와 맥락 정보를 바탕으로 정확한 시각화를 생성하는 전문가입니다.


## 시각화 요청 정보
- **목적**: {purpose}
- **내용**: {content_description}

## 원본 텍스트(이 정보만 사용하세요): {related_content}


## 전체 자막 (추가 참고용)
{caption_context}


## 지침
1. 제공된 맥락과 데이터를 정확히 활용
2. 독자 이해를 최대화
3. 위 원본 텍스트와 전체 자막에서 명시된 정보만 사용. **원본 텍스트, 전체 자막에 없는 임의의 데이터를 넣지 말 것**
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
  "chart_type": "function|scatter|heatmap|3d|line charts|pie charts|bubble charts|histograms",
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
  "diagram_type": "flowchart|timeline|concept",  
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

## 🔍 실제 작업 과정

1. **원본 텍스트 분석**: 구체적 수치, 항목, 관계 추출
2. **데이터 유형 판단**: 수치형/구조형/개념형 구분
3. **적절한 타입 선택**: 위 가이드에 따라 선택
4. **원본 기반 생성**: 추출된 정보만으로 시각화 구성
5. **data_source 추가**: 원본에서 인용한 구체적 부분 명시


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
            # 🔧 수정: tag_id 대신 인덱스 사용
            viz_id = f"viz_{i+1}"
            logger.info(f"🎯 시각화 {i+1}/{len(visualization_requests)} 생성 중... (ID: {viz_id})")
            
            try:
                prompt = VISUALIZATION_GENERATION_PROMPT.format(
                    purpose=req.get('purpose', ''),
                    content_description=req.get('content_description', ''),
                    related_content=req.get('related_content', ''),
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
                        "viz_id": viz_id,  # 🔧 수정: tag_id 대신 viz_id
                        "original_request": req,
                        "visualization": viz_result
                    })
                    
                    logger.info(f"✅ 시각화 {viz_id} 생성 성공")
                else:
                    logger.warning(f"⚠️ 시각화 {viz_id} JSON 파싱 실패")
                    
            except Exception as e:
                logger.error(f"❌ 시각화 {viz_id} 생성 실패: {e}")
        
        logger.info(f"🎨 시각화 생성 완료: {len(generated_visualizations)}/{len(visualization_requests)}개 성공")
        
        return {**state, "generated_visualizations": generated_visualizations}

# ========== 9. 최종 조립 에이전트 ==========
SMART_FINAL_ASSEMBLY_PROMPT = """
당신은 보고서와 시각화를 자연스럽게 조합하는 전문가입니다.

## 임무:
원본 보고서를 적절한 섹션으로 나누고, 각 시각화를 가장 어울리는 위치에 배치하세요.

## 원본 보고서:
{report_text}

## 생성된 시각화 목록:
{visualizations_summary}

## 배치 원칙:
1. **텍스트 유사성**: 시각화의 related_content와 가장 유사한 텍스트 부분 찾기
2. **논리적 흐름**: 독자가 자연스럽게 이해할 수 있는 순서
3. **섹션 완결성**: 각 섹션이 독립적으로도 이해 가능하도록

## 작업 방법:
1. 원본 보고서를 논리적 섹션으로 분할 (제목, 소제목, 주요 문단 기준)
2. 각 시각화의 related_content와 매칭되는 섹션 식별
3. 해당 섹션 직후에 시각화 배치
4. 전체적인 읽기 흐름 최적화

## 출력 형식:
```json
{{
  "sections": [
    {{
      "type": "text",
      "content": "첫 번째 섹션의 완전한 텍스트 내용",
      "section_info": "섹션 설명 (선택사항)"
    }},
    {{
      "type": "visualization",
      "viz_index": 0,
      "placement_reason": "이 위치에 배치한 이유",
      "content_match_score": "높음|중간|낮음"
    }},
    {{
      "type": "text", 
      "content": "두 번째 섹션의 완전한 텍스트 내용"
    }}
  ],
  "assembly_summary": {{
    "total_text_sections": 숫자,
    "total_visualizations": 숫자,
    "matching_method": "어떤 방식으로 매칭했는지"
  }}
}}
```

## 중요사항:
- **원본 보고서의 모든 텍스트를 반드시 포함**하세요
- 텍스트를 요약하거나 생략하지 마세요
- 각 시각화는 정확히 한 번만 배치하세요

JSON만 출력하세요.
"""

class SmartFinalAssemblyAgent(Runnable):
    """기존 방식 + 스마트 매칭을 결합한 조립 에이전트"""
    
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("🔧 스마트 최종 조립 시작...")
        
        if not generated_visualizations:
            logger.info("⚠️ 시각화가 없어서 텍스트만 반환")
            return {
                **state,
                "final_output": {
                    "format": "text_only",
                    "sections": [{"type": "text", "content": report_text}],
                    "total_paragraphs": 1,
                    "total_visuals": 0
                }
            }
        
        # 시각화 요약 정보 생성
        viz_summary = []
        for i, viz in enumerate(generated_visualizations):
            original_req = viz.get("original_request", {})
            viz_config = viz.get("visualization", {})
            
            summary = {
                "index": i,
                "title": viz_config.get("title", f"시각화 {i+1}"),
                "purpose": original_req.get("purpose", ""),
                "description": original_req.get("content_description", ""),
                "related_content_preview": original_req.get("related_content", "")[:150] + "..."
            }
            viz_summary.append(summary)
        
        try:
            prompt = SMART_FINAL_ASSEMBLY_PROMPT.format(
                report_text=report_text,
                visualizations_summary=json.dumps(viz_summary, indent=2, ensure_ascii=False)
            )
            
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = content[start_idx:end_idx+1]
                result = json.loads(json_part)
                
                sections = result.get("sections", [])
                assembly_summary = result.get("assembly_summary", {})
                
                # 시각화 정보 보강
                enhanced_sections = []
                for section in sections:
                    if section.get("type") == "visualization":
                        viz_index = section.get("viz_index", 0)
                        if 0 <= viz_index < len(generated_visualizations):
                            viz_data = generated_visualizations[viz_index]
                            enhanced_sections.append({
                                **section,
                                "config": viz_data["visualization"],
                                "original_request": viz_data["original_request"]
                            })
                        else:
                            logger.warning(f"⚠️ 잘못된 시각화 인덱스: {viz_index}")
                    else:
                        enhanced_sections.append(section)
                
                # 통계 계산
                text_count = len([s for s in enhanced_sections if s["type"] == "text"])
                viz_count = len([s for s in enhanced_sections if s["type"] == "visualization"])
                
                final_output = {
                    "format": "smart_assembly",
                    "sections": enhanced_sections,
                    "total_paragraphs": text_count,
                    "total_visuals": viz_count,
                    "assembly_stats": assembly_summary,
                    "assembly_method": "content_similarity_matching"
                }
                
                logger.info(f"🔧 스마트 조립 완료!")
                logger.info(f"📊 결과: 텍스트 {text_count}개, 시각화 {viz_count}개")
                
                return {**state, "final_output": final_output}
            else:
                logger.error("JSON 파싱 실패, 폴백 모드로 전환")
                return self._fallback_simple_assembly(state)
                
        except Exception as e:
            logger.error(f"스마트 조립 실패: {e}, 폴백 모드로 전환")
            return self._fallback_simple_assembly(state)
    
    def _fallback_simple_assembly(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """폴백: 기존 방식과 유사한 단순 조립"""
        report_text = state.get("report_text", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("🔄 폴백: 단순 조립 모드")
        
        # 텍스트를 문단별로 분할
        paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]
        
        sections = []
        
        # 첫 번째 절반의 텍스트
        mid_point = len(paragraphs) // 2
        if mid_point > 0:
            first_half = '\n\n'.join(paragraphs[:mid_point])
            sections.append({"type": "text", "content": first_half})
        
        # 시각화들 삽입
        for i, viz in enumerate(generated_visualizations):
            sections.append({
                "type": "visualization",
                "viz_index": i,
                "config": viz["visualization"],
                "original_request": viz["original_request"],
                "placement_reason": "폴백 모드 - 중간 위치 배치"
            })
        
        # 나머지 텍스트
        if mid_point < len(paragraphs):
            second_half = '\n\n'.join(paragraphs[mid_point:])
            sections.append({"type": "text", "content": second_half})
        
        return {
            **state,
            "final_output": {
                "format": "fallback_simple",
                "sections": sections,
                "total_paragraphs": 2 if len(paragraphs) > 1 else 1,
                "total_visuals": len(generated_visualizations),
                "assembly_method": "fallback_paragraph_split"
            }
        }

# ========== 그래프 구성 수정 (조립 에이전트만 교체) ==========
def build_hybrid_graph():
    builder = StateGraph(state_schema=ImprovedGraphState)
    
    builder.add_node("caption_node", ToolAgent(extract_youtube_caption_tool, "youtube_url", "caption"))
    builder.add_node("report_node", LangGraphAgentNode(report_agent_executor_runnable, "caption", "report_text"))
    builder.add_node("tagging_node", ContextAnalysisAgent())  # 기존 유지
    builder.add_node("visualization_node", TargetedVisualizationAgent())  # 기존 유지  
    builder.add_node("assembly_node", SmartFinalAssemblyAgent())  # 새로운 스마트 조립
    
    builder.set_entry_point("caption_node")
    builder.add_edge("caption_node", "report_node") 
    builder.add_edge("report_node", "tagging_node")
    builder.add_edge("tagging_node", "visualization_node")
    builder.add_edge("visualization_node", "assembly_node")
    builder.add_edge("assembly_node", "__end__")
    
    return builder.compile()

# 하이브리드 그래프
hybrid_graph = build_hybrid_graph()

# ========== 실행 함수 ==========
@traceable(name="hybrid-architecture-youtube-report")
def run_hybrid_architecture(youtube_url: str) -> Dict[str, Any]:
    """하이브리드 아키텍처로 YouTube 보고서 생성"""
    logger.info("\n🚀 [Hybrid Architecture] 실행 시작")
    logger.info(f"🎯 입력 URL: {youtube_url}")
    
    try:
        result = hybrid_graph.invoke({"youtube_url": youtube_url})
        logger.info("\n✅ [Hybrid Architecture] 실행 완료")
        
        final_output = result.get('final_output', {})
        logger.info(f"📦 최종 결과: 텍스트 {final_output.get('total_paragraphs', 0)}개, 시각화 {final_output.get('total_visuals', 0)}개")
        logger.info(f"🔧 조립 방식: {final_output.get('assembly_method', 'unknown')}")
        
        return result
    except Exception as e:
        logger.error(f"\n❌ [Hybrid Architecture] 실행 실패: {e}")
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
run_graph = run_hybrid_architecture