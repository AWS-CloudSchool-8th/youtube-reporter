from typing import Dict, Any, List
from datetime import datetime
import uuid
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.analysis import AnalysisResponse
from app.services.langgraph_service import langgraph_service

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
            analysis_results = {
                "fsm_analysis": fsm_result,
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
            ("system", "You are an expert document analyzer. Analyze the following document content and provide insights."),
            ("user", "Document Content: {content}\nMetadata: {metadata}")
        ])
        
        messages = prompt.format_messages(content=docs, metadata=metadata)
        result = llm.invoke(messages)
        
        return {"analysis": result.content}



analysis_service = AnalysisService() 