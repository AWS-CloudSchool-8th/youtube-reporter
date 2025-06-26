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
from app.core.config import settings
from app.services.user_s3_service import user_s3_service
from app.services.s3_service import s3_service  # S3 ���� �߰�
from app.services.state_manager import state_manager

# ========== 1. ���� ���� ==========
class GraphState(TypedDict):
    job_id: str
    user_id: str
    youtube_url: str
    caption: str
    report_text: str
    visual_blocks: List[dict]
    visual_results: List[dict]
    final_output: dict

# ========== 2. Tool ���� ==========
def extract_youtube_caption_tool(youtube_url: str) -> str:
    """YouTube URL���� �ڸ��� �����ϴ� �Լ�"""
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": "ko"}
    headers = {"Authorization": f"Bearer {settings.VIDCAP_API_KEY}"}
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get("data", {}).get("content", "")
    except Exception as e:
        return f"�ڸ� ���� ����: {str(e)}"

def generate_visuals(prompt: str) -> str:
    """DALL-E�� ����� �̹��� ���� (����� �÷��̽�Ȧ��)"""
    # TODO: DALL-E API ���� �Ǵ� �ٸ� �̹��� ���� ���� ���
    return f"[Visual placeholder for: {prompt[:50]}...]"

def upload_to_s3(file_path: str, object_name: str = None) -> str:
    """S3�� ���� ���ε�"""
    # ������ S3 ���� ���
    return s3_service.upload_file(
        file_path=file_path,
        object_name=object_name,
        content_type="image/png"
    )

def merge_report_and_visuals(report_text: str, visuals: List[dict], youtube_url: str = "") -> dict:
    """������ �ð�ȭ�� ����"""
    paragraphs = [p.strip() for p in report_text.strip().split("\n") if p.strip()]
    n, v = len(paragraphs), len(visuals)
    sections = []

    # ��Ʃ�� ��� ���� �߰�
    if youtube_url:
        sections.append({"type": "youtube", "content": youtube_url})

    # ���ܰ� �ð�ȭ�� ���� ����
    for i, para in enumerate(paragraphs):
        sections.append({"type": "paragraph", "content": para})
        if i < v:
            vis = visuals[i]
            if vis.get("url") and vis.get("type"):
                sections.append({"type": vis["type"], "src": vis["url"]})

    # ���� �ð�ȭ ����� �ִٸ� �߰�
    for j in range(len(paragraphs), v):
        vis = visuals[j]
        if vis.get("url") and vis.get("type"):
            sections.append({"type": vis["type"], "src": vis["url"]})

    return {"format": "json", "youtube_url": youtube_url, "sections": sections}

# ========== 3. ���� ������Ʈ ==========
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """# ��Ʃ�� �ڸ� �м� ���� �ۼ� ������Ʈ

## ���� ����
����� �������� ������ �м����μ�, ��Ʃ�� ������ �ڸ��� ü�����̰� ������ ���� ���·� ��ȯ�ϴ� ������ �����մϴ�.

## ���� �ۼ� ��ħ

#### 1.1 ǥ�� ����
- ���� ����: "[���� ����] �м� ����"

#### 1.2 ����
- �� ���Ǻ� ������ ��ȣ ����
- �ּ� 5�� �̻��� �ֿ� ���� ����

#### 1.3 �ʼ� ���� ����
1. **���� (Executive Summary)**
   - ������ �ٽ� ���� ��� (150-200��)
   - �ֿ� Ű���� �� �ٽ� �޽���

2. **�ֿ� ���� �м�**
   - �ּ� 3�� �̻��� ���� ����
   - �� ���ܴ� 200-300�� �̻�
   - ���� ����: ������ + ��� + �� ����

3. **�ٽ� �λ���Ʈ**
   - ���󿡼� ����Ǵ� �ֿ� �û���
   - �ǹ���/�м��� ����

4. **��� �� ����**
   - ��ü ���� ����
   - ���� ���⼺ �Ǵ� ���� ���ɼ�

5. **�η�**
   - �ֿ� �ο뱸
   - ���� �ڷ� (�ش� ��)

### 2. �ۼ� ����

#### 2.1 ��ü �� ����
- **������ ����**: ����ü�� ����ü�� ���� ��ȯ
- **������ ����**: 3��Ī �������� ����
- **������ ǥ��**: �м���/����Ͻ� ��� Ȱ��
- **���� ����**: ���� �� ����� ��Ȯȭ

#### 2.2 ���� ����
- **�� ���� �ּ� 200�� �̻�**: ����� ����� �м� ����
- **���-���� ����**: �� ������ �ٽ� ��� �� �� ����
- **���� ��� ����**: �ڸ� ������ �ٰŷ� �� �м�
- **�ƶ� ����**: ��� ���� �� ���� ���� �߰�

#### 2.3 ǰ�� ����
- **�ϰ���**: ��ü ������ ������ ���� ����
- **�ϰἺ**: �� ������ ���������ε� ���� ����
- **��Ȯ��**: ���� �ڸ� ���� �ְ� ���� �籸��
- **������**: ��Ȯ�� ����, ������, �ܶ� ����

### 3. ��� ����

���� �������� ������ �ۼ��Ͻÿ�:

```    

## ����
1. ����
2. �ֿ� ���� �м�
3. �ٽ� �λ���Ʈ  
4. ��� �� ����
5. �η�

## 1. ����
[�ٽ� ��� ����]

## 2. �ֿ� ���� �м�
### 2.1 [ù ��° ����]
**���**: [�ٽ� ���� ���]
**�м�**: [�� �м� �� ����]

### 2.2 [�� ��° ����]
**���**: [�ٽ� ���� ���]  
**�м�**: [�� �м� �� ����]

### 2.3 [�� ��° ����]
**���**: [�ٽ� ���� ���]
**�м�**: [�� �м� �� ����]

## 3. �ٽ� �λ���Ʈ
[����� �ֿ� �û���]

## 4. ��� �� ����
[��ü ���� ���� �� ���� ���⼺]

## 5. �η�
[�ֿ� �ο뱸 �� ���� �ڷ�]
```

���� ��Ʃ�� �ڸ��� �����ϸ�, ���� ��ħ�� ���� ������ ���� ���·� ��ȯ�Ͽ� �����ϰڽ��ϴ�."""),
    ("human", "{input}")
])

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_kwargs={"temperature": 0.0, "max_tokens": 4096}
)

def structure_report(caption: str) -> str:
    """�ڸ��� ����ȭ�� ������ ��ȯ"""
    messages = structure_prompt.format_messages(input=caption)
    response = llm.invoke(messages)
    return response.content.strip()

report_agent_executor_runnable = RunnableLambda(structure_report)

# ========== 4. �ð�ȭ ��� ���� ==========
visual_split_prompt = ChatPromptTemplate.from_messages([
    ("system", "�ʴ� ������ ���� ������ JSON �迭�� �ð�ȭ ����� ����ؾ� ��:\n"
     "[{\"type\": \"chart\", \"text\": \"...\"}]\n"
     "type�� �ݵ�� chart, table, image �� �ϳ���,\n"
     "text�� ���� �����̴�. key �̸��� �� type, text�� �״�� ��."),
    ("human", "{input}")
])

def _split_report(report_text: str) -> List[dict]:
    """������ �ð�ȭ ������� ����"""
    response = llm.invoke(visual_split_prompt.format_messages(input=report_text))
    try:
        content = response.content.strip()
        # JSON ��� ����
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
        print(f"�ð�ȭ ��� �Ľ� ����: {e}")
        print(f"���� ����: {response.content[:200]}...")
        return []

class WrapVisualSplitToState(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        report_text = state.get("report_text", "")
        try:
            visual_blocks = _split_report(report_text)
            print(f"[split_node] ���� �ð�: {round(time.time() - start, 2)}��")
            print(f"[split_node] �ð�ȭ ��� ��: {len(visual_blocks)}")
            return {**state, "visual_blocks": visual_blocks}
        except Exception as e:
            print(f"[split_node] ����: {e}")
            return {**state, "visual_blocks": []}

visual_split_agent_wrapped = WrapVisualSplitToState()

# ========== 5. �ð�ȭ ���� ==========
python_tool = PythonREPLTool()

code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", "���� ������ �ð�ȭ�ϴ� **Python �ڵ常** ����ϼ���. �ٸ� ������ ���� ������. �ݵ�� matplotlib.pyplot�� ����ϰ�, ������ ���� plt.savefig('output.png')���� �մϴ�."),
    ("human", "{input}")
])

def dispatch_visual_block_with_python_tool(blocks: List[dict]) -> List[dict]:
    """�ð�ȭ ��ϵ��� ���� �ð�ȭ�� ��ȯ"""
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
                    
                    # ���� ��� ���
                    print(f"?? �ð�ȭ ���� ����: {unique_filename}")
                    
                    # S3 ���ε�
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
            print(f"? �ð�ȭ ���� ����: {e}")
            results.append({"type": t, "text": txt, "url": f"[Error: {e}]"})
    return results

visual_agent_executor_group = RunnableLambda(dispatch_visual_block_with_python_tool)

# ========== 6. Node ���� ==========
class ToolAgent(Runnable):
    def __init__(self, func, field: str, output_field: str = None):
        self.func = func
        self.field = field
        self.output_field = output_field or field

    def invoke(self, state: dict, config=None):
        start = time.time()
        input_value = state.get(self.field)
        result = self.func(input_value)
        
        # Redis�� ���� ����
        job_id = state.get('job_id')
        if job_id:
            try:
                state_manager.save_step_state(job_id, self.field, {self.output_field: result})
            except Exception as e:
                print(f"?? Redis ���� ���� ���� (���õ�): {e}")
        
        execution_time = round(time.time() - start, 2)
        print(f"[{self.field}] ���� �ð�: {execution_time}��")
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
        
        # Redis�� ���� ����
        job_id = state.get('job_id')
        if job_id:
            try:
                state_manager.save_step_state(job_id, self.output_key, {self.output_key: obs})
            except Exception as e:
                print(f"?? Redis ���� ���� ���� (���õ�): {e}")
        
        execution_time = round(time.time() - start, 2)
        print(f"[{self.input_key} �� {self.output_key}] ���� �ð�: {execution_time}��")
        return {**state, self.output_key: obs}

class MergeTool(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        youtube_url = state.get('youtube_url', '')
        final_output = merge_report_and_visuals(
            state.get("report_text", ""), state.get("visual_results", []), str(youtube_url or "")
        )
        print(f"[MergeTool] ���� �ð�: {round(time.time() - start, 2)}��")
        
        # ����� ID�� �۾� ID�� ������ ������ S3�� ����
        user_id = state.get('user_id')
        job_id = state.get('job_id')
        
        # ���� ���� �õ�
        try:
            # ���� JSON�� ���ڿ��� ��ȯ
            report_json = json.dumps(final_output, ensure_ascii=False, indent=2)
            
            # ���� S3�� ���� (user_s3_service ���)
            report_key = f"reports/{user_id}/{job_id}_report.json"
            
            # �ӽ� ���Ϸ� ����
            temp_file = f"report_{job_id}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            
            # S3�� ���ε�
            s3_url = s3_service.upload_file(
                file_path=temp_file,
                object_name=report_key,
                content_type="application/json"
            )
            
            # �ӽ� ���� ����
            os.remove(temp_file)
            
            print(f"? ���� S3 ���� �Ϸ�: {report_key}")
            print(f"?? ���� URL: {s3_url}")
            
            # YouTube ���� ���� ��������
            youtube_info = get_youtube_video_info(youtube_url) if youtube_url else {}
            
            # ��Ÿ������ ���� (YouTube URL �� ���� ���� ����)
            metadata_key = f"metadata/{user_id}/{job_id}_metadata.json"
            metadata = {
                "youtube_url": youtube_url,
                "user_id": user_id,
                "job_id": job_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "report_url": s3_url,
                **youtube_info  # YouTube ���� ���� �߰�
            }
            
            # ��Ÿ������ �ӽ� ���Ϸ� ����
            temp_meta_file = f"metadata_{job_id}.json"
            with open(temp_meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # S3�� ���ε�
            s3_service.upload_file(
                file_path=temp_meta_file,
                object_name=metadata_key,
                content_type="application/json"
            )
            
            # �ӽ� ���� ����
            os.remove(temp_meta_file)
            
        except Exception as e:
            print(f"? ���� S3 ���� ����: {e}")
        
        return {**state, "final_output": final_output}

# ========== 7. FSM ���� ==========
def create_youtube_analysis_graph():
    """YouTube �м��� LangGraph ����"""
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

# ========== 8. ���� Ŭ���� ==========
class LangGraphService:
    def __init__(self):
        self.youtube_graph = create_youtube_analysis_graph()
    
    async def analyze_youtube_with_fsm(self, youtube_url: str, job_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """LangGraph FSM�� ����� YouTube �м�"""
        try:
            print(f"\n?? LangGraph FSM �м� ����: {youtube_url}")
            
            # ���¿� job_id�� user_id �߰�
            initial_state = {
                "youtube_url": youtube_url,
                "job_id": job_id or str(uuid.uuid4()),
                "user_id": user_id or "anonymous"
            }
            
            # ����� �ʱ�ȭ
            if job_id:
                try:
                    state_manager.update_progress(job_id, 0, "�м� ����")
                except Exception as e:
                    print(f"?? Redis ����� ������Ʈ ���� (���õ�): {e}")
            
            result = self.youtube_graph.invoke(initial_state)
            
            # ����� �Ϸ�
            if job_id:
                try:
                    state_manager.update_progress(job_id, 100, "�м� �Ϸ�")
                except Exception as e:
                    print(f"?? Redis ����� ������Ʈ ���� (���õ�): {e}")
            
            print("? LangGraph FSM �м� �Ϸ�")
            return result
        except Exception as e:
            if job_id:
                try:
                    state_manager.update_progress(job_id, -1, f"�м� ����: {str(e)}")
                except Exception as redis_err:
                    print(f"?? Redis ����� ������Ʈ ���� (���õ�): {redis_err}")
            print(f"? LangGraph FSM �м� ����: {e}")
            raise e

def extract_video_id(url: str) -> str:
    """YouTube URL���� video ID ����"""
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
    """YouTube ���� ���� ��������"""
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {}
        
        # YouTube Data API v3 ���
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            print("YouTube API Ű�� �������� �ʾҽ��ϴ�.")
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
            
            # ISO 8601 duration�� �б� ���� ���·� ��ȯ
            duration = content_details.get("duration", "")
            if duration:
                # PT4M13S -> 4:13 ���·� ��ȯ
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
        print(f"YouTube ���� �������� ����: {e}")
        return {
            "youtube_title": f"YouTube Video - {video_id}",
            "youtube_channel": "Unknown Channel",
            "youtube_duration": "Unknown",
            "youtube_thumbnail": f"https://img.youtube.com/vi/{video_id}/default.jpg"
        }

langgraph_service = LangGraphService()