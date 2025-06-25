from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from app.services.document_service import document_service
from app.models.document import DocumentAnalysisRequest, DocumentAnalysisResponse
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/analysis/document",
    tags=["document"]
)

@router.post("", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    request: DocumentAnalysisRequest = None
) -> Dict[str, Any]:
    """
    문서 파일을 업로드하고 분석합니다.
    
    - **file**: 분석할 문서 파일 (PDF, DOCX, XLSX, CSV, TXT)
    - **request**: 분석 요청 옵션 (메타데이터, 오디오 포함 여부 등)
    """
    try:
        # 문서 처리
        result = await document_service.process_document(file)
        
        # 응답 생성
        response = DocumentAnalysisResponse(
            document_id=str(uuid.uuid4()),
            status="completed",
            document_info={
                "filename": result["filename"],
                "content_type": result["content_type"],
                "size": result["size"]
            },
            analysis_results={
                "text": result["text"],
                "word_count": result["word_count"],
                "metadata": result.get("metadata", {})
            },
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        return response.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
