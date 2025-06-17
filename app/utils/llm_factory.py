from langchain_aws import ChatBedrock
import boto3
from config.settings import llm_config


def create_llm(custom_max_tokens: int = None) -> ChatBedrock:
    """통합 LLM 생성 팩토리"""
    max_tokens = custom_max_tokens or llm_config.max_tokens

    return ChatBedrock(
        client=boto3.client("bedrock-runtime", region_name=llm_config.region),
        model_id=llm_config.model_id,
        model_kwargs={
            "temperature": llm_config.temperature,
            "max_tokens": max_tokens
        }
    )