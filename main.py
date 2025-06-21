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
        # asyncio 타임아웃 설정
        await asyncio.sleep(0.1)  # 초기 지연
        print(f"🎬 작업 {job_id} 시작: {youtube_url}")

        # 워크플로우 실행 with 진행률 업데이트
        try:
            # 1단계: 자막 추출 시작
            jobs[job_id].update({
                "status": "processing",
                "progress": 25,
                "message": "📝 자막을 추출하고 있습니다..."
            })
            await asyncio.sleep(1)  # 실제 처리 시간 시뮬레이션
            
            # 2단계: 요약 생성 시작
            jobs[job_id].update({
                "progress": 50,
                "message": "🧠 AI가 영상 내용을 요약하고 있습니다..."
            })
            await asyncio.sleep(1)
            
            # 3단계: 시각화 생성 시작
            jobs[job_id].update({
                "progress": 75,
                "message": "📊 시각화 데이터를 생성하고 있습니다..."
            })
            await asyncio.sleep(0.5)
            
            # 실제 워크플로우 실행
            result = workflow.process(youtube_url)
            
            # 결과 검증
            if not result or not isinstance(result, dict):
                result = {"error": "워크플로우 결과가 비어있습니다"}
            
            # 결과 저장
            results[job_id] = result
        except Exception as workflow_error:
            print(f"워크플로우 실행 오류: {workflow_error}")
            results[job_id] = {"error": f"워크플로우 오류: {str(workflow_error)}"}
        # 완료 처리
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "🎉 분석이 완료되었습니다!",
            "completed_at": datetime.now().isoformat()
        })

        print(f"✅ 작업 {job_id} 완료")

    except Exception as e:
        print(f"❌ 작업 {job_id} 실패: {e}")
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"❌ 처리 실패: {str(e)}",
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

@app.get("/api/v1/")
async def api_root():
    return {
        "service": "YouTube Reporter API",
        "status": "running",
        "version": "1.0.0"
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
    
    # Windows에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 연결 오류 무시 설정
    import logging
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    
    uvicorn.run(
        app, 
        host="127.0.0.1",  # localhost로 변경
        port=8000, 
        reload=False,
        access_log=False,
        log_level="error"
    )