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
당신은 YouTube 영상 요약을 분석하여 시각적 보고서를 생성하는 전문가입니다.

**중요: 반드시 최소 1개 이상의 시각화를 생성해야 합니다.**

**시각화 생성 전략:**
1. 영상에서 언급된 구체적인 수치/비율이 있으면 → 해당 데이터로 차트 생성
2. 단계별 과정이나 순서가 있으면 → process_flow 생성
3. 시간순 이벤트나 역사가 있으면 → timeline 생성
4. 여러 개념이나 카테고리가 있으면 → mindmap 생성
5. 비교 내용이 있으면 → comparison_table 생성
6. 위 모든 것이 없어도 → 영상의 주요 키워드나 개념을 mindmap으로 생성

**시각화 우선순위:**
1순위: 실제 수치 데이터 → bar_chart, pie_chart, line_chart
2순위: 과정/단계 → process_flow
3순위: 시간순 내용 → timeline  
4순위: 비교 내용 → comparison_table
5순위: 개념 정리 → mindmap (항상 가능)

JSON 형식으로 응답하세요:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약",
      "content": "영상의 핵심 내용 2-3문장"
    }},
    {{
      "type": "paragraph",
      "title": "주요 내용",
      "content": "영상에서 다룬 구체적인 내용들"
    }},
    {{
      "type": "적절한_시각화_타입",
      "title": "의미있는 제목",
      "data": {{ 관련_데이터 }}
    }}
  ]
}}

**데이터 형식 예시:**
- mindmap: {{"center": "영상의 중심 주제", "branches": [{{"label": "주요 개념1", "children": ["세부내용1", "세부내용2"]}}, {{"label": "주요 개념2", "children": ["세부내용3", "세부내용4"]}}]}}
- process_flow: {{"steps": [{{"title": "1단계", "description": "설명1"}}, {{"title": "2단계", "description": "설명2"}}]}}
- bar_chart: {{"labels": ["항목1", "항목2"], "datasets": [{{"label": "데이터", "data": [수치1, 수치2], "backgroundColor": "#6366f1"}}]}}

**반드시 최소 1개의 시각화를 포함하세요. 데이터가 부족하면 mindmap을 사용하세요.**
            """),
            ("human", "다음 YouTube 영상 요약을 분석하여 반드시 시각화를 포함한 보고서를 생성해주세요:\n\n{summary}")
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
        """실패시 기본 결과 생성 (시각화 포함)"""
        display_content = "분석에 실패했습니다."
        if content and "요약 생성 실패" not in content and "자막을 찾을 수 없습니다" not in content:
            display_content = content[:500] + "..." if len(content) > 500 else content
            
        # 기본 마인드맵 생성 (항상 시각화 제공)
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
                },
                {
                    "type": "mindmap",
                    "title": "영상 구조",
                    "data": {
                        "center": "YouTube 영상",
                        "branches": [
                            {
                                "label": "내용 분석",
                                "children": ["자막 추출", "핵심 내용", "주요 포인트"]
                            },
                            {
                                "label": "처리 과정",
                                "children": ["AI 분석", "요약 생성", "시각화"]
                            }
                        ]
                    }
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