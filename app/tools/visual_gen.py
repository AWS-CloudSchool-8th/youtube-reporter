from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_aws import ChatBedrock
from app.tools.code_exec import generate_visual_from_code
from app.tools.s3 import upload_to_s3
import boto3, os, requests, uuid
from typing import List, Dict

# Claude 모델 초기화
llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name="us-west-2"),
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 2048}
)

# 통합 시각화 프롬프트
descriptive_visual_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "당신은 AI 시각화 전문가입니다. 주어진 설명을 바탕으로 어떤 시각화 자료(chart, table, image)가 "
        "가장 효과적으로 정보를 전달할 수 있을지 판단하고, 이를 생성하기 위한 명확한 출력 형식을 준비하세요.\n\n"
        "다음 조건을 지켜주세요:\n"
        "- 설명 내용을 정확히 파악한 뒤, 가장 알맞은 시각화 형식을 고르세요.\n"
        "- 시각화 유형이 chart 또는 table인 경우, Python 코드만 출력하세요. 반드시 matplotlib 또는 pandas를 사용하세요.\n"
        "- 시각화 유형이 image인 경우, DALL·E에 전달할 수 있는 명확하고 구체적인 프롬프트 한 줄만 작성하세요.\n"
        "- chart/table일 경우 마지막 줄은 반드시 저장 명령 (plt.savefig(...) 또는 df.to_csv(...))으로 끝나야 합니다.\n\n"
        "출력 형식 예시:\n"
        "- type: chart\n- content: (Python 코드 또는 프롬프트 내용)"
    )),
    ("human", "{description}")
])

# 시각화 자산 생성기
class GenerateVisualAsset(Runnable):
    def invoke(self, input: dict, config=None) -> dict:
        description = input.get("text")
        vtype = input.get("type")

        try:
            response = llm.invoke(
                descriptive_visual_prompt.format_messages(description=description)
            ).content.strip()

            if vtype in ["chart", "table"]:
                url = generate_visual_from_code(response)
                return {"type": vtype, "text": description, "url": url}

            elif vtype == "image":
                dalle_response = requests.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": response,
                        "n": 1,
                        "size": "1024x1024"
                    }
                )
                dalle_response.raise_for_status()
                image_url = dalle_response.json().get("data", [{}])[0].get("url")
                return {"type": vtype, "text": description, "url": image_url}

            else:
                return {"type": vtype, "text": description, "url": "[Unsupported type]"}

        except Exception as e:
            return {"type": vtype, "text": description, "url": f"[Error: {e}]"}

# Runnable로 묶어서 LangGraph에서 사용 가능
visual_asset_generator = GenerateVisualAsset()

def dispatch_visual_blocks_runnable(blocks: List[Dict]) -> List[Dict]:
    results = []
    for block in blocks:
        if isinstance(block, dict) and "type" in block and "text" in block:
            results.append(visual_asset_generator.invoke(block))
    return results

visual_node_runnable = RunnableLambda(dispatch_visual_blocks_runnable)
