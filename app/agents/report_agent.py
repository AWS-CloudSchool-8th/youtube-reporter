from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
import boto3

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name="us-west-2"),
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 4096}
)

structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 유튜브 영상 자막을 바탕으로 명확하고 논리적인 보고서를 작성하는 AI야. 자막은 대화체일 수 있으니 이를 잘 정제하고 요약해서 보고서 형식으로 바꿔야 해. 보고서는 다음 구조를 따라야 해:

1. 제목 (Title)
2. 요약 (Summary)
3. 주요 내용 정리 (Key Points) - 항목별로 정리
4. 결론 (Conclusion)

가능하다면 자막의 흐름에 따라 논리적 전개가 자연스럽게 되도록 구성해. 친절하고 간결한 어조를 유지하되, 정보는 정확하게 전달해."""),
    ("human", "{input}")
])

def generate_report(caption: str) -> str:
    try:
        messages = structure_prompt.format_messages(input=caption)
        return llm.invoke(messages).content.strip()
    except Exception as e:
        return f"[Report generation error: {e}]"