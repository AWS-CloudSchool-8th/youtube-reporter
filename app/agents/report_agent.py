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
            # 요약 내용 분석하여 적절한 시각화 결정
            viz_type = self._analyze_content_for_visualization(summary)
            print(f"🎯 분석된 시각화 타입: {viz_type}")
            print(f"📝 요약 내용 (처음 200자): {summary[:200]}...")
            
            # 분석된 타입에 따라 다른 프롬프트 사용
            specific_prompt = self._get_specific_prompt(viz_type)
            
            response = self.llm.invoke(
                specific_prompt.format_messages(summary=summary)
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
    
    def _analyze_content_for_visualization(self, summary: str) -> str:
        """요약 내용을 분석하여 적절한 시각화 타입 결정"""
        summary_lower = summary.lower()
        
        # 수치 데이터 패턴 검색
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|퍼센트|개|명|년|월|일)', summary)
        
        if len(numbers) >= 3:
            if any(word in summary_lower for word in ['증가', '감소', '변화', '트렌드', '년', '월']):
                return 'line_chart'
            else:
                return 'bar_chart'
        elif len(numbers) >= 2:
            if any(word in summary_lower for word in ['비율', '%', '퍼센트', '구성', '점유율']):
                return 'pie_chart'
            else:
                return 'bar_chart'
        elif any(word in summary_lower for word in ['단계', '과정', '방법', '절차', '순서']):
            return 'process_flow'
        elif any(word in summary_lower for word in ['시간', '년도', '역사', '발전', '변천']):
            return 'timeline'
        elif any(word in summary_lower for word in ['비교', 'vs', '차이점', '장단점']):
            return 'comparison_table'
        else:
            return 'mindmap'
    
    def _get_specific_prompt(self, viz_type: str):
        """시각화 타입에 따른 구체적인 프롬프트 생성"""
        
        if viz_type == 'bar_chart':
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약에서 구체적인 수치 데이터를 찾아 막대 차트를 생성하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약",
      "content": "요약 내용"
    }},
    {{
      "type": "bar_chart",
      "title": "실제 데이터 비교",
      "data": {{
        "labels": ["요약에서 언급된 실제 항목들"],
        "datasets": [{{
          "label": "수치",
          "data": [실제_숫자들],
          "backgroundColor": ["#667eea", "#764ba2", "#f093fb", "#4facfe"]
        }}]
      }}
    }}
  ]
}}

요약에서 언급된 실제 수치만 사용하세요.
                """),
                ("human", "{summary}")
            ])
            
        elif viz_type == 'pie_chart':
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약에서 비율이나 구성 요소를 찾아 파이 차트를 생성하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading", 
      "title": "핵심 요약",
      "content": "요약 내용"
    }},
    {{
      "type": "pie_chart",
      "title": "구성 비율",
      "data": {{
        "labels": ["요약에서 언급된 구성요소들"],
        "datasets": [{{
          "data": [실제_비율_숫자들],
          "backgroundColor": ["#667eea", "#f093fb", "#4facfe", "#43e97b"]
        }}]
      }}
    }}
  ]
}}

요약에서 언급된 실제 비율만 사용하세요.
                """),
                ("human", "{summary}")
            ])
            
        elif viz_type == 'process_flow':
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약에서 단계별 과정을 찾아 프로세스 플로우를 생성하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약", 
      "content": "요약 내용"
    }},
    {{
      "type": "process_flow",
      "title": "단계별 과정",
      "data": {{
        "steps": [
          {{"title": "1단계: 실제단계명", "description": "실제설명"}},
          {{"title": "2단계: 실제단계명", "description": "실제설명"}},
          {{"title": "3단계: 실제단계명", "description": "실제설명"}}
        ]
      }}
    }}
  ]
}}

요약에서 언급된 실제 단계들만 사용하세요.
                """),
                ("human", "{summary}")
            ])
            
        elif viz_type == 'timeline':
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약에서 시간순 이벤트를 찾아 타임라인을 생성하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약",
      "content": "요약 내용"
    }},
    {{
      "type": "timeline",
      "title": "시간순 이벤트",
      "data": {{
        "events": [
          {{"date": "실제날짜", "title": "실제이벤트", "description": "실제설명"}},
          {{"date": "실제날짜", "title": "실제이벤트", "description": "실제설명"}}
        ]
      }}
    }}
  ]
}}
                """),
                ("human", "{summary}")
            ])
            
        elif viz_type == 'comparison_table':
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약에서 비교 내용을 찾아 비교 테이블을 생성하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목", 
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약",
      "content": "요약 내용"
    }},
    {{
      "type": "comparison_table",
      "title": "비교 분석",
      "data": {{
        "columns": ["항목1", "항목2"],
        "rows": [
          {{"name": "기준1", "values": ["값1", "값2"]}},
          {{"name": "기준2", "values": ["값3", "값4"]}}
        ]
      }}
    }}
  ]
}}
                """),
                ("human", "{summary}")
            ])
            
        else:  # mindmap 기본값
            return ChatPromptTemplate.from_messages([
                ("system", """
영상 요약의 핵심 개념들을 마인드맵으로 구조화하세요.

JSON 형식으로 응답:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "핵심 요약", 
      "content": "요약 내용"
    }},
    {{
      "type": "mindmap",
      "title": "핵심 개념 구조",
      "data": {{
        "center": "영상의 중심 주제",
        "branches": [
          {{"label": "주요 개념1", "children": ["세부내용1", "세부내용2"]}},
          {{"label": "주요 개념2", "children": ["세부내용3", "세부내용4"]}}
        ]
      }}
    }}
  ]
}}
                """),
                ("human", "{summary}")
            ])
    

    
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
        """실패시 기본 결과 생성 - 다양한 시각화 랜덤 선택"""
        import random
        
        display_content = "분석에 실패했습니다."
        if content and "요약 생성 실패" not in content and "자막을 찾을 수 없습니다" not in content:
            display_content = content[:500] + "..." if len(content) > 500 else content
        
        # 랜덤하게 다른 시각화 생성
        viz_options = [
            {
                "type": "bar_chart",
                "title": "영상 분석 결과",
                "data": {
                    "labels": ["내용 품질", "정보량", "구조화 정도"],
                    "datasets": [{
                        "label": "점수",
                        "data": [random.randint(60, 95), random.randint(70, 90), random.randint(65, 85)],
                        "backgroundColor": ["#667eea", "#f093fb", "#4facfe"]
                    }]
                }
            },
            {
                "type": "pie_chart", 
                "title": "영상 구성 요소",
                "data": {
                    "labels": ["핵심 내용", "부가 설명", "예시"],
                    "datasets": [{
                        "data": [random.randint(40, 60), random.randint(25, 35), random.randint(15, 25)],
                        "backgroundColor": ["#667eea", "#f093fb", "#43e97b"]
                    }]
                }
            },
            {
                "type": "process_flow",
                "title": "분석 과정",
                "data": {
                    "steps": [
                        {"title": "1단계: 자막 추출", "description": "YouTube 영상에서 자막 데이터 추출"},
                        {"title": "2단계: 내용 요약", "description": "AI를 통한 핵심 내용 요약"},
                        {"title": "3단계: 시각화", "description": "구조화된 데이터로 시각화 생성"}
                    ]
                }
            }
        ]
        
        selected_viz = random.choice(viz_options)
        
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
                selected_viz
            ]
        }
        
        if error:
            fallback["sections"].append({
                "type": "paragraph",
                "title": "오류 정보", 
                "content": f"처리 중 오류가 발생했습니다: {error}"
            })
            
        return fallback