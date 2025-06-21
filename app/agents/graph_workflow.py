# app/agents/graph_workflow.py
from typing import TypedDict
from langgraph.graph import StateGraph
from .caption_agent import CaptionAgent
from .summary_agent import SummaryAgent
from .report_agent import ReportAgent


class GraphState(TypedDict):
    youtube_url: str
    caption: str
    summary: str
    report_result: dict
    final_output: dict


class YouTubeReporterWorkflow:
    def __init__(self):
        self.caption_agent = CaptionAgent()
        self.summary_agent = SummaryAgent()
        self.report_agent = ReportAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(state_schema=GraphState)

        # 노드 추가
        builder.add_node("caption_node", self.caption_agent)
        builder.add_node("summary_node", self.summary_agent)
        builder.add_node("report_node", self.report_agent)
        builder.add_node("finalize_node", self._finalize_result)

        # 엣지 연결 - 자막 추출 → 요약 → 보고서 생성 → 최종화
        builder.set_entry_point("caption_node")
        builder.add_edge("caption_node", "summary_node")
        builder.add_edge("summary_node", "report_node")
        builder.add_edge("report_node", "finalize_node")
        builder.add_edge("finalize_node", "__end__")

        return builder.compile()

    def _finalize_result(self, state: dict, config=None):
        """최종 결과 정리"""
        report_result = state.get("report_result", {})
        summary = state.get("summary", "")
        
        # 요약 정보를 최종 결과에 포함
        if summary and isinstance(report_result, dict):
            report_result["summary"] = summary
            
        return {**state, "final_output": report_result}

    def process(self, youtube_url: str, summary_level: str = "detailed") -> dict:
        """YouTube URL을 처리하여 결과 반환"""
        initial_state = {
            "youtube_url": youtube_url,
            "summary_level": summary_level
        }
        result = self.graph.invoke(initial_state)
        return result.get("final_output", {})