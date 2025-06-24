#!/usr/bin/env python3
"""
YouTube Reporter - 메인 실행 파일
포괄적 요약과 스마트 시각화를 제공하는 YouTube 영상 분석 도구
"""
import os
import sys
from pathlib import Path
from datetime import datetime
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

# 컨트롤러 import
from app.controllers import youtube_router
from app.utils.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 환경 변수 검증
try:
    Config.validate()
except ValueError as e:
    logger.error(f"환경 변수 오류: {e}")
    sys.exit(1)

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube Reporter",
    description="AI 기반 YouTube 영상 분석 및 스마트 시각화 도구",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(youtube_router)


# 루트 경로
@app.get("/", include_in_schema=False)
async def root():
    """루트 경로 - API 문서로 리다이렉트"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "YouTube Reporter",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "comprehensive_summary": True,
            "smart_visualization": True,
            "context_analysis": True,
            "multiple_viz_types": ["charts", "diagrams", "tables", "advanced"]
        }
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("=" * 60)
    logger.info("🚀 YouTube Reporter 서버 시작")
    logger.info(f"📖 API 문서: http://localhost:8000/docs")
    logger.info(f"🌐 프론트엔드 연결 대상: http://localhost:3000")
    logger.info("=" * 60)

    # 환경 변수 확인
    logger.info("환경 변수 설정 상태:")
    logger.info(f"  - VIDCAP_API_KEY: {'✅' if os.getenv('VIDCAP_API_KEY') else '❌'}")
    logger.info(f"  - AWS_REGION: {os.getenv('AWS_REGION', '❌')}")
    logger.info(f"  - AWS_BEDROCK_MODEL_ID: {os.getenv('AWS_BEDROCK_MODEL_ID', '❌')}")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("🛑 YouTube Reporter 서버 종료")


if __name__ == "__main__":
    # Windows에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Uvicorn 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드에서 자동 재시작
        log_level="info"
    )