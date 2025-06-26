from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.database_models import UserAnalysisJob, UserReport, UserAudioFile
from app.services.database_service import database_service
from app.services.state_manager import state_manager
from app.services.langgraph_service import langgraph_service
from app.services.user_s3_service import user_s3_service
from app.models.auth import SignInRequest
from app.services.s3_service import s3_service

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
    """사용자별 YouTube 분석 작업 생성"""
    try:
        user_id = current_user["user_id"]
        youtube_url = request.get("youtube_url")
        
        if not youtube_url:
            raise HTTPException(status_code=400, detail="youtube_url is required")
        
        # 데이터베이스에 작업 생성
        job = database_service.create_analysis_job(
            db=db,
            user_id=user_id,
            job_type="youtube",
            input_data={"youtube_url": youtube_url}
        )
        
        # Redis에 활성 작업 추가
        state_manager.add_user_active_job(user_id, str(job.id))
        
        # 백그라운드에서 분석 실행
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
            "message": "YouTube 분석이 시작되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 작업 생성 실패: {str(e)}")

async def run_youtube_analysis(job_id: str, user_id: str, youtube_url: str, db: Session):
    """백그라운드 YouTube 분석 실행"""
    try:
        # LangGraph FSM 분석 실행
        result = await langgraph_service.analyze_youtube_with_fsm(
            youtube_url=youtube_url,
            job_id=job_id,
            user_id=user_id
        )
        
        # 보고서 S3 업로드
        if result.get("final_output"):
            report_content = str(result["final_output"])
            s3_key = user_s3_service.upload_user_report(
                user_id=user_id,
                job_id=job_id,
                content=report_content,
                file_type="json"
            )
            
            # 데이터베이스에 보고서 정보 저장
            database_service.create_user_report(
                db=db,
                job_id=job_id,
                user_id=user_id,
                title=f"YouTube Analysis - {job_id}",
                s3_key=s3_key,
                file_type="json"
            )
        
        # 작업 상태 업데이트
        database_service.update_job_status(db, job_id, "completed", s3_key)
        
        # Redis에서 활성 작업 제거
        state_manager.remove_user_active_job(user_id, job_id)
        
    except Exception as e:
        # 실패 시 상태 업데이트
        database_service.update_job_status(db, job_id, "failed")
        state_manager.remove_user_active_job(user_id, job_id)
        print(f"YouTube 분석 실패: {e}")

@router.get("/jobs")
async def get_my_jobs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 작업 목록 조회"""
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
    """작업 진행률 조회"""
    user_id = current_user["user_id"]
    
    # 권한 확인
    job = database_service.get_job_by_id(db, job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Redis에서 진행률 조회
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

@router.get("/reports/{report_id}/metadata")
async def get_report_metadata(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """보고서 메타데이터 조회 (YouTube 정보 포함)"""
    user_id = current_user["user_id"]
    
    # 보고서 조회 및 권한 확인
    report = db.query(UserReport).filter(
        UserReport.id == report_id,
        UserReport.user_id == user_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        # 메타데이터 파일 조회
        metadata_key = f"metadata/{report.job_id}_metadata.json"
        metadata_content = s3_service.get_file_content(metadata_key)
        
        if metadata_content:
            import json
            metadata = json.loads(metadata_content)
            return metadata
        else:
            # 메타데이터가 없으면 기본 정보만 반환
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
        print(f"메타데이터 조회 실패: {e}")
        # 기본 정보만 반환
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
    """작업 삭제"""
    user_id = current_user["user_id"]
    
    success = database_service.delete_job(db, job_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Redis 정리
    state_manager.cleanup_job(job_id)
    state_manager.remove_user_active_job(user_id, job_id)
    
    return {"message": "Job deleted successfully"}