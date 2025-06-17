from langgraph.graph import StateGraph
from typing import TypedDict, List
from app.agents.youtube import extract_youtube_caption
from app.agents.report_agent import generate_report
from app.agents.visual_split import extract_visual_blocks
from app.tools.code_exec import generate_visual_from_code
from app.tools.visual_gen import generate_dalle_image
from app.utils.merge import merge_report_and_visuals
import asyncio

# 상태 정의
class GraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    visual_blocks: List[dict]
    visual_results: List[dict]
    final_output: dict

# 시각화 처리 함수
async def process_visual_block(block):
    t = block.get("type")
    text = block.get("text")

    handler = {
        "chart": lambda: {"type": t, "text": text, "url": generate_visual_from_code(text)},
        "table": lambda: {"type": t, "text": text, "url": generate_visual_from_code(text)},
        "image": lambda: generate_dalle_image(text, t)
    }.get(t, lambda: {"type": t, "text": text, "url": "[Unsupported type]"})

    return await handler()

# ========== LangGraph용 노드 ==========

# Tool 형식 노드
class ToolNode:
    def __init__(self, func, input_key, output_key):
        self.func = func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        result = self.func(state[self.input_key])
        return {**state, self.output_key: result}

# 시각화 블록 비동기 실행 노드
class VisualNode:
    def invoke(self, state: dict, config=None):
        blocks = state["visual_blocks"]
        results = asyncio.run(asyncio.gather(*[process_visual_block(b) for b in blocks]))
        return {**state, "visual_results": results}

# 병합 노드
class MergeNode:
    def invoke(self, state: dict, config=None):
        final = merge_report_and_visuals(state["report_text"], state["visual_results"])
        return {**state, "final_output": final}

# ========== FSM 구성 ==========

builder = StateGraph(GraphState)

builder.add_node("caption", ToolNode(extract_youtube_caption, "youtube_url", "caption"))
builder.add_node("report", ToolNode(generate_report, "caption", "report_text"))
builder.add_node("split", ToolNode(extract_visual_blocks, "report_text", "visual_blocks"))
builder.add_node("visual", VisualNode())
builder.add_node("merge", MergeNode())

builder.set_entry_point("caption")
builder.add_edge("caption", "report")
builder.add_edge("report", "split")
builder.add_edge("split", "visual")
builder.add_edge("visual", "merge")
builder.add_edge("merge", "__end__")

graph = builder.compile()

# 실행 함수
def run_graph(youtube_url: str):
    return graph.invoke({"youtube_url": youtube_url})
