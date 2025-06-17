# app/api/main.py
import os
import sys
from pathlib import Path

# 환경 변수 먼저 로드
try:
    from dotenv import load_dotenv

    # app 폴더의 .env 파일 로드
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다.")

# Python 경로 설정 - app 폴더를 sys.path에 추가
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

print(f"📁 Python 경로에 추가됨: {app_root}")
print(f"🔍 현재 작업 디렉토리: {os.getcwd()}")

# FastAPI 및 기본 라이브러리
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
import asyncio
import json
import uuid
from datetime import datetime

# 환경 변수 검증
try:
    from utils.env_validator import check_environment_comprehensive

    if not check_environment_comprehensive():
        print("❌ 환경 변수 검증 실패! .env 파일을 확인하세요.")
        sys.exit(1)
except ImportError as e:
    print(f"❌ utils.env_validator import 실패: {e}")
    print("📁 app 폴더에서 실행하고 있는지 확인하세요.")
    sys.exit(1)

# 핵심 모듈들 import
try:
    from core.workflow.fsm import run_graph
    from utils.logger import setup_logger

    print("✅ 모든 모듈 import 성공!")
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("📋 현재 sys.path:")
    for path in sys.path:
        print(f"  - {path}")
    sys.exit(1)

# 로거 설정
logger = setup_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube Reporter API",
    description="YouTube 영상을 분석하여 시각적 보고서를 생성하는 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메모리 저장소 (실제 운영에서는 Redis나 DB 사용)
jobs: Dict[str, Dict[str, Any]] = {}


# 요청/응답 모델
class ProcessRequest(BaseModel):
    youtube_url: HttpUrl
    options: Optional[Dict[str, Any]] = {}


class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# 백그라운드 작업 함수
async def process_video_background(job_id: str, youtube_url: str, options: Dict[str, Any]):
    """백그라운드에서 YouTube 영상 처리"""
    try:
        logger.info(f"Job {job_id} started for URL: {youtube_url}")

        # 작업 상태 업데이트
        jobs[job_id].update({
            "status": "processing",
            "progress": 10,
            "message": "YouTube 영상을 분석하고 있습니다..."
        })

        # 실제 처리 (동기 함수를 비동기로 실행)
        result = await asyncio.to_thread(run_graph, str(youtube_url))

        # 완료 상태 업데이트
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석이 완료되었습니다!",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
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
        "message": "YouTube Reporter API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "process": "/api/v1/process",
            "jobs": "/api/v1/jobs"
        }
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_youtube_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """YouTube 영상 처리 시작"""
    try:
        # 작업 ID 생성
        job_id = str(uuid.uuid4())

        # 작업 정보 저장
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "작업이 대기열에 추가되었습니다.",
            "created_at": datetime.now().isoformat(),
            "youtube_url": str(request.youtube_url),
            "options": request.options
        }

        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_video_background,
            job_id,
            str(request.youtube_url),
            request.options
        )

        logger.info(f"Created job {job_id} for URL: {request.youtube_url}")

        return ProcessResponse(
            job_id=job_id,
            status="queued",
            message="작업이 시작되었습니다."
        )

    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs[job_id]
    return JobStatus(**job_data)


@app.get("/api/v1/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """작업 결과 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs[job_id]

    if job_data["status"] == "processing" or job_data["status"] == "queued":
        raise HTTPException(status_code=202, detail="Job is still processing")

    if job_data["status"] == "failed":
        raise HTTPException(status_code=500, detail=job_data.get("error", "Job failed"))

    return job_data.get("result", {})


@app.get("/api/v1/jobs")
async def list_jobs():
    """모든 작업 목록 조회"""
    return {
        "jobs": list(jobs.values()),
        "total": len(jobs)
    }


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """작업 삭제"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    print("🚀 YouTube Reporter API 서버 시작")
    print("📖 API 문서: http://localhost:8000/docs")
    print("🌐 메인 페이지: http://localhost:8000")

    # 서버 실행 - 현재 모듈의 app 객체 직접 참조
    uvicorn.run(
        app,  # "main:app" 대신 app 객체 직접 전달
        host="0.0.0.0",
        port=8000,
        reload=False,  # 직접 객체 전달시 reload=False
        log_level="info"
    )