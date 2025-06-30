from fastapi import APIRouter, HTTPException, Request, Depends
from shared_lib.models.youtube import (
    YouTubeSearchRequest,
    YouTubeSearchResponse,
    YouTubeAnalysisRequest,
    YouTubeAnalysisResponse
)
from services.youtube_service import youtube_service
from shared_lib.core.auth import get_current_user

router = APIRouter(
    prefix="/youtube",
    tags=["youtube"]
)

@router.post("/search", response_model=YouTubeSearchResponse)
async def search_videos(request: YouTubeSearchRequest) -> YouTubeSearchResponse:
    """
    Search YouTube videos
    
    - **query**: Keyword to search
    - **max_results**: Maximum number of results (default: 10)
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

@router.post("/analysis")
async def analyze_youtube_with_fsm(
    request: YouTubeAnalysisRequestBody,
    raw_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """YouTube analysis using LangGraph FSM"""
    from app.services.analysis_service import analysis_service

    print(f"DEBUG: Content-Type: {raw_request.headers.get('content-type')}")
    print(f"DEBUG: Request data: {request}")
    print(f"DEBUG: youtube_url: {request.youtube_url}")

    body = await raw_request.body()
    print(f"DEBUG: Raw body: {body}")

    try:
        # Explicitly pass user_id
        result = await analysis_service.analyze_youtube_with_fsm(
            request.youtube_url,
            user_id=current_user["user_id"]
        )
        return result

    except Exception as e:
        print(f"DEBUG: Error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"FSM analysis failed: {str(e)}")
