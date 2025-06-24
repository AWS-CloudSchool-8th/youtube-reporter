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

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # ← name → __name__으로 수정

# ========== 1. 상태 정의 ==========
class GraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    visual_requirements: List[Dict]
    visual_results: List[Dict]
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

# ========== 5. 보고서 생성 ==========
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 유튜브 자막을 보고서 형식으로 재작성하는 AI야. 다음 규칙을 따르세요:\n"
               "1. 자막 내용을 서술형 문장으로 바꾸세요.\n"
               "2. 3개 이상의 문단, 300자 이상.\n"
               "3. 각 문단은 요약+설명 형식으로 작성하세요.\n"
               "4. 핵심 내용을 누락하지 말고 포괄적으로 작성하세요."),
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
    def __init__(self, tool_func, input_key: str, output_key: str):  # ← init → __init__으로 수정
        self.tool_func = tool_func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.tool_func(input_value)
        return {**state, self.output_key: result}

class LangGraphAgentNode(Runnable):
    """LangChain Runnable을 LangGraph 노드로 변환"""
    def __init__(self, runnable, input_key: str, output_key: str):  # ← init → __init__으로 수정
        self.runnable = runnable
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.runnable.invoke(input_value)
        return {**state, self.output_key: result}

class MergeTool(Runnable):
    """최종 결과 병합"""
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        visual_results = state.get("visual_results", [])

        # 보고서를 문단으로 분할
        paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]

        # 섹션 생성
        sections = []

        # 문단 추가
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # 너무 짧은 문단 제외
                sections.append({
                    "type": "paragraph",
                    "content": paragraph
                })

        # 시각화 추가
        sections.extend(visual_results)

        # 통계 계산
        total_paragraphs = len([s for s in sections if s["type"] == "paragraph"])
        total_visuals = len([s for s in sections if s["type"] != "paragraph"])

        final_output = {
            "format": "mixed",
            "sections": sections,
            "total_paragraphs": total_paragraphs,
            "total_visuals": total_visuals
        }

        return {**state, "final_output": final_output}

# ========== 7. 스마트 시각화 시스템 ==========
CONTEXT_ANALYSIS_PROMPT = """
당신은 YouTube 보고서의 맥락을 깊이 분석하는 전문가입니다.

다음 보고서를 분석해서 사용자가 영상을 보지 않고도 완전히 이해할 수 있도록 도와주세요.

보고서:
{report_text}

**분석 단계:**
1. **전체 주제와 목적** 파악
2. **핵심 개념들** 추출  
3. **이해하기 어려운 부분** 식별
4. **시각화로 도움될 수 있는 부분** 판단

**응답 형식:**
{{
  "main_topic": "전체 주제",
  "key_concepts": ["개념1", "개념2", "개념3"],
  "difficult_parts": [
    {{
      "content": "이해하기 어려운 내용",
      "why_difficult": "왜 어려운지",
      "help_type": "어떤 도움이 필요한지"
    }}
  ],
  "visualization_opportunities": [
    {{
      "content": "시각화할 내용", 
      "purpose": "overview|detail|comparison|process|concept",
      "why_helpful": "왜 시각화가 도움되는지",
      "user_benefit": "사용자가 얻을 수 있는 이해"
    }}
  ]
}}

JSON만 출력하세요.
"""

def analyze_content_context(report_text: str) -> Dict[str, Any]:
    """보고서의 맥락을 깊이 분석"""
    try:
        prompt = CONTEXT_ANALYSIS_PROMPT.format(report_text=report_text)
        response = llm.invoke(prompt)

        content = response.content.strip()
        start_idx = content.find('{')
        end_idx = content.rfind('}')

        if start_idx != -1 and end_idx != -1:
            json_part = content[start_idx:end_idx+1]
            return json.loads(json_part)
        else:
            return {"error": "JSON 파싱 실패"}

    except Exception as e:
        logger.error(f"컨텍스트 분석 실패: {e}")
        return {"error": str(e)}

SMART_VISUALIZATION_PROMPT = """
당신은 최적의 시각화를 자동으로 생성하는 AI입니다.

**상황:**
- 주제: {main_topic}
- 핵심 개념: {key_concepts}

**시각화 기회:**
{visualization_opportunity}

**목적:** {purpose}
**왜 도움되는지:** {why_helpful}
**사용자 이익:** {user_benefit}

**당신의 임무:**
1. 이 내용을 가장 효과적으로 표현할 시각화 방법을 결정
2. 필요한 데이터나 구조를 추출/생성
3. 실제 시각화 코드나 설정을 만들기

**사용 가능한 도구들:**
- **간단한 차트**: 비교, 트렌드, 비율 → Chart.js 
- **수학/과학**: 함수, 공식, 관계 → Plotly.js + 수학 계산
- **프로세스/흐름**: 단계, 절차 → Mermaid
- **구조화된 정보**: 정확한 데이터 → HTML Table
- **개념 관계/마인드맵**: 분류, 연결, 구조 → Markmap (강력 추천!)
- **창의적 표현**: 위의 것들로 안되면 새로운 방법 제안

**중요**: 
- 정해진 형식에 얽매이지 말고 가장 효과적인 방법을 선택하세요
- **개념 관계, 분류체계, 학습 구조**에는 Markmap을 우선 고려하세요
- 내용에서 실제 데이터를 추출하거나 합리적으로 생성하세요  
- 사용자가 "아, 이래서 시각화가 필요했구나!"라고 느끼도록 하세요

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

**4. Markmap 마인드맵:** (개념 관계/구조에 최적!)
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

def generate_smart_visualization(context: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """스마트하게 최적의 시각화 생성"""
    try:
        prompt = SMART_VISUALIZATION_PROMPT.format(
            main_topic=context.get('main_topic', ''),
            key_concepts=', '.join(context.get('key_concepts', [])),
            visualization_opportunity=opportunity.get('content', ''),
            purpose=opportunity.get('purpose', ''),
            why_helpful=opportunity.get('why_helpful', ''),
            user_benefit=opportunity.get('user_benefit', '')
        )
        
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_part = content[start_idx:end_idx+1]
            return json.loads(json_part)
        else:
            return {"error": "JSON 파싱 실패"}
            
    except Exception as e:
        logger.error(f"스마트 시각화 생성 실패: {e}")
        return {"error": str(e)}

class SmartVisualizationPipeline(Runnable):
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        start = time.time()
        report_text = state.get("report_text", "")
        
        # 1단계: 컨텍스트 분석
        logger.info("🧠 컨텍스트 분석 시작...")
        context = analyze_content_context(report_text)
        
        if "error" in context:
            logger.error(f"컨텍스트 분석 실패: {context['error']}")
            return {**state, "visual_results": []}
        
        logger.info(f"📝 주제: {context.get('main_topic', 'Unknown')}")
        logger.info(f"🔑 핵심 개념: {len(context.get('key_concepts', []))}개")
        logger.info(f"🎯 시각화 기회: {len(context.get('visualization_opportunities', []))}개")
        
        # 2단계: 각 시각화 기회에 대해 스마트 생성
        visual_results = []
        opportunities = context.get('visualization_opportunities', [])
        
        for i, opportunity in enumerate(opportunities):
            logger.info(f"🎨 시각화 {i+1}/{len(opportunities)} 생성 중...")
            
            viz_result = generate_smart_visualization(context, opportunity)
            
            if "error" not in viz_result:
                # 성공한 시각화를 표준 형식으로 변환
                standardized = self.standardize_visualization(viz_result, opportunity)
                if standardized:
                    visual_results.append(standardized)
                    logger.info(f"✅ 시각화 생성 성공: {viz_result.get('type', 'unknown')}")
                else:
                    logger.warning(f"⚠️ 시각화 표준화 실패")
            else:
                logger.error(f"❌ 시각화 생성 실패: {viz_result['error']}")
        
        logger.info(f"🎯 스마트 시각화 파이프라인 완료: {round(time.time() - start, 2)}초")
        logger.info(f"📊 생성된 시각화: {len(visual_results)}개")
        
        return {**state, "visual_results": visual_results}
    
    def standardize_visualization(self, viz_result: Dict[str, Any], opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI가 생성한 시각화를 표준 형식으로 변환"""
        try:
            base = {
                "section": viz_result.get('title', opportunity.get('content', '시각화')[:50]),
                "success": True,
                "insight": viz_result.get('insight', ''),
                "purpose": opportunity.get('purpose', ''),
                "user_benefit": opportunity.get('user_benefit', '')
            }
            
            viz_type = viz_result.get('type', '')
            
            if viz_type == 'chartjs':
                return {
                    **base,
                    "type": "chart",
                    "library": "chartjs",
                    "config": viz_result.get('config', {})
                }
            
            elif viz_type == 'plotly':
                return {
                    **base, 
                    "type": "chart",
                    "library": "plotly",
                    "config": viz_result.get('config', {})
                }
            
            elif viz_type == 'mermaid':
                return {
                    **base,
                    "type": "diagram", 
                    "library": "mermaid",
                    "code": viz_result.get('code', '')
                }
            
            # 🆕 Markmap 케이스 추가
            elif viz_type == 'markmap':
                return {
                    **base,
                    "type": "mindmap",
                    "library": "markmap", 
                    "markdown": viz_result.get('markdown', ''),
                    "title": viz_result.get('title', '마인드맵')
                }
            
            elif viz_type == 'table':
                return {
                    **base,
                    "type": "table",
                    "library": "html", 
                    "data": viz_result.get('data', {})
                }
            
            elif viz_type == 'creative':
                return {
                    **base,
                    "type": "creative",
                    "library": "custom",
                    "method": viz_result.get('method', ''),
                    "description": viz_result.get('description', '')
                }
            
            else:
                return None
                
        except Exception as e:
            logger.error(f"시각화 표준화 오류: {e}")
            return None

# ========== 8. 그래프 구성 ==========
smart_visualization_pipeline = SmartVisualizationPipeline()

def build_smart_graph():
    """스마트 시각화가 적용된 그래프 빌드"""
    builder = StateGraph(state_schema=GraphState)
    
    builder.add_node("caption_node", ToolAgent(extract_youtube_caption_tool, "youtube_url", "caption"))
    builder.add_node("report_node", LangGraphAgentNode(report_agent_executor_runnable, "caption", "report_text"))
    builder.add_node("smart_visual_node", smart_visualization_pipeline)
    builder.add_node("merge_node", MergeTool())
    
    builder.set_entry_point("caption_node")
    builder.add_edge("caption_node", "report_node")
    builder.add_edge("report_node", "smart_visual_node")
    builder.add_edge("smart_visual_node", "merge_node")
    builder.add_edge("merge_node", "__end__")
    
    return builder.compile()

# 컴파일된 그래프
smart_compiled_graph = build_smart_graph()

# ========== 9. 실행 함수 ==========
@traceable(name="smart-youtube-report")
def run_smart_graph(youtube_url: str) -> Dict[str, Any]:
    """스마트 시각화가 적용된 YouTube 보고서 생성"""
    logger.info("\n🚀 [Smart Graph] 실행 시작")
    logger.info(f"🎯 입력 URL: {youtube_url}")
    
    try:
        result = smart_compiled_graph.invoke({"youtube_url": youtube_url})
        logger.info("\n✅ [Smart Graph] 실행 완료")
        logger.info(f"📦 최종 결과: 문단 {result['final_output']['total_paragraphs']}개, 시각화 {result['final_output']['total_visuals']}개")
        return result
    except Exception as e:
        logger.error(f"\n❌ [Smart Graph] 실행 실패: {e}")
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
run_graph = run_smart_graph