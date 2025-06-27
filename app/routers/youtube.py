from fastapi import APIRouter, HTTPException, Request, Depends
from app.models.youtube import (
    YouTubeSearchRequest,
    YouTubeSearchResponse,
    YouTubeAnalysisRequest,
    YouTubeAnalysisResponse
)
from app.services.youtube_service import youtube_service
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/youtube",
    tags=["youtube"]
)

@router.post("/search", response_model=YouTubeSearchResponse)
async def search_videos(request: YouTubeSearchRequest) -> YouTubeSearchResponse:
    """
    YouTube 비디오 검색
    
    - **query**: 검색할 키워드
    - **max_results**: 최대 검색 결과 수 (기본값: 10)
    """
    try:
        return await youtube_service.search_videos(
            query=request.query,
            max_results=request.max_results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class YouTubeAnalysisRequestBody(BaseModel):
    youtube_url: str

@router.post("/youtube/analysis")
async def analyze_youtube_with_fsm(
    request: YouTubeAnalysisRequestBody,
    raw_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """LangGraph FSM을 사용한 YouTube 분석"""
    from app.services.analysis_service import analysis_service
    
    print(f"DEBUG: Content-Type: {raw_request.headers.get('content-type')}")
    print(f"DEBUG: 요청 데이터: {request}")
    print(f"DEBUG: youtube_url: {request.youtube_url}")
    
    body = await raw_request.body()
    print(f"DEBUG: Raw body: {body}")
    
    try:
        # user_id를 명시적으로 전달
        result = await analysis_service.analyze_youtube_with_fsm(
            request.youtube_url,
            user_id=current_user["user_id"]
        )
        return result
        
    except Exception as e:
        print(f"DEBUG: 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"FSM 분석 실패: {str(e)}") 