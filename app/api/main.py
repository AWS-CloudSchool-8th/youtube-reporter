# app/api/main.py (MVC 적용 버전)
import os
import sys
from pathlib import Path

# 환경 변수 먼저 로드
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다.")

# Python 경로 설정
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

print(f"📁 Python 경로에 추가됨: {app_root}")

# FastAPI 및 기본 라이브러리
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uuid
from datetime import datetime

# 환경 변수 검증
try:
    from utils.env_validator import check_environment_comprehensive

    if not check_environment_comprehensive():
        print("❌ 환경 변수 검증 실패!")
        sys.exit(1)
except ImportError as e:
    print(f"❌ utils.env_validator import 실패: {e}")
    sys.exit(1)

# MVC 모듈들 import
try:
    from controllers.report_controller import ReportController
    from views.schemas import ProcessVideoRequest, ProcessVideoResponse, ReportResponse
    from utils.logger import setup_logger

    print("✅ MVC 모듈 import 성공!")
except ImportError as e:
    print(f"❌ MVC 모듈 import 실패: {e}")
    print("현재 작업 디렉토리:", os.getcwd())
    sys.exit(1)

# 로거 및 컨트롤러 설정
logger = setup_logger(__name__)
report_controller = ReportController()

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube Reporter API (MVC)",
    description="MVC 패턴을 적용한 YouTube 영상 분석 API",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 작업 상태 저장소 (기존 호환성 유지)
jobs: Dict[str, Dict[str, Any]] = {}


# 백그라운드 작업 함수 (MVC 버전)
async def process_video_background_mvc(job_id: str, request: ProcessVideoRequest):
    """MVC 패턴을 사용한 백그라운드 작업"""
    try:
        logger.info(f"Job {job_id} started (MVC) for URL: {request.youtube_url}")

        # 작업 상태 업데이트
        jobs[job_id].update({
            "status": "processing",
            "progress": 20,
            "message": "MVC 컨트롤러로 처리 중..."
        })

        # MVC 컨트롤러로 처리
        result = await report_controller.process_video(request)

        # 완료 상태 업데이트
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석이 완료되었습니다!",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })

        logger.info(f"Job {job_id} completed successfully (MVC)")

    except Exception as e:
        logger.error(f"Job {job_id} failed (MVC): {str(e)}")
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"처리 중 오류가 발생했습니다: {str(e)}",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


# API 엔드포인트들
@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "YouTube Reporter API (MVC Pattern)",
        "version": "2.0.0",
        "status": "running",
        "architecture": "MVC",
        "endpoints": {
            "docs": "/docs",
            "process": "/api/v1/process",
            "reports": "/api/v1/reports",
            "jobs": "/api/v1/jobs"
        }
    }


@app.post("/api/v1/process", response_model=ProcessVideoResponse)
async def process_youtube_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """YouTube 영상 처리 시작 (MVC 버전)"""
    try:
        # 작업 ID 생성
        job_id = str(uuid.uuid4())

        # 작업 정보 저장
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "MVC 패턴으로 작업이 대기열에 추가되었습니다.",
            "created_at": datetime.now().isoformat(),
            "youtube_url": str(request.youtube_url),
            "options": request.options
        }

        # MVC 백그라운드 작업 시작
        background_tasks.add_task(
            process_video_background_mvc,
            job_id,
            request
        )

        logger.info(f"Created MVC job {job_id} for URL: {request.youtube_url}")

        return ProcessVideoResponse(
            job_id=job_id,
            report_id="",  # 처리 완료 후 설정됨
            status="queued",
            message="MVC 패턴으로 작업이 시작되었습니다."
        )

    except Exception as e:
        logger.error(f"Failed to create MVC job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 기존 job 관련 엔드포인트들 (호환성 유지)
@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/v1/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """작업 결과 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs[job_id]

    if job_data["status"] in ["processing", "queued"]:
        raise HTTPException(status_code=202, detail="Job is still processing")

    if job_data["status"] == "failed":
        raise HTTPException(status_code=500, detail=job_data.get("error", "Job failed"))

    return job_data.get("result", {})


@app.get("/api/v1/jobs")
async def list_jobs():
    """모든 작업 목록 조회"""
    return {"jobs": list(jobs.values()), "total": len(jobs)}


# 새로운 MVC 엔드포인트들
@app.get("/api/v1/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """보고서 상세 조회 (새로운 MVC 엔드포인트)"""
    try:
        report = report_controller.get_report(report_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports", response_model=list[ReportResponse])
async def list_reports():
    """모든 보고서 목록 조회 (새로운 MVC 엔드포인트)"""
    try:
        reports = report_controller.list_reports()
        return reports
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """작업 삭제"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    print("🚀 YouTube Reporter API 서버 시작 (MVC Pattern)")
    print("📖 API 문서: http://localhost:8000/docs")
    print("🏗️ 아키텍처: MVC")
    print("🌐 메인 페이지: http://localhost:8000")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )