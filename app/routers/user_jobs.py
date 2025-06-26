from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
from app.services.database_service import get_user_jobs, get_job_progress
from app.services.cognito_service import verify_access_token

router = APIRouter(prefix="/user", tags=["user-jobs"])

@router.get("/jobs")
async def get_user_job_list(authorization: Optional[str] = Header(None)):
    """사용자의 작업 목록 조회"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    access_token = authorization.split(" ")[1]
    user_info = verify_access_token(access_token)
    
    if not user_info.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        jobs = await get_user_jobs(user_info.get("username"))
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/progress")
async def get_job_progress_status(job_id: str, authorization: Optional[str] = Header(None)):
    """특정 작업의 진행률 조회"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    access_token = authorization.split(" ")[1]
    user_info = verify_access_token(access_token)
    
    if not user_info.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        progress = await get_job_progress(job_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))