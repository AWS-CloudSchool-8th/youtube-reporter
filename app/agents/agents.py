from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_aws import ChatBedrock
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate

from app.llm.claude_bedrock_custom import get_bedrock_client
from app.agents.tools import caption_tool, visual_tool, structure_report

# ──────────────────────────────────────────────────────────────
# 공통 LLM
# ──────────────────────────────────────────────────────────────
llm = ChatBedrock(
    client=get_bedrock_client(),
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs={
        "temperature": 0.0,
        "max_tokens": 4096,
        "stop_sequences": ["Final Answer:"],
    },
)

# ──────────────────────────────────────────────────────────────
# 공통 프롬프트
# ──────────────────────────────────────────────────────────────
generic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You're a helpful assistant."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# ──────────────────────────────────────────────────────────────
# Caption / Visual 에이전트
# ──────────────────────────────────────────────────────────────
caption_agent = create_tool_calling_agent(
    llm=llm, tools=[caption_tool], prompt=generic_prompt
)
caption_agent_executor = AgentExecutor(agent=caption_agent, tools=[caption_tool])

visual_agent = create_tool_calling_agent(
    llm=llm, tools=[visual_tool], prompt=generic_prompt
)
visual_agent_executor = AgentExecutor(agent=visual_agent, tools=[visual_tool])

# ──────────────────────────────────────────────────────────────
# Report 에이전트 (Tool 없이 LLM 한 번만 호출)
# ──────────────────────────────────────────────────────────────
report_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 대화 자막을 구조화된 보고서로 바꾸는 AI야."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
_report_agent = create_tool_calling_agent(llm=llm, tools=[], prompt=report_prompt)
_report_agent_executor = AgentExecutor(agent=_report_agent, tools=[])

# ──────────────────────────────────────────────────────────────
# 응답 정규화 유틸
# ──────────────────────────────────────────────────────────────
def _normalize(output) -> str:
    """list·dict 형태 응답을 안전하게 str 로 변환."""
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        # list[str]  or  list[{"text": "..."}]
        if all(isinstance(x, str) for x in output):
            return "\n".join(output)
        if all(isinstance(x, dict) and "text" in x for x in output):
            return "\n".join(x["text"] for x in output)
    return str(output)

# ──────────────────────────────────────────────────────────────
# LangGraph에서 사용할 Runnable (후처리 포함)
# ──────────────────────────────────────────────────────────────
def _structure_report_agent_executor(caption: str) -> str:
    prompt_input = structure_report(caption)          # ① 자막 → 보고서 지시어
    raw = _report_agent_executor.invoke({"input": prompt_input})["output"]  # ② LLM 한 번
    text = _normalize(raw)                            # ③ list/dict → str
    # Claude가 "Final Answer:"를 끼워넣어도 제거
    if "Final Answer:" in text:
        text = text.split("Final Answer:", 1)[-1]
    return text.strip()

# LangGraph에 넘길 Runnable
report_agent_executor_runnable = RunnableLambda(_structure_report_agent_executor)

# ──────────────────────────────────────────────────────────────
# export
# ──────────────────────────────────────────────────────────────
__all__ = [
    "caption_agent_executor",
    "report_agent_executor_runnable",   # ← 그래프에서 이 이름만 사용
    "visual_agent_executor",
]