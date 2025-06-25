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
당신은 보고서를 분석하여 시각화가 필요한 부분을 식별하고 태그를 삽입하는 전문가입니다.

## 임무
1. 보고서 내용을 깊이 분석
2. 시각화가 효과적인 내용 전달에 도움될 부분 식별 
3. 시각화가 구조화된 내용 전달에 도움될 부분 식별 
4. 해당 위치에 간단한 숫자 태그 삽입
5. 각 태그별로 시각화와 관련된 **정확한 원본 텍스트 문단** 추출

## 보고서 분석
{report_text}

## 작업 단계
1. **전체 주제와 흐름 파악**
2. **시각화가 도움될 부분 식별** (비교, 과정, 개념, 데이터 등)
3. **각 부분에 [VIZ_1], [VIZ_2], [VIZ_3] 형태로 태그 삽입**
4. **태그별로 시각화와 직접 관련된 완전한 문단 추출**

## 중요 지침
- **related_content**에는 시각화와 직접 관련된 **완전한 문단**을 포함하세요
- 문장이 중간에 끊기지 않도록 **완성된 문장들**로 구성
- 시각화 주제와 **정확히 일치하는 내용**만 선택
- 최소 100자 이상의 의미 있는 텍스트 블록 제공

## 출력 형식
```json
{{
  "tagged_report": "태그가 삽입된 전체 보고서 텍스트",
  "visualization_requests": [
    {{
      "tag_id": "1",
      "purpose": "comparison|process|concept|overview|detail",
      "content_description": "시각화할 구체적 내용",
      "related_content": "시각화와 직접 관련된 완전한 원본 문단 (완성된 문장들로 구성)"
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
                return {"tagged_report": report_text, "visualization_requests": []}
                
        except Exception as e:
            logger.error(f"맥락 분석 및 태깅 실패: {e}")
            return {"tagged_report": report_text, "visualization_requests": []}
    
    def generate_visualizations(self, visualization_requests: List[Dict], caption_context: str = "") -> List[Dict]:
        """시각화 요청에 따라 시각화 생성"""
        if not visualization_requests:
            logger.info("시각화 요청이 없습니다.")
            return []
        
        logger.info(f"{len(visualization_requests)}개 시각화 생성 시작...")
        
        generated_visualizations = []
        
        for i, req in enumerate(visualization_requests):
            logger.info(f"시각화 {i+1}/{len(visualization_requests)} 생성 중... (태그: {req.get('tag_id', 'unknown')})")
            
            try:
                prompt = f"""
당신은 특정 태그와 맥락 정보를 바탕으로 정확한 시각화를 생성하는 전문가입니다.

## 시각화 요청 정보
- **태그 ID**: {req.get('tag_id', '')}
- **목적**: {req.get('purpose', '')}
- **내용**: {req.get('content_description', '')}
- **관련 텍스트**: {req.get('related_content', '')}

## 전체 자막 (추가 참고용)
{caption_context[:1000]}

## 지침
1. 제공된 맥락과 데이터를 정확히 활용
2. 태그가 삽입될 위치에서 독자 이해를 최대화
3. 보고서에 언급된 실제 정보만 사용
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
  }}
}}

**2. Plotly 차트:**
{{
  "type": "plotly",
  "title": "차트 제목",
  "config": {{
    "data": [{{
      "x": ["A", "B", "C"],
      "y": [1, 3, 2],
      "type": "scatter",
      "mode": "lines+markers"
    }}],
    "layout": {{
      "title": "차트 제목",
      "xaxis": {{"title": "X축"}},
      "yaxis": {{"title": "Y축"}}
    }}
  }}
}}

**3. Mermaid 다이어그램:**
{{
  "type": "mermaid",
  "title": "다이어그램 제목",
  "code": "graph TD\\n    A[Start] --> B[Process]\\n    B --> C[End]"
}}

**4. Markmap 마인드맵:**
{{
  "type": "markmap",
  "title": "마인드맵 제목",
  "markdown": "# 중심 주제\\n## 주요 분야 1\\n- 세부사항 1\\n- 세부사항 2\\n## 주요 분야 2\\n- 세부사항 3"
}}

**5. 테이블:**
{{
  "type": "table",
  "title": "테이블 제목",
  "data": {{
    "headers": ["항목", "값", "설명"],
    "rows": [
      ["항목1", "값1", "설명1"],
      ["항목2", "값2", "설명2"]
    ]
  }}
}}

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