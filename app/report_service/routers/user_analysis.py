from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from shared_lib.core.auth import get_current_user
from shared_lib.core.database import get_db
from shared_lib.models.database_models import UserAnalysisJob, UserReport, UserAudioFile
from services.database_service import database_service
from services.state_manager import state_manager
#from analyzer_service.services.langgraph_service import langgraph_service
#from services.langgraph_service import call_analyzer

from services.user_s3_service import user_s3_service
from shared_lib.models.auth import SignInRequest
from services.s3_service import s3_service
import httpx

router = APIRouter(prefix="/user", tags=["user-analysis"])

class YouTubeAnalysisRequest:
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url

@router.post("/youtube/analysis")
async def create_youtube_analysis(
    request: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user["user_id"]
        youtube_url = request.get("youtube_url")
        
        if not youtube_url:
            raise HTTPException(status_code=400, detail="youtube_url is required")
        
        job = database_service.create_analysis_job(
            db=db,
            user_id=user_id,
            job_type="youtube",
            input_data={"youtube_url": youtube_url}
        )
        
        state_manager.add_user_active_job(user_id, str(job.id))
        
        background_tasks.add_task(
            run_youtube_analysis,
            str(job.id),
            user_id,
            youtube_url,
            db
        )
        
        return {
            "job_id": str(job.id),
            "status": "processing",
            "message": "YouTube"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"file: {str(e)}")

async def run_youtube_analysis(job_id: str, user_id: str, youtube_url: str, db: Session):
    try:
        #result = await langgraph_service.analyze_youtube_with_fsm(
        #    youtube_url=youtube_url,
        #    job_id=job_id,
        #    user_id=user_id
        #)
        # result = call_analyzer(youtube_url, user_id)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://analyzer_service:8000/analyze",  # 포트와 경로 확인 필요
                json={
                    "youtube_url": youtube_url,
                    "user_id": user_id,
                    "job_id": job_id
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
                       
        if result.get("final_output"):
            report_content = str(result["final_output"])
            s3_key = user_s3_service.upload_user_report(
                user_id=user_id,
                job_id=job_id,
                content=report_content,
                file_type="json"
            )
            
            database_service.create_user_report(
                db=db,
                job_id=job_id,
                user_id=user_id,
                title=f"YouTube Analysis - {job_id}",
                s3_key=s3_key,
                file_type="json"
            )
        
        database_service.update_job_status(db, job_id, "completed", s3_key)
        
        state_manager.remove_user_active_job(user_id, job_id)
        
    except Exception as e:
        database_service.update_job_status(db, job_id, "failed")
        state_manager.remove_user_active_job(user_id, job_id)
        print(f"YouTube: {e}")

@router.get("/jobs")
async def get_my_jobs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    jobs = database_service.get_user_jobs(db, user_id)
    
    return {
        "jobs": [
            {
                "id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "input_data": job.input_data,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    }

@router.get("/jobs/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    job = database_service.get_job_by_id(db, job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    progress = state_manager.get_progress(job_id)
    
    return {
        "job_id": job_id,
        "progress": progress.get("progress", 0) if progress else 0,
        "message": progress.get("message", "") if progress else "",
        "status": job.status
    }

@router.get("/reports")
async def get_my_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    reports = database_service.get_user_reports(db, user_id)
    
    return {
        "reports": [
            {
                "id": str(report.id),
                "job_id": str(report.job_id),
                "title": report.title,
                "file_type": report.file_type,
                "created_at": report.created_at.isoformat()
            }
            for report in reports
        ]
    }

@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    report = db.query(UserReport).filter(
        UserReport.id == report_id,
        UserReport.user_id == user_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    download_url = user_s3_service.get_presigned_url(report.s3_key)
    
    return {
        "download_url": download_url,
        "expires_in": 3600
    }

@router.get("/reports/{report_id}/metadata")
async def get_report_metadata(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    report = db.query(UserReport).filter(
        UserReport.id == report_id,
        UserReport.user_id == user_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        metadata_key = f"metadata/{report.job_id}_metadata.json"
        metadata_content = s3_service.get_file_content(metadata_key)
        
        if metadata_content:
            import json
            metadata = json.loads(metadata_content)
            return metadata
        else:
            return {
                "youtube_url": "",
                "user_id": user_id,
                "job_id": str(report.job_id),
                "timestamp": report.created_at.isoformat(),
                "youtube_title": "",
                "youtube_channel": "",
                "youtube_duration": "",
                "youtube_thumbnail": ""
            }
            
    except Exception as e:
        print(f"file: {e}")
        return {
            "youtube_url": "",
            "user_id": user_id,
            "job_id": str(report.job_id),
            "timestamp": report.created_at.isoformat(),
            "youtube_title": "",
            "youtube_channel": "",
            "youtube_duration": "",
            "youtube_thumbnail": ""
        }

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    success = database_service.delete_job(db, job_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    state_manager.cleanup_job(job_id)
    state_manager.remove_user_active_job(user_id, job_id)
    
    return {"message": "Job deleted successfully"}
