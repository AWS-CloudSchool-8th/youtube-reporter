from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from langsmith.run_helpers import traceable

from app.llm.claude_bedrock_custom import get_bedrock_client
from app.agents.agents import (
    caption_agent_executor,
    report_agent_executor_runnable,   # ← 수정된 이름
)
from app.agents.tools import parse_report_to_json
from langchain_aws import ChatBedrock

# ──────────────────────────────────────────────────────────────
# normalize 함수 (이전과 동일)
# ──────────────────────────────────────────────────────────────
def normalize_output(output) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        if all(isinstance(x, str) for x in output):
            return "\n".join(output)
        if all(isinstance(x, dict) and "text" in x for x in output):
            return "\n".join(x["text"] for x in output)
    return str(output)

# ──────────────────────────────────────────────────────────────
# LangGraphAgentNode (동일)
# ──────────────────────────────────────────────────────────────
class LangGraphAgentNode(Runnable):
    def __init__(self, executor, input_key="agent_output", final=False):
        self.executor = executor
        self.input_key = input_key
        self.final = final

    def _resolve_step_name(self):
        return "caption" if self.input_key == "youtube_url" else "report"

    def invoke(self, state: dict, config=None):
        text = state.get(self.input_key, "")
        if not text or (isinstance(text, str) and text.strip() == ""):
            print(f"[Skip] '{self.input_key}' is empty. Skipping.\n")
            return {**state, "steps_done": state.get("steps_done", [])}

        result = self.executor.invoke({"input": text})
        obs = result.get("output") if isinstance(result, dict) else str(result)
        new_state = {
            **state,
            "agent_output": obs,
            "steps_done": state.get("steps_done", []) + [self._resolve_step_name()],
        }
        if self.final:
            new_state["final_output"] = obs
            new_state.pop("next", None)
        print(f"[Agent Output] {obs}\n")
        return new_state

# ──────────────────────────────────────────────────────────────
# Supervisor Router & ToolAgent  (내용 동일, 생략)
# ──────────────────────────────────────────────────────────────
# === Supervisor Router 정의 ===
supervisor_llm = ChatBedrock(
    client=get_bedrock_client(),
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs={
        "max_tokens": 2048,
        "temperature": 0.0,
        "stop_sequences": ["Final Answer:"]
    }
)

class SupervisorRouter(Runnable):
    name = "supervisor"

    def invoke(self, state: dict, config=None):
        raw_output = state.get("agent_output", "")
        last_output = normalize_output(raw_output)
        steps_done = state.get("steps_done", [])

        if all(step in steps_done for step in ["caption", "report", "parse"]):
            print("[Supervisor] All steps completed. Ending execution.\n")
            return {**state, "next": "end"}

        prompt = (
            "You are a workflow supervisor in a multi-step process.\n"
            "Steps: caption, report, parse.\n"
            "Rules:\n"
            "1. Start with 'caption' if not done.\n"
            "2. Then 'report'.\n"
            "3. Then 'parse'.\n"
            "4. Do not repeat steps.\n"
            "5. If all done, return 'end'.\n"
            f"Steps done: {steps_done}\n"
            f"Last output: {last_output}\n"
            "Return next step (one word only)."
        )

        msg = HumanMessage(content=prompt)
        response = supervisor_llm.invoke([msg])
        decision = response.content.strip().lower()

        if decision not in ["caption", "report", "parse", "end"]:
            raise ValueError(f"Invalid decision from LLM: {decision}")

        if decision not in steps_done and decision != "end":
            steps_done.append(decision)

        return {**state, "next": decision, "steps_done": steps_done}

# === JSON 파싱 노드 정의 ===
class ToolAgent(Runnable):
    def __init__(self, func, field: str = "agent_output", final: bool = False):
        self.func = func
        self.field = field
        self.final = final

    def invoke(self, state: dict, config=None):
        if self.field not in state:
            raise KeyError(f"Missing '{self.field}' in state: {state}")
        input_data = state[self.field]
        result = self.func(input_data)
        updated_state = {
            **state,
            "agent_output": result,
            "steps_done": state.get("steps_done", []) + ["parse"],
        }
        if self.final:
            updated_state["final_output"] = result
            updated_state.pop("next", None)
        return updated_state

# ──────────────────────────────────────────────────────────────
# FSM 구성
# ──────────────────────────────────────────────────────────────
builder = StateGraph(state_schema=dict)

builder.add_node("supervisor", SupervisorRouter())
builder.add_node("caption", LangGraphAgentNode(caption_agent_executor, input_key="youtube_url"))
builder.add_node("report",  LangGraphAgentNode(report_agent_executor_runnable))  # ★
builder.add_node("parse",   ToolAgent(func=parse_report_to_json, final=True))

def routing(state):
    nxt = state.get("next")
    return nxt if nxt in ["caption", "report", "parse"] else "__end__"

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", routing)

builder.add_edge("caption", "supervisor")
builder.add_edge("report",  "supervisor")
builder.add_edge("parse",   "supervisor")
builder.add_edge("parse",   "__end__")

compiled_graph = builder.compile()

@traceable(name="agentic-graph")
def run_graph(state):
    return compiled_graph.invoke(state)

graph = compiled_graph