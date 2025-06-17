from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict
from app.agents.youtube import extract_youtube_caption
from app.agents.report_agent import generate_report
from app.agents.visual_split import extract_visual_blocks
from app.utils.merge import merge_report_and_visuals
from app.tools.visual_gen import GenerateVisualAsset
from utils.error_handler import handle_error
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


# Tool 형식 노드 (에러 처리 강화)
class ToolNode:
    def __init__(self, func, input_key, output_key):
        self.func = func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        try:
            input_value = state.get(self.input_key, "")
            result = self.func(input_value)
            return {**state, self.output_key: result}
        except Exception as e:
            error_result = handle_error(
                e,
                f"ToolNode_{self.func.__name__}",
                default_return=""
            )
            return {**state, self.output_key: error_result}


# 시각화 자산 생성기 인스턴스
visual_asset_generator = GenerateVisualAsset()


# 시각화 블록 비동기 실행 함수 (에러 처리 강화)
async def dispatch_visual_blocks_async(blocks: List[Dict]) -> List[Dict]:
    async def invoke_block(block, index):
        try:
            vtype = block.get("type", "text")
            text = block.get("text", "")
            return await asyncio.to_thread(visual_asset_generator.invoke, {"type": vtype, "text": text})
        except Exception as e:
            return handle_error(
                e,
                f"visual_block_{index}",
                {
                    "type": block.get("type", "text"),
                    "text": block.get("text", ""),
                    "url": ""
                }
            )

    if not blocks:
        return []

    # 각 블록에 인덱스 추가하여 에러 추적 개선
    tasks = [invoke_block(block, i) for i, block in enumerate(blocks)]
    return await asyncio.gather(*tasks, return_exceptions=True)


# Runnable 래퍼 노드 (에러 처리 강화)
class RunnableNode:
    def __init__(self, input_key, output_key):
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: dict, config=None):
        try:
            blocks = state.get(self.input_key, [])

            if not isinstance(blocks, list):
                raise ValueError(f"Expected list for {self.input_key}, got {type(blocks)}")

            results = asyncio.run(dispatch_visual_blocks_async(blocks))

            # 예외가 반환된 경우 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = handle_error(
                        result,
                        f"async_visual_block_{i}",
                        {"type": "text", "text": "", "url": ""}
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)

            return {**state, self.output_key: processed_results}

        except Exception as e:
            error_result = handle_error(
                e,
                f"RunnableNode_{self.input_key}",
                []
            )
            return {**state, self.output_key: error_result}


# 병합 노드 (에러 처리 강화)
class MergeNode:
    def invoke(self, state: dict, config=None):
        try:
            report_text = state.get("report_text", "")
            visual_results = state.get("visual_results", [])

            # 입력 검증
            if not report_text or report_text.startswith("[Error"):
                raise ValueError("Invalid report text for merging")

            if not isinstance(visual_results, list):
                raise ValueError(f"Expected list for visual_results, got {type(visual_results)}")

            final = merge_report_and_visuals(report_text, visual_results)
            return {**state, "final_output": final}

        except Exception as e:
            error_result = handle_error(
                e,
                "MergeNode",
                {"format": "json", "sections": [], "error": str(e)}
            )
            return {**state, "final_output": error_result}


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


# 실행 함수 (에러 처리 강화)
def run_graph(youtube_url: str) -> dict:
    """
    메인 그래프 실행 함수

    Args:
        youtube_url: 처리할 YouTube URL

    Returns:
        최종 결과 또는 에러 정보
    """
    try:
        if not youtube_url:
            raise ValueError("YouTube URL is required")

        result = graph.invoke({"youtube_url": youtube_url})

        if "final_output" not in result:
            raise ValueError("Final output is missing from graph result")

        return result["final_output"]

    except Exception as e:
        return handle_error(
            e,
            "run_graph",
            {"format": "json", "sections": [], "error": str(e)}
        )