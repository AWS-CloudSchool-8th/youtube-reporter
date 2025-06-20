import os
import requests
import json
from typing import TypedDict, List, Dict, Any
import boto3
import uuid
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langsmith.run_helpers import traceable
from langchain_experimental.tools import PythonREPLTool
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== 1. 상태 정의 ==========
class GraphState(TypedDict):
    youtube_url: str
    raw_caption: str
    comprehensive_report: str
    content_insights: Dict[str, Any]
    essential_visuals: List[Dict[str, Any]]
    final_document: Dict[str, Any]

# ========== 2. 환경 설정 ==========
load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AWS_REGION = os.getenv("AWS_REGION") or "us-west-2"
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID") or "anthropic.claude-3-5-sonnet-20241022-v2:0"

# 한글 폰트 설정
def setup_korean_font():
    korean_fonts = ['Malgun Gothic', 'AppleGothic', 'NanumGothic']
    for font in korean_fonts:
        try:
            plt.rcParams['font.family'] = font
            plt.rcParams['axes.unicode_minus'] = False
            logger.info(f"한글 폰트 설정 완료: {font}")
            return font
        except:
            continue
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False
    logger.warning("한글 폰트 설정 실패, 기본 폰트 사용")
    return 'sans-serif'

setup_korean_font()

# ========== 3. 핵심 도구들 ==========
def extract_youtube_caption(youtube_url: str) -> str:
    logger.info(f"YouTube 자막 추출 시작: {youtube_url}")
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": "ko"}
    headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
    response = requests.get(api_url, params=params, headers=headers)
    response.raise_for_status()
    caption = response.json().get("data", {}).get("content", "")
    logger.info(f"자막 추출 완료: {len(caption)}자")
    return caption

def upload_to_s3(file_path: str, object_name: str = None) -> str:
    logger.info(f"S3 업로드 시작: {file_path}")
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        bucket_name = os.getenv("S3_BUCKET_NAME")
        object_name = object_name or os.path.basename(file_path)
        s3.upload_file(file_path, bucket_name, object_name)
        url = f"https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        logger.info(f"S3 업로드 완료: {url}")
        return url
    except Exception as e:
        logger.error(f"S3 업로드 실패: {e}")
        return f"[S3 Upload Error: {e}]"

# ========== 4. LLM 설정 ==========
llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name=AWS_REGION),
    model_id=BEDROCK_MODEL_ID,
    model_kwargs={"temperature": 0.1, "max_tokens": 4096}
)

# ========== 5. 포괄적 보고서 생성 ==========
comprehensive_report_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 YouTube 영상을 보지 않고도 완전히 이해할 수 있는 포괄적 보고서를 작성하는 전문가입니다.

목표: 독자가 YouTube 영상을 보지 않아도 모든 핵심 내용을 파악할 수 있도록 상세한 보고서 작성

작성 규칙:
1. **완전성**: 영상의 모든 중요한 정보 포함
2. **구조화**: 논리적 흐름으로 섹션 구분
3. **구체성**: 추상적 표현보다 구체적 내용 우선
4. **맥락 제공**: 배경 정보와 연결점 명시
5. **길이**: 800-1200자 (충분히 상세하게)

보고서 구조:
# [영상 제목 또는 주제]

## 핵심 요약
[3-4문장으로 전체 내용 요약]

## 주요 내용
### [첫 번째 핵심 주제]
[상세 설명, 구체적 사례, 수치 데이터 포함]

### [두 번째 핵심 주제]
[상세 설명, 비교/대조 내용 포함]

### [세 번째 핵심 주제]
[프로세스, 단계, 방법론 등 포함]

## 핵심 인사이트
[결론, 시사점, 실용적 적용 방안]

## 추가 정보
[언급된 참고자료, 관련 개념, 후속 내용 등]"""),
    ("human", "YouTube 자막 내용:\n{caption}")
])

def create_comprehensive_report(caption: str) -> str:
    logger.info("포괄적 보고서 생성 시작")
    messages = comprehensive_report_prompt.format_messages(caption=caption)
    response = llm.invoke(messages)
    report = response.content.strip()
    logger.info(f"보고서 생성 완료: {len(report)}자")
    return report

# ========== 6. 내용 분석 및 인사이트 추출 ==========
content_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 보고서를 분석해서 시각화가 꼭 필요한 핵심 요소만 식별하는 전문가입니다.

분석 기준:
1. **데이터 중심**: 구체적 수치, 통계, 비율이 있는가?
2. **비교 요소**: 여러 항목을 비교/대조하는 내용인가?
3. **프로세스**: 단계별 절차나 흐름이 있는가?
4. **관계성**: 복잡한 개념 간 연결관계가 있는가?
5. **핵심성**: 전체 내용 이해에 필수적인가?

다음 JSON 형태로 출력:
{{
  "key_data_points": [
    {{"content": "구체적 데이터 내용", "importance": "high/medium", "visualization_need": "essential/helpful/unnecessary"}}
  ],
  "comparison_elements": [
    {{"items": ["비교대상1", "비교대상2"], "criteria": "비교기준", "importance": "high/medium"}}
  ],
  "process_flows": [
    {{"name": "프로세스명", "steps": ["단계1", "단계2"], "complexity": "high/medium/low"}}
  ],
  "concept_relationships": [
    {{"central_concept": "중심개념", "related_concepts": ["관련개념들"], "relationship_type": "hierarchy/network/flow"}}
  ],
  "visualization_priority": {{
    "essential": ["꼭 필요한 시각화 요소들"],
    "helpful": ["도움이 되는 시각화 요소들"],
    "skip": ["불필요한 요소들"]
  }}
}}"""),
    ("human", "보고서 내용:\n{report}")
])

def analyze_content_insights(report: str) -> Dict[str, Any]:
    logger.info("내용 분석 시작")
    messages = content_analysis_prompt.format_messages(report=report)
    response = llm.invoke(messages)
    try:
        analysis = json.loads(response.content)
        logger.info("내용 분석 완료")
        return analysis
    except Exception as e:
        logger.error(f"내용 분석 실패: {e}")
        return {"error": "분석 실패", "raw_response": response.content}

# ========== 7. 필수 시각화 요소 선별 ==========
essential_visual_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 보고서 이해에 꼭 필요한 시각화만 선별하는 전문가입니다.

선별 기준 (모두 만족해야 함):
1. **필수성**: 이 시각화 없이는 내용 이해가 어려운가?
2. **명확성**: 텍스트보다 시각화가 훨씬 명확한가?
3. **데이터성**: 구체적 데이터나 구조가 있는가?

시각화 타입별 적용:
- **차트**: 수치 비교, 트렌드, 분포 (3개 이상 데이터 포인트)
- **표**: 구조화된 정보, 다중 속성 비교
- **다이어그램**: 복잡한 프로세스, 시스템 구조
- **마인드맵**: 개념 간 복잡한 관계성

최대 2-3개만 선별하여 JSON 배열로 출력:
[
  {{
    "type": "chart|table|diagram|mindmap",
    "title": "시각화 제목",
    "purpose": "왜 꼭 필요한지 이유",
    "data_source": "보고서에서 추출할 구체적 데이터",
    "chart_type": "bar|line|pie|flow|hierarchy (해당시)",
    "priority_score": 1-10,
    "section": "해당 보고서 섹션"
  }}
]"""),
    ("human", "보고서:\n{report}\n\n분석 결과:\n{insights}")
])

def select_essential_visuals(report: str, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    logger.info("필수 시각화 선별 시작")
    
    # 간단한 테스트 데이터로 대체 (임시)
    test_visuals = [
        {
            "type": "chart",
            "title": "기본 삼각함수 그래프 비교",
            "purpose": "삼각함수의 기본 형태와 주기를 시각적으로 비교",
            "data_source": "sin x, cos x 함수의 그래프",
            "chart_type": "line",
            "priority_score": 10,
            "section": "주요 내용"
        },
        {
            "type": "chart",
            "title": "단위원과 삼각함수의 관계",
            "purpose": "삼각함수 값들이 단위원에서 어떻게 도출되는지 설명",
            "data_source": "단위원에서의 좌표값",
            "chart_type": "scatter",
            "priority_score": 9,
            "section": "핵심 인사이트"
        }
    ]
    
    logger.info(f"시각화 선별 완료: {len(test_visuals)}개")
    return test_visuals

# ========== 8. 고품질 시각화 생성 ==========
def generate_high_quality_visual(requirement: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"시각화 생성 시작: {requirement.get('title', 'Unknown')}")
    
    try:
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        
        chart_type = requirement.get('chart_type', 'bar')
        title = requirement.get('title', '시각화')
        
        if 'sin' in title.lower() or '삼각함수' in title:
            x = np.linspace(-2*np.pi, 2*np.pi, 1000)
            ax.plot(x, np.sin(x), label='sin(x)', linewidth=2, color='#FF6B6B')
            ax.plot(x, np.cos(x), label='cos(x)', linewidth=2, color='#4ECDC4')
            ax.set_ylim(-1.5, 1.5)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            ax.legend()
            ax.set_xlabel('x')
            ax.set_ylabel('y')
        elif chart_type == 'bar':
            categories = ['카테고리 A', '카테고리 B', '카테고리 C', '카테고리 D']
            values = [23, 45, 56, 78]
            ax.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
            ax.set_ylabel('값')
        elif chart_type == 'line':
            x = np.arange(2020, 2025)
            y = [100, 120, 140, 160, 180]
            ax.plot(x, y, marker='o', linewidth=2, markersize=8, color='#45B7D1')
            ax.set_xlabel('연도')
            ax.set_ylabel('값')
        else:
            x = np.arange(5)
            y = np.random.randint(10, 100, 5)
            ax.bar(x, y, color='#45B7D1')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('output.png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info("matplotlib로 직접 이미지 생성 완료")
        
        if os.path.exists("output.png"):
            file_size = os.path.getsize("output.png")
            logger.info(f"output.png 파일 크기: {file_size} bytes")
            
            unique_filename = f"visual-{uuid.uuid4().hex[:8]}.png"
            os.rename("output.png", unique_filename)
            
            s3_url = upload_to_s3(unique_filename, object_name=unique_filename)
            
            if os.path.exists(unique_filename):
                os.remove(unique_filename)
            
            success = not s3_url.startswith("[S3 Upload Error:")
            
            visual_result = {
                "type": requirement.get("type"),
                "title": requirement.get("title"),
                "url": s3_url,
                "purpose": requirement.get("purpose"),
                "section": requirement.get("section"),
                "success": success
            }
            logger.info(f"시각화 생성 완료: success={success}, url={s3_url}")
            return visual_result
        else:
            logger.error("output.png 파일이 생성되지 않음")
            return {
                "type": requirement.get("type"),
                "title": requirement.get("title"),
                "url": "[이미지 생성 실패]",
                "error": "Image generation failed",
                "success": False
            }
            
    except Exception as e:
        logger.error(f"시각화 생성 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return {
            "type": requirement.get("type", "unknown"),
            "title": requirement.get("title", "제목 없음"),
            "url": f"[오류: {str(e)}]",
            "error": str(e),
            "success": False
        }

def process_essential_visuals(requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(f"시각화 처리 시작: {len(requirements)}개")
    results = []
    for i, req in enumerate(requirements):
        logger.info(f"시각화 {i+1}/{len(requirements)} 처리 중: {req.get('title', 'Unknown')}")
        if req.get('priority_score', 0) >= 5:
            visual = generate_high_quality_visual(req)
            results.append(visual)
        else:
            logger.info(f"우선순위 낮음으로 스킵: {req.get('priority_score', 0)}")
    
    logger.info(f"시각화 처리 완료: {len(results)}개")
    return results

# ========== 9. 최종 문서 구성 ==========
def create_final_document(report: str, visuals: List[Dict[str, Any]]) -> Dict[str, Any]:
    logger.info("최종 문서 구성 시작")
    sections = []
    report_lines = report.split('\n')
    current_section = []
    
    for line in report_lines:
        if line.strip().startswith('#'):
            if current_section:
                sections.append({
                    "type": "text",
                    "content": '\n'.join(current_section).strip()
                })
                current_section = []
            sections.append({
                "type": "header",
                "content": line.strip()
            })
        else:
            current_section.append(line)
    
    if current_section:
        sections.append({
            "type": "text", 
            "content": '\n'.join(current_section).strip()
        })
    
    successful_visuals = [v for v in visuals if v.get('success', False)]
    logger.info(f"성공한 시각화: {len(successful_visuals)}개")
    
    for i, visual in enumerate(successful_visuals):
        insert_pos = min((i + 1) * 3, len(sections))
        sections.insert(insert_pos, {
            "type": "visual",
            "data": visual
        })
    
    final_doc = {
        "format": "comprehensive_report",
        "sections": sections,
        "visual_count": len(successful_visuals),
        "total_sections": len(sections)
    }
    
    logger.info(f"최종 문서 구성 완료: {len(sections)}개 섹션, {len(successful_visuals)}개 시각화")
    return final_doc

# ========== 10. 노드 클래스 ==========
class StateNode(Runnable):
    def __init__(self, func, input_key: str, output_key: str):
        self.func = func
        self.input_key = input_key
        self.output_key = output_key
    
    def invoke(self, state: dict, config=None):
        input_value = state.get(self.input_key)
        result = self.func(input_value)
        return {**state, self.output_key: result}

class MultiInputNode(Runnable):
    def __init__(self, func, input_keys: List[str], output_key: str):
        self.func = func
        self.input_keys = input_keys
        self.output_key = output_key
    
    def invoke(self, state: dict, config=None):
        inputs = [state.get(key) for key in self.input_keys]
        result = self.func(*inputs)
        return {**state, self.output_key: result}

# ========== 11. 그래프 구성 ==========
builder = StateGraph(GraphState)

builder.add_node("extract_caption", StateNode(extract_youtube_caption, "youtube_url", "raw_caption"))
builder.add_node("create_report", StateNode(create_comprehensive_report, "raw_caption", "comprehensive_report"))
builder.add_node("analyze_insights", StateNode(analyze_content_insights, "comprehensive_report", "content_insights"))
builder.add_node("select_visuals", MultiInputNode(select_essential_visuals, ["comprehensive_report", "content_insights"], "essential_visuals"))
builder.add_node("generate_visuals", StateNode(process_essential_visuals, "essential_visuals", "essential_visuals"))
builder.add_node("create_document", MultiInputNode(create_final_document, ["comprehensive_report", "essential_visuals"], "final_document"))

builder.set_entry_point("extract_caption")
builder.add_edge("extract_caption", "create_report")
builder.add_edge("create_report", "analyze_insights")
builder.add_edge("analyze_insights", "select_visuals")
builder.add_edge("select_visuals", "generate_visuals")
builder.add_edge("generate_visuals", "create_document")
builder.add_edge("create_document", "__end__")

compiled_graph = builder.compile()

# ========== 12. 실행 함수 ==========
@traceable(name="youtube-comprehensive-report")
def generate_youtube_report(youtube_url: str) -> Dict[str, Any]:
    logger.info(f"YouTube 보고서 생성 시작: {youtube_url}")
    result = compiled_graph.invoke({"youtube_url": youtube_url})
    final_doc = result.get("final_document", {})
    logger.info("YouTube 보고서 생성 완료")
    return final_doc

def run_graph(youtube_url: str) -> Dict[str, Any]:
    logger.info(f"run_graph 호출: {youtube_url}")
    result = compiled_graph.invoke({"youtube_url": youtube_url})
    final_output = {"final_output": result.get("final_document", {})}
    logger.info("run_graph 완료")
    return final_output