from langchain.agents import AgentExecutor, AgentType, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_aws import ChatBedrock

import boto3
import json
from typing import Optional

from app.utils.chart import generate_chart
from app.utils.image import generate_image
from app.models.report import Visual


class VisualAgent:
    def __init__(self, region: str = "ap-northeast-2", model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        # Bedrock용 클라이언트 및 Claude 모델 초기화
        self.llm = ChatBedrock(
            region_name=region,
            model_id=model_id,
            model_kwargs={
                "temperature": 0.0,
                "top_k": 250,
                "max_tokens": 1024
            }
        )

        # Python 실행기 도구 정의
        self.python_repl = PythonREPLTool()

        self.tools = [
            Tool.from_function(
                func=self.python_repl.run,
                name="python_repl",
                description="차트, 표 등의 Python 실행기"
            )
        ]

        # 에이전트용 프롬프트 정의
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "너는 Python 도구를 사용할 수 있는 시각화 에이전트입니다."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]).partial(
            tools=self.tools,
            tool_names=[tool.name for tool in self.tools]
        )

        # React Agent 생성
        react_agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # AgentExecutor 설정
        self.agent = AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            verbose=True
        )

    def create_visual(self, visual_type: str, visual_prompt: str) -> Visual:
        if visual_type == "none":
            return None

        if visual_type == "image":
            url = generate_image(visual_prompt)
            return Visual(type="image", url=url, caption=visual_prompt)

        if visual_type == "chart":
            prompt = f"""
            다음 설명을 바탕으로 차트를 생성해주세요:
            {visual_prompt}

            matplotlib을 사용하여 차트를 생성하고, x와 y 데이터, 제목을 반환해주세요.
            결과는 다음 형식의 JSON으로 반환해주세요:
            {{"x": [값들], "y": [값들], "title": "차트 제목"}}
            """
            try:
                result = self.agent.run(prompt).strip()
                json_str = extract_json(result)
                chart_data = json.loads(json_str)
                url = generate_chart(chart_data["x"], chart_data["y"], chart_data["title"])
                return Visual(type="chart", url=url, caption=chart_data["title"])
            except Exception as e:
                print(f"차트 생성 중 오류 발생: {e}")
                return Visual(type="text", caption=f"차트 생성 실패: {visual_prompt}")

        if visual_type == "table":
            prompt = f"""
            다음 설명을 바탕으로 표를 생성해주세요:
            {visual_prompt}

            표 데이터를 2차원 배열로 반환해주세요. 첫 번째 행은 헤더입니다.
            결과는 다음 형식의 JSON으로 반환해주세요:
            {{"data": [["헤더1", "헤더2"], ["값1", "값2"], ...]}}

            파이썬 코드 실행은 필요 없습니다.
            """
            try:
                result = self.agent.run(prompt).strip()
                json_str = extract_json(result)
                table_data = json.loads(json_str)
                return Visual(type="table", data=table_data["data"], caption=visual_prompt)
            except Exception as e:
                print(f"표 생성 중 오류 발생: {e}")
                return Visual(type="text", caption=f"표 생성 실패: {visual_prompt}")

        return None


def extract_json(text: str) -> str:
    """프롬프트 출력에서 JSON 문자열만 깔끔하게 뽑아내는 함수"""
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()

