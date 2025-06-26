from typing import Dict, Any, List
from datetime import datetime
import uuid
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.analysis import AnalysisResponse
from app.services.langgraph_service import langgraph_service
from app.services.rouge_service import rouge_service

class AnalysisService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    async def analyze_youtube_with_fsm(self, youtube_url: str, job_id: str = None, user_id: str = None) -> AnalysisResponse:
        """LangGraph FSM을 사용한 YouTube 분석"""
        try:
            fsm_result = await langgraph_service.analyze_youtube_with_fsm(
                youtube_url=youtube_url,
                job_id=job_id,
                user_id=user_id
            )
            
            # ROUGE 평가 계산
            rouge_scores = None
            if fsm_result and fsm_result.get('final_output'):
                try:
                    # 원본 텍스트 (caption)와 요약 텍스트 추출
                    original_text = fsm_result.get('caption', '')
                    summary_text = ''
                    
                    # final_output에서 요약 텍스트 추출
                    final_output = fsm_result['final_output']
                    if isinstance(final_output, dict) and 'sections' in final_output:
                        summary_text = ' '.join([section.get('content', '') for section in final_output['sections']])
                    elif isinstance(final_output, str):
                        summary_text = final_output
                    
                    # ROUGE 점수 계산 (원본과 요약이 모두 있을 때만)
                    if original_text and summary_text:
                        rouge_scores = rouge_service.calculate_rouge_scores(original_text, summary_text)
                        print(f"\n?? YouTube URL: {youtube_url}")
                        
                except Exception as rouge_error:
                    print(f"?? ROUGE 계산 중 오류: {rouge_error}")
            
            analysis_results = {
                "fsm_analysis": fsm_result,
                "rouge_scores": rouge_scores,
                "method": "langgraph_fsm"
            }
            
            return AnalysisResponse(
                id=job_id or str(uuid.uuid4()),
                status="completed",
                analysis_results=analysis_results,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"YouTube FSM 분석 실패: {str(e)}")

    async def analyze_document(self, content: str, metadata: Dict[str, Any]) -> AnalysisResponse:
        """문서 분석"""
        try:
            # 문서 분할
            docs = self.text_splitter.split_text(content)
            
            # 문서 분석
            analysis_results = await self._analyze_document_content(docs, metadata)
            
            # ROUGE 평가 (문서 요약이 있는 경우)
            rouge_scores = None
            if analysis_results.get('analysis') and content:
                try:
                    rouge_scores = rouge_service.calculate_rouge_scores(content, analysis_results['analysis'])
                    print(f"\n?? 문서 분석 ROUGE 평가 완료")
                except Exception as rouge_error:
                    print(f"?? 문서 ROUGE 계산 중 오류: {rouge_error}")
            
            analysis_results['rouge_scores'] = rouge_scores
            
            return AnalysisResponse(
                id=str(uuid.uuid4()),
                status="completed",
                analysis_results=analysis_results,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"문서 분석 실패: {str(e)}")





    async def _analyze_document_content(self, docs: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """문서 내용 분석 - LangGraph Service의 Claude 사용"""
        from app.services.langgraph_service import llm
        from langchain.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert document analyzer. Analyze the following document content and provide a comprehensive summary and insights."),
            ("user", "Document Content: {content}\nMetadata: {metadata}\n\nPlease provide a detailed analysis and summary.")
        ])
        
        messages = prompt.format_messages(content=docs, metadata=metadata)
        result = llm.invoke(messages)
        
        return {"analysis": result.content}



analysis_service = AnalysisService()