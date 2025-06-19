# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers import youtube_router
from .utils import Config, get_logger

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    # 환경 변수 검증
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"환경 설정 오류: {e}")
        raise
    
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
    
    # 라우터 등록
    app.include_router(youtube_router)
    
    # 루트 엔드포인트
    @app.get("/")
    async def root():
        return {
            "service": "YouTube Reporter",
            "status": "running",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    logger.info("YouTube Reporter API 앱 생성 완료")
    return app

