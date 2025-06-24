# app/agents/summary_agent.py
import boto3
from typing import Dict, Any
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from ..core.config import settings  # settings import 추가
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SummaryAgent(Runnable):
    """YouTube 영상 포괄적 요약 생성 에이전트"""

    def __init__(self):
        # 환경변수에서 LLM 설정 가져오기
        llm_config = settings.get_llm_config()

        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.aws_region),
            model_id=settings.bedrock_model_id,
            model_kwargs=llm_config  # 환경변수 사용!
        )

        logger.info(f"🧠 SummaryAgent 초기화 - 온도: {llm_config['temperature']}, 최대토큰: {llm_config['max_tokens']}")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "다음 YouTube 영상 자막을 분석하여 포괄적인 보고서를 작성해주세요:\n\n{caption}")
        ])

    def _get_system_prompt(self) -> str:
        """유튜브 자막 분석 보고서 작성을 위한 전문 프롬프트"""
        return """# 유튜브 자막 분석 보고서 작성 프롬프트

## 1. 역할 정의  
당신은 전문적인 콘텐츠 분석가로서, 유튜브 영상의 자막을 체계적이고 완전한 보고서 형태로 변환하는 역할을 수행합니다.

## 2. 보고서 작성 지침

### 2.1 필수 섹션 구성

**0. 영상 핵심 요약 (문서 최상단 배치)**  
- 문서 시작부에 한 문단(3~4줄)로 작성  
- 영상의 **전체 주제를 압축적으로 소개**  
- 주제, 방향성, 핵심 메시지 중심으로 구성  
- **배경 설명이나 분석 없이**, 내용을 요약 정보로만 전달  
- 이 요약만 읽어도 영상의 방향과 핵심 흐름을 파악할 수 있어야 함  
- '1. 개요'와는 역할이 다름 (요약 카드처럼 작성)

**1. 개요 (Executive Summary)**  
- 영상의 핵심 내용을 **서술형**으로 요약 (150~200자 이상)  
- **핵심 메시지 + 배경 맥락 + 전달 의도**를 중심으로 서술  
- 영상이 왜 중요한지, 어떤 문제를 다루는지를 해설적으로 설명  
- '상단 요약'과 달리 **분석적 서문** 역할

**2. 주요 내용 분석**  
- 최소 3개 이상의 세부 문단  
- 각 문단당 200~300자 이상  
- 문단 구조: 소제목 + 요약 + 상세 설명  
- 자막에 기반한 구체적 근거 포함
- 시간 정보 활용: 중요 구간의 타임스탬프 언급 (가능한 경우)
- 화자 구분: 다중 화자 시 발언자별 분석 (가능한 경우)

**3. 핵심 인사이트**  
- 영상에서 도출되는 주요 시사점  
- 실무적/학술적 함의 포함
- 새로운 관점이나 발견사항
- 데이터나 수치가 있는 경우 구체적으로 언급

**4. 결론 및 제언**  
- 전체 내용 종합  
- 향후 방향성 또는 응용 가능성 제시
- 실행 가능한 액션 아이템 (해당하는 경우)

**5. 부록**  
- 주요 인용구  
- 언급된 통계나 수치 정리
- 참고 자료 (필요 시)

### 2.2 문체 및 형식
- **서술형 문장**: 구어체를 문어체로 완전히 변환  
- **객관적 어조**: 3인칭 관점에서 기술  
- **전문적 표현**: 학술적/비즈니스 용어 사용  
- **논리적 연결**: 문장 간 흐름과 연결 고리를 명확히 할 것

### 2.3 내용 구성
- **각 문단 최소 200자 이상**  
- **요약-설명 구조**로 구성  
- **증거 기반 서술**: 자막 내용 또는 맥락을 근거로 분석  
- **맥락 제공**: 필요 시 배경 지식이나 외부 설명 추가  
- **상단 요약과 개요는 역할이 다르며 반드시 구분**
- **자막 특성 고려**: 비언어적 요소 [음악], [박수] 등 맥락 정보 활용

### 2.4 품질 기준
- **일관성**: 전체 어조와 형식 유지  
- **완결성**: 각 섹션이 독립적으로도 이해 가능  
- **정확성**: 자막 내용을 왜곡 없이 재구성  
- **가독성**: 제목, 부제목, 단락 구분 명확
- **실용성**: 독자가 실제로 활용할 수 있는 정보 제공

## 3. 출력 형식

```markdown
# [영상 제목] 분석 보고서

**영상 핵심 요약**: [한 문단, 3~4줄 이내의 압축적 요약]

## 1. 개요  
[핵심 내용 요약 (배경 맥락, 전달 의도 포함, 150-200자 이상)]

## 2. 주요 내용 분석  

### 2.1 [첫 번째 주제]  
**요약**: [핵심 내용 요약]  
**분석**: [상세 분석 및 설명 (200-300자 이상)]  

### 2.2 [두 번째 주제]  
**요약**: [핵심 내용 요약]  
**분석**: [상세 분석 및 설명 (200-300자 이상)]  

### 2.3 [세 번째 주제]  
**요약**: [핵심 내용 요약]  
**분석**: [상세 분석 및 설명 (200-300자 이상)]  

## 3. 핵심 인사이트  
[도출된 주요 시사점 및 의미, 실무적/학술적 함의]

## 4. 결론 및 제언  
[전체 내용 종합 및 향후 방향 제안, 실행 가능한 조언]

## 5. 부록  
[주요 인용구, 통계 정리, 참고 자료]
```

## 4. 중요 지침
- 최소 1000자 이상의 상세한 분석 제공
- 전문 용어 사용 시 처음 등장할 때 설명 포함
- 시간 순서나 인과관계가 있는 내용은 명확히 표시
- 복잡한 개념은 시각화 가능하도록 명확히 기술
- 자막에 없는 내용을 추측하여 추가하지 말 것
- 구체적 수치, 통계, 비교 데이터가 있으면 모두 포함
- 영상을 보지 않고도 완전히 이해할 수 있는 수준으로 작성"""

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """포괄적 요약 생성"""
        caption = state.get("caption", "")

        if not caption or "[오류]" in caption:
            logger.warning("유효한 자막이 없습니다.")
            return {
                **state,
                "summary": "자막을 분석할 수 없습니다. 영상에 자막이 없거나 추출에 실패했습니다."
            }

        try:
            logger.info("🧠 포괄적 요약 생성 시작...")

            # 자막이 너무 길면 전처리
            processed_caption = self._preprocess_caption(caption)

            response = self.llm.invoke(
                self.prompt.format_messages(caption=processed_caption)
            )

            summary = response.content.strip()

            # 요약 품질 검증
            if len(summary) < 500:
                logger.warning("생성된 요약이 너무 짧습니다. 더 상세한 요약을 요청합니다.")
                summary = self._generate_detailed_summary(processed_caption, summary)

            logger.info(f"✅ 요약 생성 완료: {len(summary)}자")
            return {**state, "summary": summary}

        except Exception as e:
            error_msg = f"요약 생성 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return {**state, "summary": f"[오류] {error_msg}"}

    def _preprocess_caption(self, caption: str) -> str:
        """자막 전처리 - 중요 부분 추출"""
        if len(caption) <= 6000:
            return caption

        logger.info(f"자막이 너무 깁니다 ({len(caption)}자). 중요 부분을 추출합니다.")

        # 중요도 키워드
        importance_keywords = [
            '중요', '핵심', '주요', '필수', '결론', '요약', '정리',
            '첫째', '둘째', '셋째', '마지막', '또한', '그리고', '따라서',
            '장점', '단점', '특징', '방법', '이유', '결과', '원인',
            '주의', '팁', '추천', '권장', '제안',
            '데이터', '통계', '수치', '비교', '분석',
            '정의', '개념', '원리', '이론', '법칙'
        ]

        # 문장 단위로 분할
        sentences = [s.strip() for s in caption.replace('\n', ' ').split('.') if s.strip()]

        # 중요 문장과 일반 문장 분류
        important_sentences = []
        regular_sentences = []

        for sentence in sentences:
            importance_score = sum(1 for keyword in importance_keywords if keyword in sentence)
            if importance_score > 0:
                important_sentences.append((importance_score, sentence))
            else:
                regular_sentences.append(sentence)

        # 중요도 순으로 정렬
        important_sentences.sort(key=lambda x: x[0], reverse=True)

        # 결과 조합
        result_sentences = []

        # 처음과 끝 부분 포함
        result_sentences.extend(sentences[:10])
        result_sentences.extend(sentences[-10:])

        # 중요 문장들 추가
        result_sentences.extend([s[1] for s in important_sentences[:40]])

        # 일반 문장 중 일부 추가
        step = max(1, len(regular_sentences) // 20)
        result_sentences.extend(regular_sentences[::step][:20])

        # 중복 제거하면서 순서 유지
        seen = set()
        final_sentences = []
        for sentence in result_sentences:
            if sentence not in seen and sentence.strip():
                seen.add(sentence)
                final_sentences.append(sentence)

        processed = '. '.join(final_sentences)

        # 최대 길이 제한
        if len(processed) > 6000:
            processed = processed[:6000] + "..."

        logger.info(f"자막 전처리 완료: {len(caption)}자 → {len(processed)}자")
        return processed

    def _generate_detailed_summary(self, caption: str, initial_summary: str) -> str:
        """더 상세한 요약 생성"""
        try:
            followup_prompt = ChatPromptTemplate.from_messages([
                ("system", "이전 요약이 너무 간단합니다. 원본 자막의 모든 중요한 내용을 포함하여 더 상세하고 포괄적인 분석 보고서를 작성해주세요."),
                ("human", f"원본 자막:\n{caption}\n\n이전 요약:\n{initial_summary}\n\n더 상세한 분석 보고서를 작성해주세요.")
            ])

            response = self.llm.invoke(followup_prompt.format_messages())
            return response.content.strip()

        except Exception as e:
            logger.error(f"상세 요약 생성 실패: {e}")
            return initial_summary