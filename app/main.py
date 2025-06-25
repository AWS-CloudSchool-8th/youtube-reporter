#!/usr/bin/env python3
"""
YouTube Reporter - 메인 애플리케이션
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

    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않음")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

# API 라우터 import
from .api import youtube_router
from .core.config import settings, validate_settings
from .utils.logger import get_logger

logger = get_logger(__name__)

# 환경 변수 검증
try:
    validate_settings()
except ValueError as e:
    logger.error(f"환경 변수 오류: {e}")
    sys.exit(1)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="AI 기반 YouTube 영상 분석 및 스마트 시각화 도구",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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
        "service": settings.app_name,
        "version": settings.app_version,
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
    logger.info(f"🚀 {settings.app_name} 서버 시작")
    logger.info(f"📖 API 문서: http://localhost:{settings.port}/docs")
    logger.info(f"🌐 프론트엔드 연결 대상: http://localhost:3000")
    logger.info("=" * 60)

    # 환경 변수 확인
    logger.info("환경 변수 설정 상태:")
    logger.info(f"  - VIDCAP_API_KEY: {'✅' if settings.vidcap_api_key else '❌'}")
    logger.info(f"  - AWS_REGION: {settings.aws_region}")
    logger.info(f"  - BEDROCK_MODEL_ID: {settings.bedrock_model_id}")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info(f"🛑 {settings.app_name} 서버 종료")


if __name__ == "__main__":
    # Windows에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Uvicorn 서버 실행
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )