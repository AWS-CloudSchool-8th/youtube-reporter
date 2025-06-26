from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from typing import List, Optional
from datetime import datetime

from app.models.analysis import (
    VideoInfo, SearchRequest, YouTubeAnalysisRequest,
    DocumentAnalysisRequest, AnalysisResponse
)
from app.services.s3_service import s3_service
from app.services.audio_service import audio_service
from app.services.analysis_service import analysis_service
from app.core.config import settings

router = APIRouter(prefix="/analysis", tags=["analysis"])

# 분석 작업 저장소
analysis_jobs = {}

@router.get("/")
async def list_analysis_jobs():
    """모든 분석 작업 목록 조회"""
    jobs_list = []
    for job_id, job in analysis_jobs.items():
        job_info = {
            "job_id": job_id,
            "status": job["status"],
            "current_step": job.get("current_step"),
            "progress": job.get("progress", 0),
            "input_type": job["input_type"],
            "search_query": job.get("search_query"),
            "file_name": job.get("file_name"),
            "created_at": job["created_at"],
            "completed_at": job.get("completed_at"),
            "has_s3_report": False,
            "has_audio": False
        }
        
        if job.get("result"):
            s3_info = job["result"].get("s3_info", {})
            audio_info = job["result"].get("audio_info", {})
            
            job_info["has_s3_report"] = s3_info.get("success", False)
            job_info["has_audio"] = audio_info.get("success", False)
            
            if s3_info.get("success"):
                job_info["report_id"] = s3_info.get("report_id")
            
            if audio_info.get("success"):
                job_info["audio_s3_key"] = audio_info.get("audio_s3_key")
        
        jobs_list.append(job_info)
    
    return {
        "total_jobs": len(jobs_list),
        "jobs": sorted(jobs_list, key=lambda x: x["created_at"], reverse=True),
        "summary": {
            "with_s3_reports": len([j for j in jobs_list if j["has_s3_report"]]),
            "with_audio": len([j for j in jobs_list if j["has_audio"]]),
            "completed": len([j for j in jobs_list if j["status"] == "completed"]),
            "processing": len([j for j in jobs_list if j["status"] == "processing"])
        }
    }

@router.get("/{job_id}", response_model=AnalysisResponse)
async def get_analysis_status(job_id: str):
    """분석 작업 상태 및 결과 조회"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    job = analysis_jobs[job_id]
    
    return AnalysisResponse(
        request_id=job["request_id"],
        status=job["status"],
        current_step=job.get("current_step"),
        progress=job.get("progress", 0),
        input_type=job["input_type"],
        result=job.get("result"),
        s3_info=job.get("result", {}).get("s3_info") if job.get("result") else None,
        audio_info=job.get("result", {}).get("audio_info") if job.get("result") else None,
        error=job.get("error"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )

@router.delete("/{job_id}")
async def delete_analysis_job(job_id: str, delete_s3_files: bool = Query(False)):
    """분석 작업 삭제 (선택적으로 S3 파일도 삭제)"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    job = analysis_jobs[job_id]
    deleted_files = []
    
    # S3 파일 삭제 (옵션)
    if delete_s3_files and job.get("result"):
        try:
            s3_info = job["result"].get("s3_info", {})
            audio_info = job["result"].get("audio_info", {})
            
            # 보고서 파일 삭제
            if s3_info.get("s3_key"):
                await s3_service.delete_report(s3_info["s3_key"])
                deleted_files.append(s3_info["s3_key"])
            
            if s3_info.get("text_s3_key"):
                await s3_service.delete_report(s3_info["text_s3_key"])
                deleted_files.append(s3_info["text_s3_key"])
            
            # 오디오 파일 삭제
            if audio_info.get("audio_s3_key"):
                await s3_service.delete_report(audio_info["audio_s3_key"])
                deleted_files.append(audio_info["audio_s3_key"])
                
        except Exception as e:
            print(f"S3 파일 삭제 중 오류: {e}")
    
    # 작업 삭제
    del analysis_jobs[job_id]
    
    return {
        "message": f"작업 {job_id}가 삭제되었습니다.",
        "deleted_s3_files": deleted_files if delete_s3_files else [],
        "s3_deletion_requested": delete_s3_files
    }

@router.get("/health")
async def health_check():
    """시스템 상태 확인"""
    # S3 연결 테스트
    s3_status = False
    try:
        s3_service.s3_client.head_bucket(Bucket=s3_service.bucket_name)
        s3_status = True
    except:
        s3_status = False
    
    # Polly 연결 테스트
    polly_status = False
    try:
        audio_service.polly_client.describe_voices(LanguageCode='ko-KR')
        polly_status = True
    except:
        polly_status = False
    
    return {
        "status": "healthy",
        "services": {
            "s3_available": s3_status,
            "polly_available": polly_status,
            "vidcap_api_configured": bool(settings.VIDCAP_API_KEY)
        },
        "storage": {
            "s3_bucket": settings.S3_BUCKET_NAME,
            "aws_region": settings.AWS_REGION
        },
        "audio": {
            "default_voice": settings.POLLY_VOICE_ID,
            "supported_voices": ["Seoyeon"] if polly_status else []
        },
        "active_jobs": len([job for job in analysis_jobs.values() if job["status"] == "processing"]),
        "total_jobs": len(analysis_jobs),
        "supported_formats": [".pdf", ".docx", ".xlsx", ".csv", ".txt"],
        "timestamp": datetime.now().isoformat()
    } 