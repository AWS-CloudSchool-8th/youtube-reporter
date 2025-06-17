from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict
from app.agents.youtube import extract_youtube_caption
from app.agents.report_agent import generate_report
from app.agents.visual_split import extract_visual_blocks
from app.utils.merge import merge_report_and_visuals
from app.tools.visual_gen import GenerateVisualAsset
from langchain_core.runnables import RunnableLambda
import asyncio
import traceback

# 상태 정의
class GraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    visual_blocks: List[dict]
    visual_results: List[dict]
    final_output: dict

# Tool 형식 노드
class ToolNode:
    def __init__(self, func, input_key, output_key):
        self.func = func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        try:
            result = self.func(state.get(self.input_key, ""))
            return {**state, self.output_key: result}
        except Exception as e:
            return {**state, self.output_key: f"[Error: {e}]"}

# 시각화 자산 생성기 인스턴스
visual_asset_generator = GenerateVisualAsset()

# 시각화 블록 비동기 실행 함수
async def dispatch_visual_blocks_async(blocks: List[Dict]) -> List[Dict]:
    async def invoke_block(block):
        try:
            vtype = block.get("type", "text")
            text = block.get("text", "")
            return await asyncio.to_thread(visual_asset_generator.invoke, {"type": vtype, "text": text})
        except Exception as e:
            return {
                "type": block.get("type", "text"),
                "text": block.get("text", ""),
                "url": f"[Error: {str(e)}]",
                "trace": traceback.format_exc()
            }
    return await asyncio.gather(*[invoke_block(b) for b in blocks])

# Runnable 래퍼 노드
class RunnableNode:
    def __init__(self, input_key, output_key):
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        blocks = state.get(self.input_key, [])
        results = asyncio.run(dispatch_visual_blocks_async(blocks))
        return {**state, self.output_key: results}

# 병합 노드
class MergeNode:
    def invoke(self, state: dict, config=None):
        try:
            final = merge_report_and_visuals(state.get("report_text", ""), state.get("visual_results", []))
            return {**state, "final_output": final}
        except Exception as e:
            return {**state, "final_output": f"[Error during merge: {e}]"}

# FSM 구성
builder = StateGraph(GraphState)

builder.add_node("caption", ToolNode(extract_youtube_caption, "youtube_url", "caption"))
builder.add_node("report", ToolNode(generate_report, "caption", "report_text"))
builder.add_node("split", ToolNode(extract_visual_blocks, "report_text", "visual_blocks"))
builder.add_node("visual_node", RunnableNode("visual_blocks", "visual_results"))
builder.add_node("merge", MergeNode())

builder.set_entry_point("caption")
builder.add_edge("caption", "report")
builder.add_edge("report", "split")
builder.add_edge("split", "visual_node")
builder.add_edge("visual_node", "merge")
builder.add_edge("merge", "__end__")

graph = builder.compile()

# 실행 함수
def run_graph(youtube_url: str):
    result = graph.invoke({"youtube_url": youtube_url})
    assert "final_output" in result, "Final output is missing"
    return result["final_output"]
