#!/usr/bin/env python3
"""
YouTube Reporter - 메인 실행 파일
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json
import asyncio

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않음")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube Reporter",
    description="YouTube 영상을 분석하여 시각적 보고서를 생성하는 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 워크플로우 import
from app.agents.graph_workflow import YouTubeReporterWorkflow

# 워크플로우 인스턴스
workflow = YouTubeReporterWorkflow()

# 메모리 저장소
jobs: Dict[str, Dict[str, Any]] = {}
results: Dict[str, Dict[str, Any]] = {}

# API 모델
class ProcessRequest(BaseModel):
    youtube_url: HttpUrl

# 백그라운드 작업 함수
async def process_video_task(job_id: str, youtube_url: str):
    """비동기 영상 처리"""
    try:
        print(f"🎬 작업 {job_id} 시작: {youtube_url}")

        # 진행률 업데이트
        jobs[job_id].update({
            "status": "processing",
            "progress": 10,
            "message": "자막 추출 중..."
        })

        # 워크플로우 실행
        result = workflow.process(youtube_url)
        
        # 결과 저장
        results[job_id] = result
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석 완료!",
            "completed_at": datetime.now().isoformat()
        })

        print(f"✅ 작업 {job_id} 완료")

    except Exception as e:
        print(f"❌ 작업 {job_id} 실패: {e}")
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"처리 실패: {str(e)}",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

# API 엔드포인트
@app.get("/")
async def root():
    return {
        "service": "YouTube Reporter",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/api/v1/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """영상 처리 시작"""
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "message": "분석 대기 중...",
        "created_at": datetime.now().isoformat(),
        "youtube_url": str(request.youtube_url)
    }

    background_tasks.add_task(process_video_task, job_id, str(request.youtube_url))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "분석이 시작되었습니다."
    }

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

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job is still processing")

    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job.get("error", "Job failed"))

    if job_id not in results:
        raise HTTPException(status_code=404, detail="Result not found")

    return results[job_id]

@app.get("/api/v1/jobs")
async def list_jobs():
    """모든 작업 목록"""
    return {"jobs": list(jobs.values())}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 YouTube Reporter 시작")
    print("📖 API 문서: http://localhost:8000/docs")
    print("🌐 프론트엔드: http://localhost:3000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)