# app/agents/report_agent.py
import os
import boto3
import json
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
당신은 YouTube 영상 요약을 바탕으로 시각적 보고서를 생성하는 전문가입니다.

주어진 영상 요약을 분석하여:
1. 구조화된 보고서 생성
2. 영상에서 언급된 실제 데이터나 개념을 추출
3. 내용과 관련성 있는 시각화 생성

다음 JSON 형식으로 응답하세요:
{{
  "title": "영상 주제 (요약에서 추출)",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약",
      "content": "요약에서 제공된 핵심 내용"
    }},
    {{
      "type": "paragraph", 
      "title": "상세 내용",
      "content": "요약에서 언급된 주요 포인트들을 구체적으로 설명"
    }},
    {{
      "type": "bar_chart",
      "title": "관련 데이터 분석",
      "data": {{
        "labels": ["요약에서 언급된 실제 항목들"],
        "datasets": [{{
          "label": "데이터",
          "data": [관련_수치들],
          "backgroundColor": "#6366f1"
        }}]
      }}
    }},
    {{
      "type": "mindmap",
      "title": "핵심 개념 구조",
      "data": {{
        "center": "영상의 중심 주제",
        "branches": [
          {{
            "label": "요약에서 언급된 주요 개념",
            "children": ["구체적인 세부사항들"]
          }}
        ]
      }}
    }}
  ]
}}

중요: 
- 요약에서 실제로 언급된 내용만 사용하세요
- 가상의 데이터를 만들지 마세요
- 영상 내용과 관련없는 일반적인 데이터는 생성하지 마세요
            """),
            ("human", "다음은 YouTube 영상의 요약입니다. 이를 바탕으로 시각적 보고서를 생성해주세요:\n\n{summary}")
        ])

    def invoke(self, state: dict, config=None):
        summary = state.get("summary", "")
        caption = state.get("caption", "")
        
        if not summary or "요약 생성 실패" in summary:
            return self._create_fallback_result(caption)

        try:
            response = self.llm.invoke(
                self.prompt.format_messages(summary=summary)
            )

            # JSON 파싱
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.rfind("```")
                content = content[start:end].strip()

            result = json.loads(content)
            
            # 결과 검증 및 보완
            result = self._validate_and_enhance_result(result, summary)
            
            return {**state, "report_result": result}

        except Exception as e:
            print(f"ReportAgent 오류: {str(e)}")
            return self._create_fallback_result(summary, str(e))
    

    
    def _validate_and_enhance_result(self, result: dict, original_summary: str) -> dict:
        """결과 검증 및 보완"""
        if not isinstance(result, dict):
            return self._create_fallback_result(original_summary)
            
        # 기본 구조 확인
        if "title" not in result:
            result["title"] = "YouTube 영상 분석"
            
        if "sections" not in result or not isinstance(result["sections"], list):
            result["sections"] = []
            
        # 빈 섹션이면 기본 섹션 추가
        if not result["sections"]:
            result["sections"] = [
                {
                    "type": "heading",
                    "title": "분석 요약",
                    "content": "영상 내용을 분석하여 요약을 생성했습니다."
                },
                {
                    "type": "paragraph", 
                    "title": "주요 내용",
                    "content": original_summary[:800] + "..." if len(original_summary) > 800 else original_summary
                }
            ]
            
        return result
    
    def _create_fallback_result(self, content: str, error: str = None) -> dict:
        """실패시 기본 결과 생성"""
        display_content = "분석에 실패했습니다."
        if content and "요약 생성 실패" not in content and "자막을 찾을 수 없습니다" not in content:
            display_content = content[:500] + "..." if len(content) > 500 else content
            
        fallback = {
            "title": "YouTube 영상 분석",
            "sections": [
                {
                    "type": "heading",
                    "title": "분석 결과",
                    "content": "영상 내용을 기반으로 한 분석 결과입니다."
                },
                {
                    "type": "paragraph",
                    "title": "내용",
                    "content": display_content
                }
            ]
        }
        
        if error:
            fallback["sections"].append({
                "type": "paragraph",
                "title": "오류 정보", 
                "content": f"처리 중 오류가 발생했습니다: {error}"
            })
            
        return fallback