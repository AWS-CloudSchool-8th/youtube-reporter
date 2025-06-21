# app/agents/summary_agent.py
import os
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


class SummaryAgent(Runnable):
    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION")),
            model_id=os.getenv("AWS_BEDROCK_MODEL_ID"),
            model_kwargs={"temperature": 0.3, "max_tokens": 2048}
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
당신은 YouTube 영상 자막을 분석하여 핵심 내용을 추출하는 전문가입니다.

주어진 자막을 분석하여 다음을 추출하세요:
1. 영상의 주제/제목
2. 핵심 요약 (2-3문장)
3. 주요 내용 (상세 설명)
4. 언급된 중요한 데이터나 수치
5. 핵심 키워드들

간결하고 명확하게 정리해주세요.
            """),
            ("human", "다음 YouTube 영상 자막을 분석해주세요:\n\n{caption}")
        ])

    def invoke(self, state: dict, config=None):
        caption = state.get("caption", "")
        summary_level = state.get("summary_level", "detailed")
        
        if not caption or "자막을 찾을 수 없습니다" in caption or "자막 추출 실패" in caption:
            return {**state, "summary": "자막을 분석할 수 없습니다."}

        try:
            # 자막이 너무 길면 중요한 부분만 추출
            processed_caption = self._preprocess_caption(caption)
            
            # 요약 레벨에 따른 프롬프트 조정
            level_prompt = self._get_level_specific_prompt(summary_level)
            
            response = self.llm.invoke(
                level_prompt.format_messages(caption=processed_caption)
            )

            summary = response.content.strip()
            return {**state, "summary": summary, "summary_level": summary_level}

        except Exception as e:
            print(f"SummaryAgent 오류: {str(e)}")
            return {**state, "summary": f"요약 생성 실패: {str(e)}", "summary_level": summary_level}
    
    def _preprocess_caption(self, caption: str) -> str:
        """자막 전처리"""
        if len(caption) <= 4000:
            return caption
            
        # 중요한 부분 추출
        sentences = caption.split('.')
        important_sentences = []
        
        keywords = ['중요', '핵심', '결론', '요약', '포인트', '주요', '특징', '방법', '결과', '데이터', '통계']
        
        # 처음 10문장
        important_sentences.extend(sentences[:10])
        
        # 키워드 포함 문장들
        for sentence in sentences[10:-10]:
            if any(keyword in sentence for keyword in keywords):
                important_sentences.append(sentence)
                
        # 마지막 10문장  
        important_sentences.extend(sentences[-10:])
        
        processed = '. '.join(important_sentences)
        return processed[:4000] if len(processed) > 4000 else processed
    
    def _get_level_specific_prompt(self, level: str):
        """요약 레벨에 따른 구체적인 프롬프트 생성"""
        if level == "simple":
            return ChatPromptTemplate.from_messages([
                ("system", """
당신은 YouTube 영상 자막을 간단하게 요약하는 전문가입니다.

주어진 자막을 분석하여 다음을 간단히 추출하세요:
1. 영상의 핵심 주제 (1문장)
2. 가장 중요한 포인트 3가지 (각 1문장)
3. 핵심 키워드 5개

간결하고 핵심만 정리해주세요.
                """),
                ("human", "다음 YouTube 영상 자막을 간단히 요약해주세요:\n\n{caption}")
            ])
        elif level == "expert":
            return ChatPromptTemplate.from_messages([
                ("system", """
당신은 YouTube 영상 자막을 전문적으로 분석하는 전문가입니다.

주어진 자막을 분석하여 다음을 상세히 추출하세요:
1. 영상의 주제/제목과 배경 맥락
2. 상세한 핵심 요약 (5-7문장)
3. 주요 내용의 심화 분석 (논리적 구조, 근거, 예시 포함)
4. 언급된 모든 중요한 데이터, 수치, 통계
5. 전문 용어 및 핵심 개념 설명
6. 실무 적용 방안 및 시사점
7. 관련 분야 및 추가 학습 방향

전문적이고 체계적으로 분석해주세요.
                """),
                ("human", "다음 YouTube 영상 자막을 전문가 수준으로 분석해주세요:\n\n{caption}")
            ])
        else:  # detailed (기본값)
            return self.prompt