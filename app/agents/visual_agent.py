import os
import json
import boto3
import logging
from typing import List, Dict, Any
from langchain_aws import ChatBedrock
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 환경변수 디버그
print(f"[DEBUG] BEDROCK_MODEL_ID: {os.getenv('BEDROCK_MODEL_ID')}")
print(f"[DEBUG] AWS_REGION: {os.getenv('AWS_REGION')}")

class VisualAgent:
    def __init__(self):
        load_dotenv()  # 환경변수 다시 로드
        model_id = os.getenv("BEDROCK_MODEL_ID")
        if not model_id:
            raise ValueError("BEDROCK_MODEL_ID 환경변수가 설정되지 않았습니다")
            
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION")),
            model_id=model_id,
            model_kwargs={"temperature": 0.0, "max_tokens": 4096}
        )
    
    def analyze_and_tag(self, report_text: str) -> Dict[str, Any]:
        """보고서를 분석하여 시각화 태그 삽입"""
        prompt = f"""
당신은 보고서를 분석하여 시각화가 필요한 부분을 식별하는 전문가입니다.

## 임무
1. 보고서 내용을 깊이 분석
2. 시각화가 효과적인 내용 전달에 도움될 부분 식별 
3. 시각화와 관련된 **정확한 원본 텍스트 문단** 추출

## 보고서 분석
{report_text}

## 작업 단계
1. **전체 주제와 흐름 파악**
2. **시각화가 도움될 부분 식별** (비교, 과정, 개념, 데이터, 구조, 흐름 등)
3. **시각화와 직접 관련된 완전한 문단 추출**

## 중요 지침
- **related_content**에는 시각화와 직접 관련된 **완전한 문단**을 포함하세요
- 문장이 중간에 끊기지 않도록 **완성된 문장들**로 구성
- 시각화 주제와 **정확히 일치하는 내용**만 선택
- 최소 100자 이상의 의미 있는 텍스트 블록 제공

## 출력 형식
```json
{{
  "visualization_requests": [
    {{
      "purpose": "comparison|process|concept|overview|detail",
      "content_description": "시각화할 구체적 내용",
      "related_content": "시각화와 직접 관련된 완전한 원본 문단"
    }}
  ]
}}
```

JSON만 출력하세요.
"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = content[start_idx:end_idx+1]
                result = json.loads(json_part)
                
                logger.info(f"태깅 완료: {len(result.get('visualization_requests', []))}개 시각화 요청")
                return result
            else:
                logger.error("JSON 파싱 실패")
                return {**state, "visualization_requests": []}
                
        except Exception as e:
            logger.error(f"맥락 분석 및 태깅 실패: {e}")
            return {**state, "visualization_requests": []}
    
    def generate_visualizations(self, visualization_requests: List[Dict], caption_context: str = "") -> List[Dict]:
        """시각화 요청에 따라 시각화 생성"""
        if not visualization_requests:
            logger.info("시각화 요청이 없습니다.")
            return []
        
        logger.info(f"{len(visualization_requests)}개 시각화 생성 시작...")
        
        generated_visualizations = []
        
        for i, req in enumerate(visualization_requests):
            tag_id = str(i + 1) 
            logger.info(f"시각화 {i+1}/{len(visualization_requests)} 생성 중... (태그: {req.get('tag_id', 'unknown')})")
            
            try:
                purpose = req.get("purpose", "")
                content_description = req.get("content_description", "")
                related_content = req.get("related_content", "")
                prompt = f"""
당신은 특정 태그와 맥락 정보를 바탕으로 정확한 시각화를 생성하는 전문가입니다.


## 시각화 요청 정보
- **목적**: {purpose}
- **내용**: {content_description}

## 원본 텍스트(이 정보만 사용하세요): {related_content}


## 전체 자막 (추가 참고용)
{caption_context}


## 지침
1. 제공된 맥락과 데이터를 정확히 활용
2. 독자 이해를 최대화
3. 위 원본 텍스트와 전체 자막에서 명시된 정보만 사용. **원본 텍스트, 전체 자막에 없는 임의의 데이터를 넣지 말 것**
4. 요청된 목적에 정확히 부합하는 시각화 생성


## 사용 가능한 시각화 타입
- **chartjs**: 데이터 비교, 트렌드, 비율
- **plotly**: 수학적/과학적 그래프, 복잡한 데이터
- **mermaid**: 프로세스, 플로우차트, 타임라인
- **markmap**: 개념 관계, 마인드맵, 분류 체계
- **table**: 구조화된 정보, 비교표

다음 중 하나의 형식으로 응답하세요:

**1. Chart.js 차트:**
{{
  "type": "chartjs",
  "chart_type": "bar|line|pie|radar|scatter",
  "title": "차트 제목",
  "config": {{
    "type": "bar",
    "data": {{
      "labels": ["항목1", "항목2", "항목3"],
      "datasets": [{{
        "label": "데이터셋 이름",
        "data": [10, 20, 30],
        "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
      }}]
    }},
    "options": {{
      "responsive": true,
      "maintainAspectRatio": false
    }}
  }},
  "insight": "이 차트를 통해 얻을 수 있는 인사이트"
}}

**2. Plotly 수학/과학:**
{{
  "type": "plotly", 
  "chart_type": "function|scatter|heatmap|3d|line charts|pie charts|bubble charts|histograms",
  "title": "그래프 제목",
  "config": {{
    "data": [{{
      "x": [1, 2, 3, 4],
      "y": [10, 11, 12, 13],
      "type": "scatter",
      "mode": "lines+markers"
    }}],
    "layout": {{
      "title": "그래프 제목",
      "xaxis": {{"title": "X축"}},
      "yaxis": {{"title": "Y축"}}
    }}
  }},
  "insight": "이 그래프를 통해 얻을 수 있는 인사이트"
}}

**3. Mermaid 다이어그램:**
{{
  "type": "mermaid",
  "diagram_type": "flowchart|timeline|concept",  
  "title": "다이어그램 제목",
  "code": "graph TD\\n    A[Start] --> B[Process]\\n    B --> C[End]",
  "insight": "이 다이어그램을 통해 얻을 수 있는 인사이트"
}}

**4. Markmap 마인드맵:**
{{
  "type": "markmap",
  "title": "마인드맵 제목",
  "markdown": "# 중심 주제\\n\\n## 큰 분류 1\\n\\n- 세부사항 1\\n- 세부사항 2\\n  - 하위 항목\\n\\n## 큰 분류 2\\n\\n- 세부사항 A\\n- 세부사항 B",
  "insight": "이 마인드맵을 통해 얻을 수 있는 인사이트"
}}

**5. HTML 테이블:**
{{
  "type": "table",
  "title": "표 제목", 
  "data": {{
    "headers": ["항목", "값", "설명"],
    "rows": [
      ["항목1", "값1", "설명1"],
      ["항목2", "값2", "설명2"]
    ]
  }},
  "insight": "이 표를 통해 얻을 수 있는 인사이트"
}}

**6. 창의적 제안:**
{{
  "type": "creative",
  "method": "제안하는 방법",
  "description": "어떻게 구현할지",
  "insight": "왜 이 방법이 최적인지"
}}

## 🔍 실제 작업 과정

1. **원본 텍스트 분석**: 구체적 수치, 항목, 관계 추출
2. **데이터 유형 판단**: 수치형/구조형/개념형 구분
3. **적절한 타입 선택**: 위 가이드에 따라 선택
4. **원본 기반 생성**: 추출된 정보만으로 시각화 구성
5. **data_source 추가**: 원본에서 인용한 구체적 부분 명시


JSON만 출력하세요.
"""
                
                response = self.llm.invoke(prompt)
                content = response.content.strip()
                
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_part = content[start_idx:end_idx+1]
                    viz_result = json.loads(json_part)
                    
                    # 원본 텍스트 추가
                    viz_result['original_text'] = req.get('related_content', '')
                    
                    req_with_tag = {**req, "tag_id": tag_id}

                    generated_visualizations.append({
                        "tag_id": req.get('tag_id'),
                        "original_request": req,
                        "visualization": viz_result
                    })
                    
                    logger.info(f"태그 {req.get('tag_id')} 시각화 생성 성공")
                else:
                    logger.warning(f"태그 {req.get('tag_id')} JSON 파싱 실패")
                    
            except Exception as e:
                logger.error(f"태그 {req.get('tag_id')} 시각화 생성 실패: {e}")
        
        logger.info(f"시각화 생성 완료: {len(generated_visualizations)}/{len(visualization_requests)}개 성공")
        return generated_visualizations