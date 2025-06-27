from typing import Dict, Any, List
from datetime import datetime
import uuid
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.analysis import AnalysisResponse
from app.services.rouge_service import rouge_service

class AnalysisService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

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
                    print(f"\n📄 문서 분석 ROUGE 평가 완료")
                except Exception as rouge_error:
                    print(f"⚠️ 문서 ROUGE 계산 중 오류: {rouge_error}")
            
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