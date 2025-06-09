from functools import partial
from contextlib import contextmanager

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.redis import RedisSaver

from app.fsm.types import ReportState
from app.fsm.nodes import (
    extract_caption,
    analyze_paragraphs,
    generate_visuals,
    finalize_report,
)
from app.agents.visual_agent import VisualAgent

# 🧠 Claude 3.5 Sonnet 기반 VisualAgent 생성
agent = VisualAgent(
    region="ap-northeast-2",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
)

# 🧱 StateGraph 구성
builder = StateGraph(ReportState)

builder.add_node("extract_caption", extract_caption)
builder.add_node("analyze", partial(analyze_paragraphs, agent=agent))
builder.add_node("visuals", partial(generate_visuals, agent=agent))
builder.add_node("finish", finalize_report)

builder.add_edge(START, "extract_caption")
builder.add_edge("extract_caption", "analyze")
builder.add_edge("analyze", "visuals")
builder.add_edge("visuals", "finish")
builder.add_edge("finish", END)

# 🔧 LangGraph 체크포인트 설정 + 인덱스 생성까지
@contextmanager
def get_graph():
    with RedisSaver.from_conn_string("redis://localhost:6379") as saver:
        # ❗ 인덱스가 없으면 생성 (overwrite=False로 안전하게)
        saver.checkpoints_index.create(overwrite=False)

        graph = builder.compile(checkpointer=saver)
        yield graph

