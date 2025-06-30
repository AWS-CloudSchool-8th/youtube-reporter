import os
import json
import uuid
import time
from typing import TypedDict, List, Dict, Any
import boto3
import requests
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.tools import PythonREPLTool
from shared_lib.core.config import settings
from report_service.services.user_s3_service import user_s3_service
from report_service.services.s3_service import s3_service  # S3 서비스 추가
from report_service.services.state_manager import state_manager

# ========== 1. 상태 정의 ==========
class GraphState(TypedDict):
    job_id: str
    user_id: str
    youtube_url: str
    caption: str
    report_text: str
    visual_blocks: List[dict]
    visual_results: List[dict]
    final_output: dict


def call_analyzer(youtube_url: str, user_id: str):
    try:
        response = requests.post(
            "http://analyzer_service:8000/internal/langgraph",
            json={"youtube_url": youtube_url, "user_id": user_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
        
# ========== 2. Tool 정의 ==========
def extract_youtube_caption_tool(youtube_url: str) -> str:
    """YouTube URL에서 자막을 추출하는 함수"""
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": "ko"}
    headers = {"Authorization": f"Bearer {settings.VIDCAP_API_KEY}"}
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get("data", {}).get("content", "")
    except Exception as e:
        return f"자막 추출 실패: {str(e)}"

def generate_visuals(prompt: str) -> str:
    """DALL-E를 사용한 이미지 생성 (현재는 플레이스홀더)"""
    # TODO: DALL-E API 구현 또는 다른 이미지 생성 서비스 사용
    return f"[Visual placeholder for: {prompt[:50]}...]"

def upload_to_s3(file_path: str, object_name: str = None) -> str:
    """S3에 파일 업로드"""
    # 개선된 S3 서비스 사용
    return s3_service.upload_file(
        file_path=file_path,
        object_name=object_name,
        content_type="image/png"
    )

def merge_report_and_visuals(report_text: str, visuals: List[dict], youtube_url: str = "") -> dict:
    """보고서와 시각화를 병합"""
    paragraphs = [p.strip() for p in report_text.strip().split("\n") if p.strip()]
    n, v = len(paragraphs), len(visuals)
    sections = []

    # 유튜브 블록 먼저 추가
    if youtube_url:
        sections.append({"type": "youtube", "content": youtube_url})

    # 문단과 시각화를 교차 삽입
    for i, para in enumerate(paragraphs):
        sections.append({"type": "paragraph", "content": para})
        if i < v:
            vis = visuals[i]
            if vis.get("url") and vis.get("type"):
                sections.append({"type": vis["type"], "src": vis["url"]})

    # 남은 시각화 블록이 있다면 추가
    for j in range(len(paragraphs), v):
        vis = visuals[j]
        if vis.get("url") and vis.get("type"):
            sections.append({"type": vis["type"], "src": vis["url"]})

    return {"format": "json", "youtube_url": youtube_url, "sections": sections}

# ========== 3. 보고서 에이전트 ==========
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """# 유튜브 자막 분석 보고서 작성 프롬프트

## 역할 정의
당신은 전문적인 콘텐츠 분석가로서, 유튜브 영상의 자막을 체계적이고 완전한 보고서 형태로 변환하는 역할을 수행합니다.

## 보고서 작성 지침

#### 1.1 표지 정보
- 보고서 제목: "[영상 제목] 분석 보고서"

#### 1.2 목차
- 각 섹션별 페이지 번호 포함
- 최소 5개 이상의 주요 섹션 구성

#### 1.3 필수 섹션 구성
1. **개요 (Executive Summary)**
   - 영상의 핵심 내용 요약 (150-200자)
   - 주요 키워드 및 핵심 메시지

2. **주요 내용 분석**
   - 최소 3개 이상의 세부 문단
   - 각 문단당 200-300자 이상
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
- **각 문단 최소 200자 이상**: 충분한 설명과 분석 포함
- **요약-설명 구조**: 각 문단은 핵심 요약 후 상세 설명
- **증거 기반 서술**: 자막 내용을 근거로 한 분석
- **맥락 제공**: 배경 정보 및 관련 설명 추가

#### 2.3 품질 기준
- **일관성**: 전체 보고서의 어조와 형식 통일
- **완결성**: 각 섹션이 독립적으로도 이해 가능
- **정확성**: 원본 자막 내용 왜곡 없이 재구성
- **가독성**: 명확한 제목, 부제목, 단락 구분

### 3. 출력 형식

다음 형식으로 보고서를 작성하시오:

```    

## 목차
1. 개요
2. 주요 내용 분석
3. 핵심 인사이트  
4. 결론 및 제언
5. 부록

## 1. 개요
[핵심 요약 내용]

## 2. 주요 내용 분석
### 2.1 [첫 번째 주제]
**요약**: [핵심 내용 요약]
**분석**: [상세 분석 및 설명]

### 2.2 [두 번째 주제]
**요약**: [핵심 내용 요약]  
**분석**: [상세 분석 및 설명]

### 2.3 [세 번째 주제]
**요약**: [핵심 내용 요약]
**분석**: [상세 분석 및 설명]

## 3. 핵심 인사이트
[도출된 주요 시사점]

## 4. 결론 및 제언
[전체 내용 종합 및 향후 방향성]

## 5. 부록
[주요 인용구 및 참고 자료]
```

이제 유튜브 자막을 제공하면, 위의 지침에 따라 완전한 보고서 형태로 변환하여 제시하겠습니다."""),
    ("human", "{input}")
])

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_kwargs={"temperature": 0.0, "max_tokens": 4096}
)

def structure_report(caption: str) -> str:
    """자막을 구조화된 보고서로 변환"""
    messages = structure_prompt.format_messages(input=caption)
    response = llm.invoke(messages)
    return response.content.strip()

report_agent_executor_runnable = RunnableLambda(structure_report)

# ========== 4. 시각화 블록 분해 ==========
visual_split_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 보고서를 다음 형식의 JSON 배열로 시각화 블록을 출력해야 해:\n"
     "[{\"type\": \"chart\", \"text\": \"...\"}]\n"
     "type은 반드시 chart, table, image 중 하나고,\n"
     "text는 설명 문장이다. key 이름은 꼭 type, text를 그대로 써."),
    ("human", "{input}")
])

def _split_report(report_text: str) -> List[dict]:
    """보고서를 시각화 블록으로 분해"""
    response = llm.invoke(visual_split_prompt.format_messages(input=report_text))
    try:
        content = response.content.strip()
        # JSON 블록 추출
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        raw = json.loads(content)
        if not isinstance(raw, list):
            return []
        parsed = []
        for item in raw:
            if isinstance(item, dict) and 'type' in item and 'text' in item:
                parsed.append(item)
        return parsed
    except Exception as e:
        print(f"시각화 블록 파싱 실패: {e}")
        print(f"원본 응답: {response.content[:200]}...")
        return []

class WrapVisualSplitToState(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        report_text = state.get("report_text", "")
        try:
            visual_blocks = _split_report(report_text)
            print(f"[split_node] 실행 시간: {round(time.time() - start, 2)}초")
            print(f"[split_node] 시각화 블록 수: {len(visual_blocks)}")
            return {**state, "visual_blocks": visual_blocks}
        except Exception as e:
            print(f"[split_node] 에러: {e}")
            return {**state, "visual_blocks": []}

visual_split_agent_wrapped = WrapVisualSplitToState()

# ========== 5. 시각화 생성 ==========
python_tool = PythonREPLTool()

code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", "다음 문장을 시각화하는 **Python 코드만** 출력하세요. 다른 설명은 하지 마세요. 반드시 matplotlib.pyplot을 사용하고, 마지막 줄은 plt.savefig('output.png')여야 합니다."),
    ("human", "{input}")
])

def dispatch_visual_block_with_python_tool(blocks: List[dict]) -> List[dict]:
    """시각화 블록들을 실제 시각화로 변환"""
    results = []
    for i, blk in enumerate(blocks):
        if not isinstance(blk, dict):
            continue
        t, txt = blk.get("type"), blk.get("text")
        if not t or not txt:
            continue
        try:
            if t in ["chart", "table"]:
                code = llm.invoke(code_gen_prompt.format_messages(input=txt)).content
                result = python_tool.run(code)
                
                if os.path.exists("output.png"):
                    unique_filename = f"output-{uuid.uuid4().hex[:8]}.png"
                    os.rename("output.png", unique_filename)
                    
                    # 파일 경로 출력
                    print(f"?? 시각화 파일 생성: {unique_filename}")
                    
                    # S3 업로드
                    s3_url = upload_to_s3(unique_filename, object_name=unique_filename)
                    os.remove(unique_filename)
                    url = s3_url
                else:
                    url = f"[Image not created: {result}]"
            elif t == "image":
                url = generate_visuals(txt)
            else:
                url = f"[Unsupported type: {t}]"
            
            results.append({"type": t, "text": txt, "url": url})
        except Exception as e:
            print(f"? 시각화 생성 실패: {e}")
            results.append({"type": t, "text": txt, "url": f"[Error: {e}]"})
    return results

visual_agent_executor_group = RunnableLambda(dispatch_visual_block_with_python_tool)

# ========== 6. Node 정의 ==========
class ToolAgent(Runnable):
    def __init__(self, func, field: str, output_field: str = None):
        self.func = func
        self.field = field
        self.output_field = output_field or field

    def invoke(self, state: dict, config=None):
        start = time.time()
        input_value = state.get(self.field)
        result = self.func(input_value)
        
        # Redis에 상태 저장
        job_id = state.get('job_id')
        if job_id:
            try:
                state_manager.save_step_state(job_id, self.field, {self.output_field: result})
            except Exception as e:
                print(f"?? Redis 상태 저장 실패 (무시됨): {e}")
        
        execution_time = round(time.time() - start, 2)
        print(f"[{self.field}] 실행 시간: {execution_time}초")
        return {**state, self.output_field: result}

class LangGraphAgentNode(Runnable):
    def __init__(self, executor, input_key: str, output_key: str):
        self.executor = executor
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        start = time.time()
        input_val = state[self.input_key]
        result = self.executor.invoke(input_val)
        
        if isinstance(result, dict) and "output" in result:
            obs = result["output"]
        else:
            obs = result
        
        # Redis에 상태 저장
        job_id = state.get('job_id')
        if job_id:
            try:
                state_manager.save_step_state(job_id, self.output_key, {self.output_key: obs})
            except Exception as e:
                print(f"?? Redis 상태 저장 실패 (무시됨): {e}")
        
        execution_time = round(time.time() - start, 2)
        print(f"[{self.input_key} → {self.output_key}] 실행 시간: {execution_time}초")
        return {**state, self.output_key: obs}

class MergeTool(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        youtube_url = state.get('youtube_url', '')
        final_output = merge_report_and_visuals(
            state.get("report_text", ""), state.get("visual_results", []), str(youtube_url or "")
        )
        print(f"[MergeTool] 실행 시간: {round(time.time() - start, 2)}초")
        
        # 사용자 ID와 작업 ID가 있으면 보고서를 S3에 저장
        user_id = state.get('user_id')
        job_id = state.get('job_id')
        
        # 보고서 저장 시도
        try:
            # 보고서 JSON을 문자열로 변환
            report_json = json.dumps(final_output, ensure_ascii=False, indent=2)
            
            # 직접 S3에 저장 (user_s3_service 대신)
            report_key = f"reports/{user_id}/{job_id}_report.json"
            
            # 임시 파일로 저장
            temp_file = f"report_{job_id}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            
            # S3에 업로드
            s3_url = s3_service.upload_file(
                file_path=temp_file,
                object_name=report_key,
                content_type="application/json"
            )
            
            # 임시 파일 삭제
            os.remove(temp_file)
            
            print(f"? 보고서 S3 저장 완료: {report_key}")
            print(f"?? 보고서 URL: {s3_url}")
            
            # YouTube 영상 정보 가져오기
            youtube_info = get_youtube_video_info(youtube_url) if youtube_url else {}
            
            # 메타데이터 저장 (YouTube URL 및 영상 정보 포함)
            metadata_key = f"metadata/{user_id}/{job_id}_metadata.json"
            metadata = {
                "youtube_url": youtube_url,
                "user_id": user_id,
                "job_id": job_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "report_url": s3_url,
                **youtube_info  # YouTube 영상 정보 추가
            }
            
            # 메타데이터 임시 파일로 저장
            temp_meta_file = f"metadata_{job_id}.json"
            with open(temp_meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # S3에 업로드
            s3_service.upload_file(
                file_path=temp_meta_file,
                object_name=metadata_key,
                content_type="application/json"
            )
            
            # 임시 파일 삭제
            os.remove(temp_meta_file)
            
        except Exception as e:
            print(f"? 보고서 S3 저장 실패: {e}")
        
        return {**state, "final_output": final_output}

# ========== 7. FSM 구성 ==========
def create_youtube_analysis_graph():
    """YouTube 분석용 LangGraph 생성"""
    builder = StateGraph(state_schema=GraphState)

    builder.add_node("caption_node", ToolAgent(extract_youtube_caption_tool, "youtube_url", "caption"))
    builder.add_node("report_node", LangGraphAgentNode(report_agent_executor_runnable, "caption", "report_text"))
    builder.add_node("split_node", visual_split_agent_wrapped)
    builder.add_node("visual_node", LangGraphAgentNode(visual_agent_executor_group, "visual_blocks", "visual_results"))
    builder.add_node("merge_node", MergeTool())

    builder.set_entry_point("caption_node")
    for src, dst in [
        ("caption_node", "report_node"),
        ("report_node", "split_node"),
        ("split_node", "visual_node"),
        ("visual_node", "merge_node"),
        ("merge_node", "__end__")
    ]:
        builder.add_edge(src, dst)

    return builder.compile()

# ========== 8. 서비스 클래스 ==========
class LangGraphService:
    def __init__(self):
        self.youtube_graph = create_youtube_analysis_graph()
    
    async def analyze_youtube_with_fsm(self, youtube_url: str, job_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """LangGraph FSM을 사용한 YouTube 분석"""
        try:
            print(f"\n?? LangGraph FSM 분석 시작: {youtube_url}")
            
            # 상태에 job_id와 user_id 추가
            initial_state = {
                "youtube_url": youtube_url,
                "job_id": job_id or str(uuid.uuid4()),
                "user_id": user_id or "anonymous"
            }
            
            # 진행률 초기화
            if job_id:
                try:
                    state_manager.update_progress(job_id, 0, "분석 시작")
                except Exception as e:
                    print(f"?? Redis 진행률 업데이트 실패 (무시됨): {e}")
            
            result = self.youtube_graph.invoke(initial_state)
            
            # 진행률 완료
            if job_id:
                try:
                    state_manager.update_progress(job_id, 100, "분석 완료")
                except Exception as e:
                    print(f"?? Redis 진행률 업데이트 실패 (무시됨): {e}")
            
            print("? LangGraph FSM 분석 완료")
            return result
        except Exception as e:
            if job_id:
                try:
                    state_manager.update_progress(job_id, -1, f"분석 실패: {str(e)}")
                except Exception as redis_err:
                    print(f"?? Redis 진행률 업데이트 실패 (무시됨): {redis_err}")
            print(f"? LangGraph FSM 분석 실패: {e}")
            raise e

def extract_video_id(url: str) -> str:
    """YouTube URL에서 video ID 추출"""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

def get_youtube_video_info(youtube_url: str) -> Dict[str, str]:
    """YouTube 영상 정보 가져오기"""
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {}
        
        # YouTube Data API v3 사용
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            print("YouTube API 키가 설정되지 않았습니다.")
            return {
                "youtube_title": f"YouTube Video - {video_id}",
                "youtube_channel": "Unknown Channel",
                "youtube_duration": "Unknown",
                "youtube_thumbnail": f"https://img.youtube.com/vi/{video_id}/default.jpg"
            }
        
        url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,contentDetails"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get("items") and len(data["items"]) > 0:
            video_info = data["items"][0]
            snippet = video_info.get("snippet", {})
            content_details = video_info.get("contentDetails", {})
            
            # ISO 8601 duration을 읽기 쉬운 형태로 변환
            duration = content_details.get("duration", "")
            if duration:
                # PT4M13S -> 4:13 형태로 변환
                import re
                match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                if match:
                    hours, minutes, seconds = match.groups()
                    hours = int(hours) if hours else 0
                    minutes = int(minutes) if minutes else 0
                    seconds = int(seconds) if seconds else 0
                    
                    if hours > 0:
                        duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration = f"{minutes}:{seconds:02d}"
            
            return {
                "youtube_title": snippet.get("title", f"YouTube Video - {video_id}"),
                "youtube_channel": snippet.get("channelTitle", "Unknown Channel"),
                "youtube_duration": duration or "Unknown",
                "youtube_thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", f"https://img.youtube.com/vi/{video_id}/default.jpg")
            }
        else:
            return {
                "youtube_title": f"YouTube Video - {video_id}",
                "youtube_channel": "Unknown Channel",
                "youtube_duration": "Unknown",
                "youtube_thumbnail": f"https://img.youtube.com/vi/{video_id}/default.jpg"
            }
            
    except Exception as e:
        print(f"YouTube 정보 가져오기 실패: {e}")
        return {
            "youtube_title": f"YouTube Video - {video_id}",
            "youtube_channel": "Unknown Channel",
            "youtube_duration": "Unknown",
            "youtube_thumbnail": f"https://img.youtube.com/vi/{video_id}/default.jpg"
        }

langgraph_service = LangGraphService()