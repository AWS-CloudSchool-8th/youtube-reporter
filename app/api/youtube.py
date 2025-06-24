# app/api/youtube.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
from ..models.request import ProcessVideoRequest
from ..models.response import (
    ProcessVideoResponse, JobStatusResponse, ReportResult,
    ErrorResponse, JobStatus
)
from ..services.youtube_service import YouTubeService
from ..core.dependencies import get_youtube_service, validate_youtube_url
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["YouTube Reporter"])


@router.get("/")
async def health_check():
    """API 상태 확인"""
    return {
        "service": "YouTube Reporter",
        "status": "running",
        "version": "2.0.0",
        "description": "AI 기반 YouTube 영상 분석 및 스마트 시각화 도구",
        "features": [
            "포괄적 요약 생성",
            "스마트 시각화",
            "컨텍스트 기반 분석",
            "다양한 차트 및 다이어그램 지원"
        ],
        "endpoints": {
            "process": "POST /api/v1/process - 영상 처리 시작",
            "status": "GET /api/v1/jobs/{job_id}/status - 작업 상태 조회",
            "result": "GET /api/v1/jobs/{job_id}/result - 작업 결과 조회",
            "jobs": "GET /api/v1/jobs - 작업 목록 조회",
            "stats": "GET /api/v1/stats - 서비스 통계"
        }
    }


@router.post("/process", response_model=ProcessVideoResponse)
async def process_video(
        request: ProcessVideoRequest,
        background_tasks: BackgroundTasks,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """YouTube 영상 처리 시작"""
    try:
        # URL 검증
        url_str = str(request.youtube_url)
        validate_youtube_url(url_str)

        # 작업 생성
        job_id = youtube_service.create_job(url_str)

        # 백그라운드에서 처리
        background_tasks.add_task(
            youtube_service.process_video,
            job_id,
            url_str
        )

        logger.info(f"🚀 영상 처리 작업 시작: {job_id}")

        return ProcessVideoResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            message="🚀 분석이 시작되었습니다. AI가 영상을 분석하고 스마트 시각화를 생성하는 중입니다..."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 영상 처리 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
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
        logger.error(f"❌ 작업 상태 조회 실패: {e}")
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

        if job_status.status == JobStatus.PROCESSING:
            raise HTTPException(
                status_code=202,
                detail="아직 처리 중입니다. 잠시 후 다시 시도해주세요."
            )
        elif job_status.status == JobStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=job_status.error or "작업이 실패했습니다."
            )
        elif job_status.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"작업 상태: {job_status.status}"
            )

        result = youtube_service.get_job_result(job_id)

        # 결과 통계 로깅
        logger.info(f"📊 작업 {job_id} 결과 반환:")
        logger.info(f"  - 제목: {result.title}")
        logger.info(f"  - 전체 섹션: {result.statistics.total_sections}개")
        logger.info(f"  - 시각화: {result.statistics.visualizations}개")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 작업 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
        limit: int = 20,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """모든 작업 목록"""
    try:
        # 오래된 작업 정리
        youtube_service.cleanup_old_jobs()
        jobs = youtube_service.list_jobs(limit=limit)

        return jobs

    except Exception as e:
        logger.error(f"❌ 작업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_service_stats(
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """서비스 통계 정보"""
    try:
        return youtube_service.get_service_stats()
    except Exception as e:
        logger.error(f"❌ 서비스 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(
        job_id: str,
        youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """작업 삭제 (관리용)"""
    try:
        # 작업 존재 확인
        youtube_service.get_job_status(job_id)

        # 현재는 메모리에서만 관리하므로 cleanup_old_jobs에 의존
        # TODO: 실제 삭제 로직 구현

        return {"message": f"작업 {job_id} 삭제 예약됨"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 작업 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 추가 유틸리티 엔드포인트들
@router.get("/validate-url")
async def validate_youtube_url_endpoint(url: str):
    """YouTube URL 유효성 검증 엔드포인트"""
    try:
        from ..utils.helpers import validate_youtube_url as validate_url_helper

        is_valid = validate_url_helper(url)
        video_id = None

        if is_valid:
            from ..utils.helpers import extract_youtube_video_id
            video_id = extract_youtube_video_id(url)

        return {
            "url": url,
            "is_valid": is_valid,
            "video_id": video_id,
            "message": "유효한 YouTube URL입니다." if is_valid else "유효하지 않은 YouTube URL입니다."
        }

    except Exception as e:
        logger.error(f"❌ URL 검증 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info():
    """시스템 정보 조회"""
    import sys
    import platform
    from datetime import datetime
    from ..core.config import settings

    try:
        return {
            "system": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
            },
            "application": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug_mode": settings.debug,
                "log_level": settings.log_level,
            },
            "configuration": {
                "aws_region": settings.aws_region,
                "bedrock_model": settings.bedrock_model_id,
                "features_enabled": {
                    "vidcap_api": bool(settings.vidcap_api_key),
                    "aws_bedrock": bool(settings.aws_region and settings.bedrock_model_id),
                    "s3_storage": bool(settings.s3_bucket_name),
                    "openai_integration": bool(settings.openai_api_key),
                    "langchain_tracing": settings.langchain_tracing_v2
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 시스템 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_pipeline():
    """파이프라인 테스트용 엔드포인트 (개발용)"""
    try:
        from ..services.langgraph_service import LangGraphService

        service = LangGraphService()
        pipeline_status = service.get_pipeline_status()

        return {
            "message": "파이프라인이 정상적으로 초기화되었습니다.",
            "pipeline_info": pipeline_status,
            "test_status": "success"
        }

    except Exception as e:
        logger.error(f"❌ 파이프라인 테스트 실패: {e}")
        return {
            "message": f"파이프라인 테스트 실패: {str(e)}",
            "test_status": "failed",
            "error": str(e)
        }


# 에러 핸들러 (전역 에러 처리)
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    logger.warning(f"HTTP 예외 발생: {exc.status_code} - {exc.detail}")
    return ErrorResponse(
        detail=exc.detail,
        error_code=str(exc.status_code)
    )


@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """값 오류 처리"""
    logger.warning(f"값 오류: {str(exc)}")
    return ErrorResponse(
        detail=str(exc),
        error_code="400"
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"❌ 예상치 못한 오류: {exc}", exc_info=True)
    return ErrorResponse(
        detail="내부 서버 오류가 발생했습니다.",
        error_code="500"
    )