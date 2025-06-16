import os
import requests
import json
from typing import TypedDict, List

import boto3
import uuid
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langsmith.run_helpers import traceable
from langchain_experimental.tools import PythonREPLTool

# ========== 1. 상태 정의 ==========
class GraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    visual_blocks: List[dict]
    visual_results: List[dict]
    final_output: dict

# ========== 2. 환경 변수 로딩 ==========
load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ========== 3. Tool 정의 ==========
def extract_youtube_caption_tool(youtube_url: str) -> str:
    api_url = "https://vidcap.xyz/api/v1/youtube/caption"
    params = {"url": youtube_url, "locale": "ko"}
    headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
    response = requests.get(api_url, params=params, headers=headers)
    response.raise_for_status()
    return response.json().get("data", {}).get("content", "")

def generate_visuals(description: str, vtype: str = "diagram") -> str:
    dalle_api = "https://api.openai.com/v1/images/generations"
    dalle_prompt = make_image_prompt(description, vtype)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": dalle_prompt,
        "n": 1,
        "size": "1024x1024"
    }
    response = requests.post(dalle_api, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("data", [{}])[0].get("url", "[Image generation failed]")

def upload_to_s3(file_path: str, object_name: str = None) -> str:
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    bucket_name = os.getenv("S3_BUCKET_NAME")
    object_name = object_name or os.path.basename(file_path)

    s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={"ACL": "public-read"})

    return f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

'''
def merge_report_and_visuals(report_text: str, visuals: List[dict]) -> dict:
    sections = [{"type": "paragraph", "content": report_text}]
    for v in visuals:
        if not v.get("url") or not v.get("type"):
            continue
        sections.append({"type": v["type"], "src": v["url"]})
    return {"format": "json", "sections": sections}
'''
def merge_report_and_visuals(report_text: str, visuals: List[dict]) -> dict:
    paragraphs = [p.strip() for p in report_text.strip().split("\n") if p.strip()]
    n, v = len(paragraphs), len(visuals)
    sections = []

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

    return {"format": "json", "sections": sections}


# ========== 4. 보고서 에이전트 ==========
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 유튜브 자막을 바탕으로 논리적이고 풍부한 설명이 담긴 전문 보고서를 작성하는 고급 AI야. 다음 지침을 반드시 따르세요:\n\n"
     "1. 전체 자막 내용을 기반으로 주제별로 핵심 흐름을 재구성하고, 문단 단위로 재배열해.\n"
     "2. 단순한 자막 나열을 피하고, 정보를 통합하여 하나의 자연스러운 글로 이어줘.\n"
     "3. 각 문단은 다음의 구조를 따르도록 해:\n"
     "   - 🔹 주제 요약 (문단의 중심 메시지)\n"
     "   - 🔹 개념 설명 (핵심 개념이나 이론을 정확하고 쉽게 설명)\n"
     "   - 🔹 예시 및 비유 (실제 사례나 독자가 이해하기 쉬운 비유 사용)\n"
     "4. 전체 문단은 최소 4개 이상, 전체 길이는 500자 이상, 중복 없는 내용으로 구성해.\n"
     "5. 설명은 **전문가가 초심자에게 가르치듯 자세하고 친절하게 써줘. 너무 간단하거나 딱딱한 어투는 피하고, 부드러운 설명체로 작성해.\n"
     "6. 각 문단은 제목 없이 자연스럽게 이어지되, 보고서처럼 논리적 구조를 유지해.\n"
     "7. 필요하다면 문맥을 보완해서 원래 자막에 없던 부분도 유추해서 추가해도 좋아.\n\n"
     "마지막으로, 하나의 완결된 보고서처럼 구성해줘. 중간중간 끊기는 느낌 없이 부드럽게 연결돼야 해."),
    ("human", "{input}")
])

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name="us-west-2"),
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 4096}
)

visual_prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 이미지 생성 전문가입니다. 주어진 설명을 보고, "
     "{type} 형태의 시각화를 만들기 위한 DALL·E 프롬프트를 작성해 주세요. "
     "항상 최소한의 스타일 가이드(예: 검은 실선, 흰 배경, 핵심 레이블)를 포함하고, "
     "내용을 명확히 전달할 수 있도록 작성해야 합니다."),
    ("human", "{description}")
])

def make_image_prompt(description: str, vtype: str) -> str:
    msgs = visual_prompt_template.format_messages(description=description, type=vtype)
    return llm.invoke(msgs).content.strip()

def structure_report(caption: str) -> str:
    messages = structure_prompt.format_messages(input=caption)
    response = llm.invoke(messages)
    return response.content.strip()

report_agent_executor_runnable = RunnableLambda(structure_report)

# ========== 5. 시각화 블록 분해 ==========
visual_split_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 보고서를 다음 형식의 JSON 배열로 시각화 블록을 출력해야 해:\n"
     "[{{\"type\": \"chart\", \"text\": \"...\"}}]\n"
     "type은 반드시 chart, table, image 중 하나고,\n" # diagram, mindmap 추가 예정
     "text는 설명 문장이다. key 이름은 꼭 type, text를 그대로 써."),
    ("human", "{input}")
])

def _split_report(report_text: str) -> List[dict]:
    response = llm.invoke(visual_split_prompt.format_messages(input=report_text))
    try:
        raw = json.loads(response.content)
        print("🧪 raw LLM 응답:", raw)
        if not isinstance(raw, list):
            print("❌ LLM 응답이 리스트 아님")
            return []
        parsed = []
        for i, item in enumerate(raw):
            if isinstance(item, dict):
                parsed.append(item)
            elif isinstance(item, str):
                try:
                    parsed_item = json.loads(item)
                    parsed.append(parsed_item)
                    print(f"✅ item {i} 파싱 성공: {parsed_item}")
                except Exception as e:
                    print(f"❌ item {i} 파싱 실패: {item}, 오류: {e}")
        return parsed
    except Exception as e:
        print("❌ 전체 파싱 실패:", e)
        return []

class WrapVisualSplitToState(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        report_text = state.get("report_text", "")
        visual_blocks = _split_report(report_text)
        print(f"[split_node] 실행 시간: {round(time.time() - start, 2)}초")
        return {**state, "visual_blocks": visual_blocks}

visual_split_agent_wrapped = WrapVisualSplitToState()

# ========== 6. 시각화 생성 ==========
python_tool = PythonREPLTool()

code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", "다음 문장을 시각화하는 **Python 코드만** 출력하세요. 다른 설명은 하지 마세요. 반드시 matplotlib.pyplot 또는 pandas를 사용하고, 마지막 줄은 plt.savefig('output.png') 또는 df.to_csv('output.csv')여야 합니다."),
    ("human", "{input}")
])

def dispatch_visual_block_with_python_tool(blocks: List[dict]) -> List[dict]:
    results = []
    for i, blk in enumerate(blocks):
        print(f"\n🔍 블록 {i} 내용 확인: {blk} (타입: {type(blk)})")
        if isinstance(blk, str):
            blk = blk.strip()
            if not blk:
                print(f"⚠️ 빈 문자열 블록 무시됨.")
                continue
            try:
                blk = json.loads(blk)
                print(f"✅ 문자열 파싱 성공: {blk}")
            except Exception as e:
                print(f"❌ 문자열 파싱 실패: {e} | 원본: {blk}")
                continue
        if not isinstance(blk, dict):
            print(f"❌ dict 타입 아님. blk = {blk}")
            continue
        t, txt = blk.get("type"), blk.get("text")
        print(f"🧩 type: {t}, text: {txt}")
        if not t or not txt:
            continue
        try:
            if t in ["chart", "table"]:
                code = llm.invoke(code_gen_prompt.format_messages(input=txt)).content
                print("🧪 생성된 코드:\n", code)
                result = python_tool.run(code)
                print("🛠️ 실행 결과:", result)

                if os.path.exists("output.png"):
                    # ✅ 고유 파일명 생성
                    unique_filename = f"output-{uuid.uuid4().hex[:8]}.png"
                    os.rename("output.png", unique_filename)

                    # ✅ S3에 업로드
                    s3_url = upload_to_s3(unique_filename, object_name=unique_filename)
                    
                    # ✅ 로컬 파일 삭제
                    os.remove(unique_filename)

                    url = s3_url
                else:
                    url = f"[Image not created: {result}]"

            elif t == "image":
                url = generate_visuals(txt, vtype=t)

            else:
                url = f"[Unsupported type: {t}]"

            results.append({"type": t, "text": txt, "url": url})

        except Exception as e:
            results.append({"type": t, "text": txt, "url": f"[Error: {e}]"})
    return results

visual_agent_executor_group = RunnableLambda(dispatch_visual_block_with_python_tool)

# ========== 7. Node 정의 ==========
class ToolAgent(Runnable):
    def __init__(self, func, field: str, output_field: str | None = None):
        self.func = func
        self.field = field
        self.output_field = output_field or field

    def invoke(self, state: dict, config=None):
        start = time.time()
        # print(f"\n🔧 [ToolAgent] 실행 - field: {self.field}")
        input_value = state.get(self.field)
        # print(f"📥 입력값: {input_value}")
        result = self.func(input_value)
        # print(f"📤 출력값: {result}")
        print(f"[{self.field}] 실행 시간: {round(time.time() - start, 2)}초")
        return {**state, self.output_field: result}


class LangGraphAgentNode(Runnable):
    def __init__(self, executor, input_key: str, output_key: str):
        self.executor = executor
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        start = time.time()
        # print(f"\n🧠 [LangGraphAgentNode] 실행 - input_key: {self.input_key}")
        input_val = state[self.input_key]
        # print(f"📥 입력값: {input_val}")
        result = self.executor.invoke(input_val)

        if isinstance(result, dict) and "output" in result:
            obs = result["output"]
        else:
            obs = result

        # print(f"📤 출력값: {obs}")
        print(f"[{self.input_key} → {self.output_key}] 실행 시간: {round(time.time() - start, 2)}초")
        return {**state, self.output_key: obs}


class MergeTool(Runnable):
    def invoke(self, state: dict, config=None):
        start = time.time()
        # print("\n🧩 [MergeTool] 실행")
        # print(f"📥 보고서: {state.get('report_text')}")
        # print(f"📥 시각화: {state.get('visual_results')}")
        final_output = merge_report_and_visuals(
            state.get("report_text", ""), state.get("visual_results", [])
        )
        # print(f"📤 최종 결과: {final_output}")
        print(f"[MergeTool] 실행 시간: {round(time.time() - start, 2)}초")
        return {**state, "final_output": final_output}


# ========== 8. FSM 구성 ==========
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

compiled_graph = builder.compile()

# ========== 9. 실행 함수 ==========
@traceable(name="youtube-report-fsm")
def run_graph(youtube_url: str):
    print("\n🚀 [run_graph] 실행 시작")
    print(f"🎯 입력 URL: {youtube_url}")
    result = compiled_graph.invoke({"youtube_url": youtube_url})
    print("\n✅ [run_graph] 실행 완료")
    print(f"📦 최종 상태: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result