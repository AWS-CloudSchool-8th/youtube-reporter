# app/agents/report_agent.py
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


class ReportAgent(Runnable):
    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION")),
            model_id=os.getenv("AWS_BEDROCK_MODEL_ID"),
            model_kwargs={"temperature": 0.7, "max_tokens": 4096}
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
당신은 YouTube 영상을 분석하여 시각적 보고서를 생성하는 전문가입니다.

다음 JSON 형식으로 응답하세요:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "요약", 
      "content": "영상의 핵심 내용을 2-3문장으로 요약"
    }},
    {{
      "type": "paragraph",
      "title": "주요 내용",
      "content": "영상의 주요 내용을 상세히 설명"
    }},
    {{
      "type": "bar_chart",
      "title": "데이터 차트",
      "data": {{
        "labels": ["항목1", "항목2", "항목3"],
        "datasets": [{{
          "label": "데이터",
          "data": [10, 20, 15],
          "backgroundColor": "#6366f1"
        }}]
      }}
    }},
    {{
      "type": "mindmap",
      "title": "핵심 개념",
      "data": {{
        "center": "중심 주제",
        "branches": [
          {{
            "label": "주요 개념 1",
            "children": ["세부사항1", "세부사항2"]
          }}
        ]
      }}
    }}
  ]
}}

실제 영상 내용을 반영하여 의미있는 데이터와 시각화를 생성하세요.
            """),
            ("human", "YouTube 영상 자막:\n{caption}")
        ])

    def invoke(self, state: dict, config=None):
        caption = state.get("caption", "")

        try:
            response = self.llm.invoke(
                self.prompt.format_messages(caption=caption[:2000])
            )

            # JSON 파싱
            import json
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()

            result = json.loads(content)
            return {**state, "report_result": result}

        except Exception as e:
            # 실패시 기본 결과
            fallback = {
                "title": "YouTube 영상 분석",
                "sections": [
                    {
                        "type": "heading",
                        "title": "분석 결과",
                        "content": "YouTube 영상 분석 결과"
                    },
                    {
                        "type": "paragraph",
                        "title": "영상 내용",
                        "content": caption[:500] + "..." if len(caption) > 500 else caption
                    }
                ]
            }
            return {**state, "report_result": fallback}