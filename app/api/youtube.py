# app/api/youtube.py - 완전 비동기 버전
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import asyncio
import os
import sys
import platform
from datetime import datetime
from ..models.request import ProcessVideoRequest
from ..models.response import ProcessVideoResponse, JobStatus, ReportResult
from ..services.youtube_service import YouTubeService
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["YouTube Reporter"])

# 싱글톤 서비스 인스턴스
_youtube_service = None


def get_youtube_service() -> YouTubeService:
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service


def validate_youtube_url(url: str):
    """YouTube URL 유효성 검증"""
    if not ('youtube.com' in url or 'youtu.be' in url):
        raise HTTPException(status_code=400, detail="유효한 YouTube URL이 아닙니다.")


@router.get("/")
async def health_check():
    """API 상태 확인"""
    return {
        "service": "YouTube Reporter",
        "status": "running",
        "version": "2.0.0",
        "mode": "async",
        "description": "AI 기반 YouTube 영상 분석 및 스마트 시각화 도구",
        "features": [
            "포괄적 요약 생성",
            "스마트 시각화",
            "컨텍스트 기반 분석",
            "다양한 차트 및 다이어그램 지원",
            "완전 비동기 처리"
        ]
    }


@router.post("/process", response_model=ProcessVideoResponse)
async def process_video(
        request: ProcessVideoRequest,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """YouTube 영상 처리 시작"""
    try:
        url_str = str(request.youtube_url)
        validate_youtube_url(url_str)

        job_id = youtube_service.create_job(url_str)

        asyncio.create_task(
            youtube_service.process_video(job_id, url_str)
        )

        logger.info(f"영상 처리 작업 시작: {job_id}")

        return ProcessVideoResponse(
            job_id=job_id,
            status="queued",
            message="🚀 분석이 시작되었습니다. AI가 영상을 분석하고 스마트 시각화를 생성하는 중입니다..."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"영상 처리 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(
        job_id: str,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """작업 상태 조회"""
    try:
        return youtube_service.get_job_status(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/result", response_model=ReportResult)
async def get_job_result(
        job_id: str,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """작업 결과 조회"""
    try:
        job_status = youtube_service.get_job_status(job_id)

        if job_status.status == "processing":
            raise HTTPException(
                status_code=202,
                detail="아직 처리 중입니다. 잠시 후 다시 시도해주세요."
            )
        elif job_status.status == "failed":
            raise HTTPException(
                status_code=500,
                detail=job_status.error or "작업이 실패했습니다."
            )
        elif job_status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"작업 상태: {job_status.status}"
            )

        result = youtube_service.get_job_result(job_id)

        logger.info(f"작업 {job_id} 결과 반환:")
        logger.info(f"  - 제목: {result.title}")
        logger.info(f"  - 전체 섹션: {result.statistics.get('total_sections', 0)}개")
        logger.info(f"  - 시각화: {result.statistics.get('visualizations', 0)}개")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"작업 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(
        limit: int = 20,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """모든 작업 목록"""
    try:
        youtube_service.cleanup_old_jobs()
        jobs = youtube_service.list_jobs()
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        return {
            "jobs": jobs[:limit],
            "total": len(jobs)
        }
    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-url")
async def validate_youtube_url_endpoint(url: str):
    """YouTube URL 유효성 검증 엔드포인트"""
    try:
        is_valid = 'youtube.com' in url or 'youtu.be' in url
        return {
            "url": url,
            "is_valid": is_valid,
            "message": "유효한 YouTube URL입니다." if is_valid else "유효하지 않은 YouTube URL입니다."
        }
    except Exception as e:
        logger.error(f"URL 검증 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info():
    """시스템 정보 조회"""
    try:
        return {
            "system": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
            },
            "application": {
                "name": "YouTube Reporter",
                "version": "2.0.0",
                "mode": "async"
            },
            "configuration": {
                "features_enabled": {
                    "vidcap_api": bool(os.getenv("VIDCAP_API_KEY")),
                    "aws_bedrock": bool(os.getenv("AWS_BEDROCK_MODEL_ID")),
                    "langchain_tracing": bool(os.getenv("LANGCHAIN_TRACING_V2"))
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"시스템 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(
        job_id: str,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """작업 삭제"""
    try:
        youtube_service.get_job_status(job_id)
        return {"message": f"작업 {job_id} 삭제 예약됨"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"작업 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))