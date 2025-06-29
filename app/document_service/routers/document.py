from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from services.document_service import document_service
from shared_lib.models.document import DocumentAnalysisRequest, DocumentAnalysisResponse
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
    try:
        result = await document_service.process_document(file)
        
    
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
