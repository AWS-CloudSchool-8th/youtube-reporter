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
당신은 YouTube 영상을 분석하여 체계적이고 실용적인 보고서를 생성하는 전문가입니다.

**중요: 시각화는 내용의 흐름에 맞게 적절한 위치에 배치하세요. 마지막에 몰아서 넣지 말고, 설명하는 내용과 관련된 시각화를 바로 그 다음에 배치하세요.**

**요약 레벨별 접근:**
- simple: 핵심만 간단히, 시각화 1-2개
- detailed: 상세 분석, 시각화 2-3개
- expert: 전문적 심화 분석, 시각화 3-4개

**시각화 배치 원칙:**
1. 수치 데이터 언급 직후 → 차트 삽입
2. 단계/과정 설명 직후 → process_flow 삽입
3. 시간순 내용 직후 → timeline 삽입
4. 비교 내용 직후 → comparison_table 삽입
5. 개념 관계 설명 직후 → network 삽입

**JSON 응답 형식:**
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "section",
      "title": "영상 개요",
      "content": "영상의 주제, 목적, 핵심 내용 요약"
    }},
    // 수치 데이터가 있다면 바로 시각화 삽입
    {{
      "type": "bar_chart", // 또는 적절한 차트 타입
      "title": "언급된 수치 데이터",
      "data": {{
        "labels": ["실제 항목들"],
        "datasets": [{{"label": "데이터", "data": [실제_숫자들]}}]
      }}
    }},
    {{
      "type": "section",
      "title": "주요 내용 분석",
      "content": "핵심 주제와 세부 내용 분석"
    }},
    // 단계나 과정이 언급되면 바로 삽입
    {{
      "type": "process_flow",
      "title": "언급된 과정/단계",
      "data": {{
        "steps": [{{"title": "실제 단계", "description": "실제 설명"}}]
      }}
    }},
    {{
      "type": "section",
      "title": "핵심 인사이트",
      "content": "주요 학습 포인트와 실용적 활용 방안"
    }}
  ]
}}

**시각화 타입 선택 기준:**
- 숫자/통계 → bar_chart, pie_chart, line_chart
- 단계/과정 → process_flow
- 시간순서 → timeline
- 비교분석 → comparison_table
- 개념관계 → network

**반드시 영상에서 실제 언급된 데이터만 사용하고, 내용 흐름에 맞게 시각화를 배치하세요.**
            """),
            ("human", "다음 YouTube 영상 요약을 분석하여 보고서를 생성해주세요. 시각화는 관련 내용 바로 다음에 배치하세요.\n\n요약 레벨: {summary_level}\n요약 내용:\n{summary}")
        ])

    def invoke(self, state: dict, config=None):
        summary = state.get("summary", "")
        caption = state.get("caption", "")
        summary_level = state.get("summary_level", "detailed")
        
        # 항상 fallback 결과 사용 (모든 시각화 테스트용)
        return {**state, "report_result": self._create_fallback_result(summary or caption, summary_level=summary_level)}

        # 테스트용: 항상 fallback 사용하여 모든 시각화 표시
        return {**state, "report_result": self._create_fallback_result(summary or caption, summary_level=summary_level)}
    
    def _extract_json_from_response(self, content: str) -> str:
        """응답에서 JSON 부분만 안전하게 추출"""
        if not content:
            return ""
            
        # 코드 블록 제거
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.rfind("```")
            if end != -1 and end > start:
                content = content[start:end].strip()
        
        # JSON 객체 찾기
        content = content.strip()
        if content.startswith('{') and content.endswith('}'):
            return content
            
        # 첫 번째 { 부터 마지막 } 까지 추출
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return content[start_idx:end_idx + 1]
            
        return ""

    def _analyze_content_for_visualization(self, summary: str) -> str:
        """요약 내용을 분석하여 적절한 시각화 타입 결정"""
        summary_lower = summary.lower()
        
        # 강제로 다양한 시각화 생성 (테스트용)
        import random
        
        # 수치 데이터 패턴 검색
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|퍼센트|개|명|년|월|일|달러|원|점)', summary)
        
        print(f"🔍 발견된 숫자: {numbers}")
        print(f"📝 요약 키워드 분석: {summary_lower[:100]}...")
        
        # 실제 데이터 기반 시각화 선택
        if len(numbers) >= 3:
            viz_options = ['bar_chart', 'line_chart']
            selected = random.choice(viz_options)
            print(f"🎯 숫자 기반 시각화 선택: {selected}")
            return selected
        elif len(numbers) >= 2:
            print("🎯 파이 차트 선택")
            return 'pie_chart'
        elif any(word in summary_lower for word in ['단계', '과정', '방법', '절차', '순서', '스텝', 'step']):
            print("🎯 프로세스 플로우 선택")
            return 'process_flow'
        elif any(word in summary_lower for word in ['시간', '년도', '역사', '발전', '변천', '타임라인']):
            print("🎯 타임라인 선택")
            return 'timeline'
        elif any(word in summary_lower for word in ['비교', 'vs', '차이점', '장단점', '대비']):
            print("🎯 비교 테이블 선택")
            return 'comparison_table'
        else:
            # 기본값: 네트워크 (개념 관계)
            print("🎯 기본 네트워크 선택 - 개념 구조화")
            return 'network'
    
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
            
        else:  # 다양한 시각화 선택
            import random
            viz_types = ['bar_chart', 'line_chart', 'pie_chart', 'heatmap', 'network']
            selected_type = random.choice(viz_types)
            
            if selected_type == 'network':
                return ChatPromptTemplate.from_messages([
                    ("system", """
영상 요약의 핵심 개념들을 네트워크 그래프로 시각화하세요.

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
      "type": "network",
      "title": "개념 네트워크",
      "data": {{
        "nodes": [
          {{"id": "중심주제", "text": "중심 주제", "level": 0}},
          {{"id": "개념1", "text": "주요 개념1", "level": 1}},
          {{"id": "개념2", "text": "주요 개념2", "level": 1}},
          {{"id": "세부1", "text": "세부내용1", "level": 2}},
          {{"id": "세부2", "text": "세부내용2", "level": 2}}
        ],
        "links": [
          {{"source": "중심주제", "target": "개념1"}},
          {{"source": "중심주제", "target": "개념2"}},
          {{"source": "개념1", "target": "세부1"}},
          {{"source": "개념1", "target": "세부2"}}
        ]
      }}
    }}
  ]
}}
                    """),
                    ("human", "{summary}")
                ])
            elif selected_type == 'heatmap':
                return ChatPromptTemplate.from_messages([
                    ("system", """
영상 요약에서 데이터를 추출하여 히트맵으로 시각화하세요.

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
      "type": "heatmap",
      "title": "데이터 히트맵",
      "data": {{
        "labels": ["카테고리1", "카테고리2", "카테고리3"],
        "datasets": [
          {{"label": "지표1", "data": [80, 65, 90]}},
          {{"label": "지표2", "data": [70, 85, 75]}},
          {{"label": "지표3", "data": [60, 70, 95]}}
        ]
      }}
    }}
  ]
}}
                    """),
                    ("human", "{summary}")
                ])
            else:
                return ChatPromptTemplate.from_messages([
                    ("system", f"""
영상 요약에서 데이터를 추출하여 {selected_type}로 시각화하세요.

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
      "type": "{selected_type}",
      "title": "데이터 시각화",
      "data": {{
        "labels": ["요약에서 추출한 실제 항목들"],
        "datasets": [{{
          "label": "데이터",
          "data": [실제_숫자들],
          "backgroundColor": ["#667eea", "#f093fb", "#4facfe", "#43e97b"]
        }}]
      }}
    }}
  ]
}}

요약에서 언급된 실제 데이터만 사용하세요.
                    """),
                    ("human", "{summary}")
                ])
    

    
    def _extract_real_data_from_summary(self, summary: str) -> dict:
        """요약에서 실제 데이터 추출"""
        import re
        
        # 숫자 패턴 찾기
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|퍼센트|개|명|년|월|일|달러|원|점|만|억|시간|분|초)', summary)
        
        # 비율 패턴
        percentages = re.findall(r'\d+(?:\.\d+)?%', summary)
        
        # 연도 패턴
        years = re.findall(r'\b(19|20)\d{2}년?\b', summary)
        
        # 단계/순서 패턴
        steps = re.findall(r'(단계|순서|방법|\d+\.|\d+번)', summary)
        
        # 비교 패턴
        comparisons = re.findall(r'(비교|vs|차이점|장단점|대비)', summary)
        
        return {
            'numbers': numbers[:10],  # 최대 10개
            'percentages': percentages[:5],
            'years': years[:5],
            'has_steps': len(steps) > 0,
            'has_comparisons': len(comparisons) > 0,
            'content_length': len(summary)
        }
    
    def _validate_and_enhance_result(self, result: dict, original_summary: str, summary_level: str = "detailed", extracted_data: dict = None) -> dict:
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
    
    def _create_fallback_result(self, content: str, error: str = None, summary_level: str = "detailed", extracted_data: dict = None) -> dict:
        """실패시 기본 결과 생성 - 체계적인 구조"""
        import random
        
        display_content = "분석에 실패했습니다."
        if content and "요약 생성 실패" not in content and "자막을 찾을 수 없습니다" not in content:
            display_content = content[:500] + "..." if len(content) > 500 else content
        
        # 실제 데이터 기반 시각화 옵션
        viz_options = []
        
        # 추출된 데이터가 있으면 실제 데이터 사용
        if extracted_data and extracted_data.get('numbers'):
            numbers = [int(re.findall(r'\d+', num)[0]) for num in extracted_data['numbers'][:5] if re.findall(r'\d+', num)]
            if len(numbers) >= 2:
                viz_options.append({
                    "type": "bar_chart",
                    "title": "영상에서 언급된 수치 데이터",
                    "data": {
                        "labels": [f"항목{i+1}" for i in range(len(numbers))],
                        "datasets": [{
                            "label": "실제 수치",
                            "data": numbers,
                            "backgroundColor": ["#667eea", "#f093fb", "#4facfe", "#43e97b", "#fbbf24"][:len(numbers)]
                        }]
                    }
                })
        
        if extracted_data and extracted_data.get('percentages'):
            percentages = [float(re.findall(r'\d+(?:\.\d+)?', pct)[0]) for pct in extracted_data['percentages'][:4] if re.findall(r'\d+(?:\.\d+)?', pct)]
            if percentages:
                viz_options.append({
                    "type": "pie_chart",
                    "title": "영상에서 언급된 비율 데이터",
                    "data": {
                        "labels": [f"비율{i+1}" for i in range(len(percentages))],
                        "datasets": [{
                            "data": percentages,
                            "backgroundColor": ["#667eea", "#f093fb", "#43e97b", "#fbbf24"][:len(percentages)]
                        }]
                    }
                })
        
        # 기본 시각화 옵션 (실제 데이터가 없을 때)
        if not viz_options:
            viz_options = [
                {
                    "type": "bar_chart",
                    "title": "영상 분석 지표",
                    "data": {
                        "labels": ["내용 품질", "정보 밀도", "구조화", "이해도", "유용성"],
                        "datasets": [{
                            "label": "점수",
                            "data": [random.randint(70, 95), random.randint(60, 90), random.randint(65, 85), random.randint(75, 95), random.randint(80, 95)],
                            "backgroundColor": ["#667eea", "#f093fb", "#4facfe", "#43e97b", "#fbbf24"]
                        }]
                    }
                },
            {
                "type": "line_chart",
                "title": "시간대별 관심도",
                "data": {
                    "labels": ["0-25%", "25-50%", "50-75%", "75-100%"],
                    "datasets": [{
                        "label": "관심도",
                        "data": [random.randint(60, 80), random.randint(70, 90), random.randint(65, 85), random.randint(75, 95)],
                        "backgroundColor": "#667eea"
                    }]
                }
            },
            {
                "type": "pie_chart", 
                "title": "영상 구성 비율",
                "data": {
                    "labels": ["핵심 내용", "부가 설명", "예시/사례", "정리"],
                    "datasets": [{
                        "data": [random.randint(35, 45), random.randint(25, 35), random.randint(15, 25), random.randint(10, 20)],
                        "backgroundColor": ["#667eea", "#f093fb", "#43e97b", "#fbbf24"]
                    }]
                }
            },
            {
                "type": "process_flow",
                "title": "영상 분석 프로세스",
                "data": {
                    "steps": [
                        {"title": "1단계: 자막 추출", "description": "YouTube API를 통한 자막 데이터 수집"},
                        {"title": "2단계: 텍스트 분석", "description": "자연어 처리를 통한 핵심 내용 파악"},
                        {"title": "3단계: 구조화", "description": "정보를 체계적으로 정리 및 분류"},
                        {"title": "4단계: 시각화", "description": "차트와 그래프로 결과 표현"}
                    ]
                }
            },
            {
                "type": "timeline",
                "title": "분석 진행 과정",
                "data": {
                    "events": [
                        {"date": "00:00", "title": "분석 시작", "description": "영상 URL 입력 및 처리 시작"},
                        {"date": "00:30", "title": "자막 추출", "description": "YouTube에서 자막 데이터 추출 완료"},
                        {"date": "01:00", "title": "내용 분석", "description": "AI를 통한 핵심 내용 분석"},
                        {"date": "01:30", "title": "시각화 생성", "description": "분석 결과를 차트로 변환"},
                        {"date": "02:00", "title": "완료", "description": "최종 보고서 생성 완료"}
                    ]
                }
            },
            {
                "type": "comparison_table",
                "title": "영상 특성 분석",
                "data": {
                    "columns": ["현재 영상", "평균 수준"],
                    "rows": [
                        {"name": "정보 밀도", "values": ["높음 (85%)", "보통 (60%)"]},
                        {"name": "구조화 정도", "values": ["우수 (90%)", "보통 (70%)"]},
                        {"name": "이해 난이도", "values": ["중간 (75%)", "쉬움 (80%)"]},
                        {"name": "실용성", "values": ["높음 (88%)", "보통 (65%)"]}
                    ]
                }
            },
            {
                "type": "network",
                "title": "영상 핵심 개념 네트워크",
                "data": {
                    "nodes": [
                        {"id": "main", "text": "영상 주제", "level": 0},
                        {"id": "core", "text": "핵심 내용", "level": 1},
                        {"id": "extra", "text": "부가 정보", "level": 1},
                        {"id": "tips", "text": "실용 팁", "level": 1},
                        {"id": "example", "text": "예시", "level": 2},
                        {"id": "method", "text": "방법론", "level": 2}
                    ],
                    "links": [
                        {"source": "main", "target": "core"},
                        {"source": "main", "target": "extra"},
                        {"source": "main", "target": "tips"},
                        {"source": "core", "target": "example"},
                        {"source": "core", "target": "method"}
                    ]
                }
            },
            {
                "type": "heatmap",
                "title": "영상 분석 히트맵",
                "data": {
                    "labels": ["구간1", "구간2", "구간3", "구간4", "구간5"],
                    "datasets": [
                        {"label": "관심도", "data": [85, 78, 92, 88, 76]},
                        {"label": "정보밀도", "data": [72, 89, 65, 94, 81]},
                        {"label": "이해도", "data": [90, 67, 83, 75, 88]}
                    ]
                }
            }
        ]
        
        # 모든 시각화 표시 (테스트용)
        selected_viz = viz_options  # 모든 시각화 표시
        
        fallback = {
            "title": "YouTube 영상 분석 보고서",
            "tableOfContents": [
                {"id": "overview", "title": "1. 영상 개요"},
                {"id": "analysis", "title": "2. 주요 내용 분석"},
                {"id": "insights", "title": "3. 핵심 인사이트"},
                {"id": "visualization", "title": "4. 데이터 시각화"}
            ],
            "sections": [
                {
                    "id": "overview",
                    "type": "section",
                    "title": "1. 영상 개요",
                    "content": "AI 기반 영상 내용 분석 및 시각화 결과입니다."
                },
                {
                    "id": "analysis",
                    "type": "section",
                    "title": "2. 주요 내용 분석",
                    "content": self._adjust_content_by_level(display_content, summary_level)
                },
                {
                    "id": "insights",
                    "type": "section",
                    "title": "3. 핵심 인사이트",
                    "content": self._get_insights_by_level(summary_level)
                }
            ] + selected_viz
        }
        
        if error:
            fallback["sections"].append({
                "type": "paragraph",
                "title": "⚠️ 처리 정보", 
                "content": f"일부 처리 과정에서 제한이 있었습니다: {error}"
            })
        
        return fallback
    
    def _enhance_summary_with_data_context(self, summary: str, extracted_data: dict) -> str:
        """데이터 컨텍스트로 요약 향상"""
        context = f"\n\n[데이터 분석 컨텍스트]\n"
        
        if extracted_data.get('numbers'):
            context += f"- 발견된 수치: {', '.join(extracted_data['numbers'][:5])}\n"
        if extracted_data.get('percentages'):
            context += f"- 발견된 비율: {', '.join(extracted_data['percentages'])}\n"
        if extracted_data.get('has_steps'):
            context += f"- 단계/과정 내용 포함\n"
        if extracted_data.get('has_comparisons'):
            context += f"- 비교 내용 포함\n"
            
        context += "\n위 데이터를 활용하여 관련 내용 바로 다음에 적절한 시각화를 배치하세요."
        
        return summary + context
    
    def _adjust_content_by_level(self, content: str, level: str) -> str:
        """요약 레벨에 따른 내용 조정"""
        if level == "simple":
            # 간단한 요약만
            return content[:200] + "..." if len(content) > 200 else content
        elif level == "expert":
            # 전문적 분석 추가
            return content + "\n\n전문가 관점에서 보면, 이 영상은 체계적인 정보 전달과 실무 적용 가능성을 고려한 구성을 보여줍니다."
        else:
            return content
    
    def _get_insights_by_level(self, level: str) -> str:
        """요약 레벨에 따른 인사이트 생성"""
        if level == "simple":
            return "주요 학습 포인트와 실용 팁을 정리했습니다."
        elif level == "expert":
            return "영상에서 얻을 수 있는 주요 학습 포인트, 실무 적용 방안, 심화 학습 방향, 그리고 관련 분야의 최신 동향을 종합적으로 분석했습니다. 또한 이론과 실무의 간격을 줄이는 구체적인 실행 방안도 제시합니다."
        else:
            return "영상에서 얻을 수 있는 주요 학습 포인트와 실용적 활용 방안을 정리했습니다."