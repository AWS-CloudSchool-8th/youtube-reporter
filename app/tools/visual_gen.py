import os
import requests
import tempfile
from app.tools.s3 import upload_to_s3
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
import boto3
import asyncio
import uuid

llm = ChatBedrock(
    client=boto3.client("bedrock-runtime", region_name="us-west-2"),
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 4096}
)

prompt_template = ChatPromptTemplate.from_messages([
    ("system",   "당신은 이미지 생성 전문가입니다. 주어진 설명을 보고, "
     "{type} 형태의 시각화를 만들기 위한 DALL·E 프롬프트를 작성해 주세요. "
     "항상 최소한의 스타일 가이드(예: 검은 실선, 흰 배경, 핵심 레이블)를 포함하고, "
     "내용을 명확히 전달할 수 있도록 작성해야 합니다."),
    ("human", "{description}")
])

async def generate_dalle_image(description: str, vtype: str) -> dict:
    try:
        dalle_prompt = llm.invoke(prompt_template.format_messages(description=description, type=vtype)).content
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={"model": "dall-e-3", "prompt": dalle_prompt, "n": 1, "size": "1024x1024"}
        )
        response.raise_for_status()
        image_url = response.json().get("data", [{}])[0].get("url")
        return {"type": vtype, "text": description, "url": image_url}
    except Exception as e:
        return {"type": vtype, "text": description, "url": f"[Error: {e}]"}