from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from utils.llm_factory import create_llm
from app.tools.code_exec import generate_visual_from_code
from app.tools.s3 import upload_to_s3
from config.settings import api_config
from utils.exceptions import VisualizationError
from utils.error_handler import handle_error
import os, requests, uuid
from typing import List, Dict

# LLM 인스턴스는 함수 호출 시 생성 (visual_gen에서는 더 적은 토큰 사용)
llm = create_llm(custom_max_tokens=2048)

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
        description = input.get("text", "")
        vtype = input.get("type", "text")

        # 기본 반환 형식
        default_result = {"type": vtype, "text": description, "url": ""}

        try:
            if not description:
                raise VisualizationError("Empty description provided", "GenerateVisualAsset")

            response = llm.invoke(
                descriptive_visual_prompt.format_messages(description=description)
            ).content.strip()

            if not response:
                raise VisualizationError("Empty response from LLM", "GenerateVisualAsset")

            if vtype in ["chart", "table"]:
                url = generate_visual_from_code(response)
                if not url or url.startswith("[Error"):
                    raise VisualizationError("Code execution failed", "GenerateVisualAsset")
                return {"type": vtype, "text": description, "url": url}

            elif vtype == "image":
                if not api_config.openai_api_key:
                    raise VisualizationError("OpenAI API key not configured", "GenerateVisualAsset")

                dalle_response = requests.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_config.openai_api_key}",
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

                data = dalle_response.json().get("data", [])
                if not data:
                    raise VisualizationError("No image data in DALL-E response", "GenerateVisualAsset")

                image_url = data[0].get("url")
                if not image_url:
                    raise VisualizationError("No image URL in DALL-E response", "GenerateVisualAsset")

                return {"type": vtype, "text": description, "url": image_url}

            else:
                return {"type": vtype, "text": description, "url": "[Unsupported type]"}

        except VisualizationError:
            # 이미 우리가 정의한 예외는 그대로 처리
            raise
        except Exception as e:
            # 예상치 못한 예외는 VisualizationError로 래핑
            raise VisualizationError(str(e), "GenerateVisualAsset")


# Runnable로 묶어서 LangGraph에서 사용 가능
visual_asset_generator = GenerateVisualAsset()


def dispatch_visual_blocks_runnable(blocks: List[Dict]) -> List[Dict]:
    """시각화 블록들을 처리하는 함수 (에러 처리 포함)"""
    results = []
    for i, block in enumerate(blocks):
        try:
            if isinstance(block, dict) and "type" in block and "text" in block:
                result = visual_asset_generator.invoke(block)
                results.append(result)
            else:
                # 잘못된 블록 형식
                error_result = handle_error(
                    VisualizationError("Invalid block format", f"block_{i}"),
                    f"dispatch_visual_blocks_runnable[{i}]",
                    {"type": "text", "text": str(block), "url": ""}
                )
                results.append(error_result)
        except Exception as e:
            # 개별 블록 처리 실패 시 에러 정보 포함하여 계속 진행
            error_result = handle_error(
                e,
                f"dispatch_visual_blocks_runnable[{i}]",
                {"type": block.get("type", "text"), "text": block.get("text", ""), "url": ""}
            )
            results.append(error_result)

    return results


visual_node_runnable = RunnableLambda(dispatch_visual_blocks_runnable)