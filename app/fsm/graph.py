from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.redis import RedisSaver
from app.fsm.types import ReportState
from app.fsm.nodes import (
    extract_caption, analyze_paragraphs,
    generate_visuals, finalize_report
)

saver = RedisSaver.from_conn_string("redis://localhost:6379")
builder = StateGraph(ReportState)
builder.add_node("extract_caption", extract_caption)
builder.add_node("analyze", analyze_paragraphs)
builder.add_node("visuals", generate_visuals)
builder.add_node("finish", finalize_report)
builder.add_edge("extract_caption", "analyze")
builder.add_edge("analyze", "visuals")
builder.add_edge("visuals", "finish")
graph = builder.compile(checkpointer=saver)