# app/agents/summary_agent.py
import os
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SummaryAgent(Runnable):
    """YouTube 영상을 포괄적으로 요약하는 에이전트"""

    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION")),
            model_id=os.getenv("AWS_BEDROCK_MODEL_ID"),
            model_kwargs={"temperature": 0.3, "max_tokens": 4096}
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 YouTube 영상 자막을 분석하여 **영상을 보지 않고도 완전히 이해할 수 있는** 포괄적인 요약을 생성하는 전문가입니다.

**핵심 원칙:**
1. **완전성**: 영상의 모든 중요한 내용을 포함하여, 독자가 영상을 보지 않아도 전체 내용을 이해할 수 있도록 합니다.
2. **구조화**: 논리적인 흐름으로 내용을 조직화하여 읽기 쉽게 만듭니다.
3. **맥락 제공**: 배경 정보, 전제 조건, 관련 개념을 충분히 설명합니다.
4. **구체성**: 추상적인 설명보다는 구체적인 예시, 수치, 사실을 포함합니다.
5. **시각화 기회**: 복잡한 개념, 프로세스, 비교, 데이터는 나중에 시각화할 수 있도록 명확히 기술합니다.

**요약 구조:**
1. **개요 (Overview)**
   - 영상의 주제와 목적
   - 핵심 메시지 또는 주장
   - 대상 시청자와 배경 맥락

2. **주요 내용 (Main Content)**
   - 핵심 개념들을 논리적 순서로 설명
   - 각 개념에 대한 충분한 설명과 예시
   - 단계별 프로세스나 방법론은 상세히 기술
   - 언급된 모든 수치, 통계, 비교 데이터 포함

3. **세부 사항 (Details)**
   - 중요한 팁, 주의사항, 권장사항
   - 관련 도구, 리소스, 참고자료
   - 실제 적용 사례나 시나리오

4. **핵심 요점 (Key Takeaways)**
   - 가장 중요한 3-5개의 핵심 메시지
   - 실행 가능한 조언이나 다음 단계

**작성 지침:**
- 최소 800자 이상의 상세한 요약
- 전문 용어는 처음 나올 때 설명 포함
- 시간 순서가 있는 내용은 명확히 표시
- 인과관계, 비교, 대조를 명확히 설명
- 복잡한 개념은 단순한 언어로 풀어서 설명

**중요**: 이 요약만 읽어도 누군가에게 영상 내용을 완전히 설명할 수 있을 정도로 상세하게 작성하세요."""),
            ("human", "다음 YouTube 영상 자막을 분석하여 포괄적인 요약을 작성해주세요:\n\n{caption}")
        ])

    def invoke(self, state: dict, config=None):
        caption = state.get("caption", "")

        if not caption or "자막을 찾을 수 없습니다" in caption or "자막 추출 실패" in caption:
            logger.warning("유효한 자막이 없습니다.")
            return {**state, "summary": "자막을 분석할 수 없습니다. 영상에 자막이 없거나 추출에 실패했습니다."}

        try:
            # 자막이 너무 길면 중요 부분 추출
            processed_caption = self._preprocess_caption(caption)

            logger.info("포괄적 요약 생성 시작...")
            response = self.llm.invoke(
                self.prompt.format_messages(caption=processed_caption)
            )

            summary = response.content.strip()

            # 요약 품질 검증
            if len(summary) < 500:
                logger.warning("생성된 요약이 너무 짧습니다. 재시도합니다.")
                # 더 상세한 요약을 요청하는 추가 프롬프트
                followup_prompt = ChatPromptTemplate.from_messages([
                    ("system", "이전 요약이 너무 간단합니다. 더 상세하고 포괄적인 요약을 작성해주세요."),
                    ("human", f"원본 자막:\n{processed_caption}\n\n이전 요약:\n{summary}\n\n더 상세한 요약을 작성해주세요.")
                ])
                response = self.llm.invoke(followup_prompt.format_messages())
                summary = response.content.strip()

            logger.info(f"요약 생성 완료: {len(summary)}자")
            return {**state, "summary": summary}

        except Exception as e:
            logger.error(f"요약 생성 실패: {str(e)}")
            return {**state, "summary": f"요약 생성 중 오류가 발생했습니다: {str(e)}"}

    def _preprocess_caption(self, caption: str) -> str:
        """자막 전처리 - 중요 부분 추출"""
        if len(caption) <= 6000:
            return caption

        logger.info(f"자막이 너무 깁니다 ({len(caption)}자). 중요 부분을 추출합니다.")

        # 문장 단위로 분할
        sentences = caption.replace('\n', ' ').split('.')

        # 중요도 키워드
        importance_keywords = [
            '중요', '핵심', '주요', '필수', '결론', '요약', '정리',
            '첫째', '둘째', '셋째', '마지막',
            '장점', '단점', '특징', '방법', '이유', '결과',
            '주의', '팁', '추천', '권장',
            '데이터', '통계', '수치', '비교',
            '정의', '개념', '원리', '이론'
        ]

        # 중요 문장 추출
        important_sentences = []
        regular_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 중요도 점수 계산
            importance_score = sum(1 for keyword in importance_keywords if keyword in sentence)

            if importance_score > 0:
                important_sentences.append((importance_score, sentence))
            else:
                regular_sentences.append(sentence)

        # 중요도 순으로 정렬
        important_sentences.sort(key=lambda x: x[0], reverse=True)

        # 처음, 중간, 끝 부분 포함
        result_sentences = []

        # 처음 10문장
        result_sentences.extend(sentences[:10])

        # 중요 문장들
        result_sentences.extend([s[1] for s in important_sentences[:30]])

        # 일반 문장 중 일부
        step = max(1, len(regular_sentences) // 20)
        result_sentences.extend(regular_sentences[::step][:20])

        # 마지막 10문장
        result_sentences.extend(sentences[-10:])

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

        logger.info(f"자막 전처리 완료: {len(caption)}자 -> {len(processed)}자")
        return processed