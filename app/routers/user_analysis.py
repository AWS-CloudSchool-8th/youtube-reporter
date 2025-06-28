from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.database_models import UserAnalysisJob, UserReport, UserAudioFile
from app.services.database_service import database_service
from app.services.state_manager import state_manager
from app.services.user_s3_service import user_s3_service
from app.services.youtube_reporter_service import youtube_reporter_service
from app.models.auth import SignInRequest
from app.services.s3_service import s3_service

router = APIRouter(prefix="/user", tags=["user-analysis"])

@router.post("/youtube/analysis")
async def create_youtube_analysis(
    request: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자별 YouTube 분석 작업 생성 (YouTube Reporter 통합)"""
    try:
        user_id = current_user["user_id"]
        youtube_url = request.get("youtube_url")
        include_audio = request.get("include_audio", True)
        
        if not youtube_url:
            raise HTTPException(status_code=400, detail="youtube_url is required")
        
        # YouTube Reporter 서비스 사용
        job_id = await youtube_reporter_service.create_analysis_job(
            user_id=user_id,
            youtube_url=youtube_url,
            db=db,
            include_audio=include_audio
        )
        
        # 백그라운드에서 분석 실행
        background_tasks.add_task(
            run_youtube_reporter_analysis,
            job_id,
            user_id,
            youtube_url,
            include_audio,
            db
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "🚀 YouTube Reporter 분석이 시작되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 작업 생성 실패: {str(e)}")

async def run_youtube_reporter_analysis(job_id: str, user_id: str, youtube_url: str, include_audio: bool, db: Session):
    """백그라운드 YouTube Reporter 분석 실행"""
    try:
        await youtube_reporter_service.process_youtube_analysis(
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            db=db,
            include_audio=include_audio
        )
    except Exception as e:
        print(f"YouTube Reporter 분석 실패: {e}")

@router.get("/jobs")
async def get_my_jobs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 작업 목록 조회 (모든 타입 통합)"""
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
    """작업 진행률 조회 (모든 타입 통합)"""
    user_id = current_user["user_id"]
    
    # 권한 확인
    job = database_service.get_job_by_id(db, job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # YouTube Reporter 진행률 조회
    if job.job_type == "youtube_reporter":
        progress_info = youtube_reporter_service.get_job_progress(job_id)
        return {
            "job_id": job_id,
            "progress": progress_info.get("progress", 0),
            "message": progress_info.get("message", ""),
            "status": job.status
        }
    
    # 기존 방식 (Redis)
    progress = state_manager.get_progress(job_id)
    return {
        "job_id": job_id,
        "progress": progress.get("progress", 0) if progress else 0,
        "message": progress.get("message", "") if progress else "",
        "status": job.status
    }

@router.get("/jobs/{job_id}/result")
async def get_job_result(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """작업 결과 조회 (모든 타입 통합)"""
    user_id = current_user["user_id"]
    
    # 권한 확인
    job = database_service.get_job_by_id(db, job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(status_code=202, detail="Job not completed yet")
    
    # 보고서 조회
    reports = database_service.get_user_reports(db, user_id)
    job_report = next((r for r in reports if str(r.job_id) == job_id), None)
    
    if not job_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # S3에서 내용 가져오기
    try:
        from app.core.redis_client import redis_client
        import json
        
        download_url = user_s3_service.get_presigned_url(job_report.s3_key)
        
        # Redis 캐시 확인
        cache_key = f"report_content:{job_id}"
        report_content = None
        
        try:
            cached_content = redis_client.get(cache_key)
            if cached_content:
                report_content = cached_content
            else:
                content = user_s3_service.get_file_content(job_report.s3_key)
                if content and job_report.file_type == 'json':
                    report_content = json.loads(content)
                    redis_client.set_with_ttl(cache_key, report_content, 3600)
        except Exception as e:
            print(f"리포트 내용 조회 실패: {e}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "title": job_report.title,
            "created_at": job_report.created_at.isoformat(),
            "download_url": download_url,
            "s3_key": job_report.s3_key,
            "file_type": job_report.file_type,
            "content": report_content,
            "message": "✅ 분석이 완료되었습니다!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 조회 실패: {str(e)}")

@router.get("/reports")
async def get_my_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 보고서 목록"""
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
    """보고서 다운로드 URL 생성"""
    user_id = current_user["user_id"]
    
    # 보고서 조회 및 권한 확인
    report = db.query(UserReport).filter(
        UserReport.id == report_id,
        UserReport.user_id == user_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 사전 서명된 URL 생성
    download_url = user_s3_service.get_presigned_url(report.s3_key)
    
    return {
        "download_url": download_url,
        "expires_in": 3600
    }

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """작업 삭제 (모든 타입 통합)"""
    user_id = current_user["user_id"]
    
    success = database_service.delete_job(db, job_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Redis 정리
    state_manager.cleanup_job(job_id)
    state_manager.remove_user_active_job(user_id, job_id)
    
    return {"message": "Job deleted successfully"}