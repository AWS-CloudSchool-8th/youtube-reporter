from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
import json
import boto3

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name="us-west-2"),
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 4096}
)

split_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 보고서를 분석해 각 문단을 시각화 가능한 정보 블록으로 나누는 역할을 해. 각 블록은 다음 형식을 따라야 해:

[
  {
    "title": "블록 제목",
    "summary": "핵심 내용 요약",
    "visual_type": "bar_chart | line_chart | pie_chart | timeline | text | image",
    "data": { 필요한 경우 시각화에 사용될 데이터 (예: 숫자 목록, 시간별 값 등) }
  },
  ...
]

문단 내용을 바탕으로 적절한 시각화 타입을 판단하고, 가능하면 데이터도 함께 구성해. 시각화가 어려운 문단은 'text' 타입으로 처리해.
"""),
    ("human", "{input}")
])

def extract_visual_blocks(text: str):
    try:
        result = llm.invoke(split_prompt.format_messages(input=text)).content
        parsed = json.loads(result)
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        return []