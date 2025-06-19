# app/controllers/youtube_controller.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ..models.request_models import ProcessVideoRequest
from ..models.response_models import ProcessVideoResponse, JobStatus, ReportResult
from ..services.youtube_service import YouTubeService
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["YouTube Reporter"])


# 서비스 의존성
def get_youtube_service() -> YouTubeService:
    return YouTubeService()


@router.get("/")
async def health_check():
    """API 상태 확인"""
    return {
        "service": "YouTube Reporter",
        "status": "running",
        "version": "1.0.0"
    }


@router.post("/process", response_model=ProcessVideoResponse)
async def process_video(
        request: ProcessVideoRequest,
        background_tasks: BackgroundTasks,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """YouTube 영상 처리 시작"""
    try:
        # 작업 생성
        job_id = youtube_service.create_job(str(request.youtube_url))

        # 백그라운드에서 처리
        background_tasks.add_task(
            youtube_service.process_video,
            job_id,
            str(request.youtube_url)
        )

        return ProcessVideoResponse(
            job_id=job_id,
            status="queued",
            message="분석이 시작되었습니다."
        )

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
        # 상태 먼저 확인
        job_status = youtube_service.get_job_status(job_id)

        if job_status.status == "processing":
            raise HTTPException(status_code=202, detail="Job is still processing")
        elif job_status.status == "failed":
            raise HTTPException(status_code=500, detail=job_status.error or "Job failed")
        elif job_status.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job status: {job_status.status}")

        return youtube_service.get_job_result(job_id)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"작업 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(youtube_service: YouTubeService = Depends(get_youtube_service)):
    """모든 작업 목록"""
    try:
        jobs = youtube_service.list_jobs()
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))