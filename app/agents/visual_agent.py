from langchain.agents import Tool, AgentExecutor
from langchain.tools.python.tool import PythonREPLTool
from langchain.llms import OpenAI

python_repl = PythonREPLTool()

tools = [
    Tool.from_function(
        func=python_repl.run,
        name="python_repl",
        description="차트, 표 등의 Python 실행기"
    )
]

agent = AgentExecutor.from_agent_and_tools(
    OpenAI(temperature=0),
    tools,
    verbose=True
)