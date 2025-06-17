from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from utils.llm_factory import create_llm
from core.tools.code_exec import generate_visual_from_code
from config.settings import api_config
from utils.exceptions import VisualizationError
from utils.error_handler import handle_error
import requests
import os
import uuid
from typing import List, Dict

# LLM 인스턴스는 함수 호출 시 생성
llm = create_llm(custom_max_tokens=2048)

# 참고 코드의 프롬프트 방식 적용 - Python 코드만 출력하도록 강조
code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "다음 문장을 시각화하는 **Python 코드만** 출력하세요. 다른 설명은 하지 마세요.\n"
     "반드시 matplotlib.pyplot 또는 pandas를 사용하고, 마지막 줄은 plt.savefig('output.png', dpi=300, bbox_inches='tight')여야 합니다.\n\n"
     "예시:\n"
     "import matplotlib.pyplot as plt\n"
     "import numpy as np\n"
     "data = [1, 2, 3, 4]\n"
     "plt.figure(figsize=(10, 6))\n"
     "plt.bar(range(len(data)), data)\n"
     "plt.title('Sample Chart')\n"
     "plt.savefig('output.png', dpi=300, bbox_inches='tight')\n"
     ),
    ("human", "{input}")
])

# DALL-E 프롬프트 생성용
visual_prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 이미지 생성 전문가입니다. 주어진 설명을 보고, "
     "{type} 형태의 시각화를 만들기 위한 DALL·E 프롬프트를 작성해 주세요. "
     "항상 최소한의 스타일 가이드(예: 검은 실선, 흰 배경, 핵심 레이블)를 포함하고, "
     "내용을 명확히 전달할 수 있도록 작성해야 합니다."),
    ("human", "{description}")
])


def make_image_prompt(description: str, vtype: str) -> str:
    """DALL-E 프롬프트 생성"""
    msgs = visual_prompt_template.format_messages(description=description, type=vtype)
    return llm.invoke(msgs).content.strip()


def generate_visuals(description: str, vtype: str = "diagram") -> str:
    """DALL-E 이미지 생성"""
    dalle_api = "https://api.openai.com/v1/images/generations"
    dalle_prompt = make_image_prompt(description, vtype)

    headers = {
        "Authorization": f"Bearer {api_config.openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": api_config.dalle_model,
        "prompt": dalle_prompt,
        "n": 1,
        "size": api_config.dalle_image_size
    }
    response = requests.post(dalle_api, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("data", [{}])[0].get("url", "[Image generation failed]")


# 차트/그래프 관련 타입들 정의
CHART_TYPES = {
    "bar_chart", "line_chart", "pie_chart", "timeline",
    "chart", "table", "graph", "plot", "histogram", "scatter"
}

# 이미지 관련 타입들 정의
IMAGE_TYPES = {"image", "illustration", "diagram", "picture"}

# 텍스트 관련 타입들 정의
TEXT_TYPES = {"text"}


def dispatch_visual_block(blocks: List[dict]) -> List[dict]:
    """참고 코드 방식의 시각화 블록 처리"""
    results = []

    for i, blk in enumerate(blocks):
        print(f"\n🔍 블록 {i} 내용 확인: {blk} (타입: {type(blk)})")

        # 블록 검증 및 정리
        if not isinstance(blk, dict):
            print(f"❌ dict 타입 아님. blk = {blk}")
            continue

        t, txt = blk.get("type"), blk.get("text")
        print(f"🧩 type: {t}, text: {txt}")

        if not t or not txt:
            print(f"❌ type 또는 text가 누락됨")
            continue

        try:
            if t in CHART_TYPES:
                # Python 코드 생성 및 실행
                code = llm.invoke(code_gen_prompt.format_messages(input=txt)).content
                print("🧪 생성된 코드:\n", code)

                url = generate_visual_from_code(code)

                if url.startswith("[Error"):
                    print(f"❌ 코드 실행 실패: {url}")
                    url = f"[Chart generation failed: {url}]"

            elif t in IMAGE_TYPES:
                # DALL-E 이미지 생성
                if not api_config.openai_api_key:
                    url = "[OpenAI API key not configured]"
                else:
                    url = generate_visuals(txt, vtype=t)

            elif t in TEXT_TYPES:
                # 텍스트는 시각화 없음
                url = ""

            else:
                # 기본적으로 차트로 처리
                code = llm.invoke(code_gen_prompt.format_messages(input=txt)).content
                print("🧪 생성된 코드 (기본):\n", code)
                url = generate_visual_from_code(code)

                if url.startswith("[Error"):
                    url = f"[Unsupported type: {t}]"

            results.append({"type": t, "text": txt, "url": url})

        except Exception as e:
            print(f"❌ 블록 {i} 처리 중 오류: {e}")
            results.append({"type": t, "text": txt, "url": f"[Error: {e}]"})

    return results


# 시각화 자산 생성기 (기존 인터페이스 유지하면서 내부 로직 변경)
class GenerateVisualAsset(Runnable):
    def invoke(self, input: dict, config=None) -> dict:
        description = input.get("text", "")
        vtype = input.get("type", "text")

        try:
            if not description:
                raise VisualizationError("Empty description provided", "GenerateVisualAsset")

            # 단일 블록을 리스트로 만들어서 기존 함수 활용
            blocks = [{"type": vtype, "text": description}]
            results = dispatch_visual_block(blocks)

            if results:
                return results[0]
            else:
                return {"type": vtype, "text": description, "url": ""}

        except Exception as e:
            raise VisualizationError(str(e), "GenerateVisualAsset")


# Runnable로 묶어서 LangGraph에서 사용 가능
visual_asset_generator = GenerateVisualAsset()


def dispatch_visual_blocks_runnable(blocks: List[Dict]) -> List[Dict]:
    """시각화 블록들을 처리하는 함수 (에러 처리 포함)"""
    return dispatch_visual_block(blocks)


visual_node_runnable = RunnableLambda(dispatch_visual_blocks_runnable)