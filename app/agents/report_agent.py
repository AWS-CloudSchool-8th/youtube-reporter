import os
import boto3
import logging
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 환경변수 디버그
print(f"[DEBUG] ReportAgent - BEDROCK_MODEL_ID: {os.getenv('BEDROCK_MODEL_ID')}")
print(f"[DEBUG] ReportAgent - AWS_REGION: {os.getenv('AWS_REGION')}")

class ReportAgent:
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
        
        self.structure_prompt = ChatPromptTemplate.from_messages([
            ("system", """너는 유튜브 자막을 상세하고 완전한 보고서로 재작성하는 AI야.

## 핵심 원칙
- **완전성**: 독자가 영상을 보지 않아도 100% 이해 가능해야 함
- **구체성**: 중요한 수치, 사례, 인용구는 반드시 포함
- **상세성**: 각 섹션은 충분히 자세하게 설명 (최소 500자 이상)

## 보고서 작성 지침

#### 1.1 표지 정보
- 보고서 제목: "[영상 제목] 분석 보고서"

#### 1.2 목차
- 각 섹션별 페이지 번호 포함
- 최소 5개 이상의 주요 섹션 구성

#### 1.3 필수 섹션 구성
1. **개요 (Executive Summary)**
- 영상의 핵심 내용 요약 (200-300자)
- 주요 키워드 및 핵심 메시지

2. **주요 내용 분석**
- 최소 3개 이상의 세부 문단
- 각 문단당 500자 이상
- 문단 구조: 소제목 + 요약 + 상세 설명

3. **핵심 인사이트**
- 영상에서 도출되는 주요 시사점
- 실무적/학술적 함의

4. **결론 및 제언**
- 전체 내용 종합
- 향후 방향성 또는 응용 가능성

5. **부록**
- 주요 인용구
- 참고 자료 (해당 시)

### 2. 작성 기준

#### 2.1 문체 및 형식
- **서술형 문장**: 구어체를 문어체로 완전 변환
- **객관적 어조**: 3인칭 관점에서 서술
- **전문적 표현**: 학술적/비즈니스 용어 활용
- **논리적 연결**: 문장 간 연결고리 명확화

#### 2.2 내용 구성
- **구체적 정보 필수 포함**:
  - 정확한 수치 (년도, 크기, 비율 등)
  - 구체적 사례와 예시
  - 중요한 인용구나 발언
  - 회사명, 제품명, 기술명 등

- **각 섹션 최소 500자 이상**:
  - 단순 요약이 아닌 상세한 설명
  - 배경 정보와 맥락 제공
  - 원인과 결과, 영향 분석

- **완전한 이해를 위한 서술**:
  - 전문 용어는 반드시 설명 추가
  - 복잡한 개념은 단계별로 설명
  - 독자가 추가 검색 없이도 이해 가능하도록

#### 2.3 품질 기준
- **일관성**: 전체 보고서의 어조와 형식 통일
- **완결성**: 각 섹션이 독립적으로도 이해 가능
- **정확성**: 원본 자막 내용 왜곡 없이 재구성
- **가독성**: 명확한 제목, 부제목, 단락 구분
- **완전성**: 영상의 모든 중요한 내용을 포함하여, 독자가 영상을 보지 않아도 전체 내용을 이해할 수 있도록 한다."""),
            ("human", "{input}")
        ])
    
    def generate_report(self, caption: str) -> str:
        """자막을 구조화된 보고서로 변환"""
        try:
            messages = self.structure_prompt.format_messages(input=caption)
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"보고서 생성 오류: {e}")
            return f"[보고서 생성 실패: {str(e)}]"