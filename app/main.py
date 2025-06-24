# app/main.py - Exception Handler 추가된 버전
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from .core.config import settings
from .api.youtube import router as youtube_router
from .models.response import ErrorResponse
from .utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("=" * 60)
    logger.info("🚀 YouTube Reporter 서버 시작")
    logger.info(f"📖 API 문서: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🌐 프론트엔드: http://{settings.host}:{settings.port}")
    logger.info("=" * 60)

    # 환경 변수 확인
    logger.info("환경 변수 설정 상태:")
    logger.info(f"  - VIDCAP_API_KEY: {'✅' if settings.vidcap_api_key else '❌'}")
    logger.info(f"  - AWS_REGION: {settings.aws_region}")
    logger.info(f"  - BEDROCK_MODEL_ID: {settings.bedrock_model_id}")
    logger.info(f"  - S3_BUCKET_NAME: {'✅' if settings.s3_bucket_name else '❌ (선택적)'}")
    logger.info(f"  - OPENAI_API_KEY: {'✅' if settings.openai_api_key else '❌ (선택적)'}")

    # 애플리케이션 상태 체크
    await perform_startup_checks()

    yield

    # 종료 시
    logger.info("🛑 YouTube Reporter 서버 종료")
    await perform_shutdown_cleanup()


async def perform_startup_checks():
    """시작 시 상태 체크"""
    try:
        # AWS 연결 확인
        if settings.aws_region:
            logger.info("🔍 AWS 연결 상태 확인 중...")
            # TODO: AWS 연결 상태 확인 로직

        # VidCap API 상태 확인
        if settings.vidcap_api_key:
            logger.info("🔍 VidCap API 상태 확인 중...")
            # TODO: API 상태 확인 로직

        logger.info("✅ 모든 시작 검사 완료")

    except Exception as e:
        logger.warning(f"⚠️ 시작 검사 중 일부 실패: {e}")


async def perform_shutdown_cleanup():
    """종료 시 정리 작업"""
    try:
        logger.info("🧹 종료 정리 작업 시작...")
        # TODO: 진행 중인 작업 정리
        # TODO: 임시 파일 정리
        # TODO: 연결 종료
        logger.info("✅ 종료 정리 완료")
    except Exception as e:
        logger.error(f"❌ 종료 정리 중 오류: {e}")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""

    app = FastAPI(
        title=settings.app_name,
        description="AI 기반 YouTube 영상 분석 및 스마트 시각화 도구",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=settings.debug
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================
    # Exception Handlers (앱 레벨에서 추가)
    # ========================================

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP 예외 처리"""
        logger.warning(f"HTTP 예외 발생: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": str(exc.status_code),
                "timestamp": datetime.now().isoformat()
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """값 오류 처리"""
        logger.warning(f"값 오류: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "400",
                "timestamp": datetime.now().isoformat()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """일반 예외 처리"""
        logger.error(f"❌ 예상치 못한 오류: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "내부 서버 오류가 발생했습니다.",
                "error_code": "500",
                "timestamp": datetime.now().isoformat()
            }
        )

    # 라우터 등록
    app.include_router(youtube_router)

    # 정적 파일 서빙 (프론트엔드)
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        logger.info(f"📁 정적 파일 경로 설정: {frontend_path}")

    # 루트 경로
    @app.get("/", include_in_schema=False)
    async def root():
        """루트 경로 - 프론트엔드 또는 API 문서로 리다이렉트"""
        # 프론트엔드가 있으면 프론트엔드로, 없으면 API 문서로
        if frontend_path.exists() and (frontend_path / "index.html").exists():
            return RedirectResponse(url="/static/index.html")
        else:
            return RedirectResponse(url="/docs")

    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "debug": settings.debug,
                "aws_region": settings.aws_region,
                "features_enabled": {
                    "vidcap_api": bool(settings.vidcap_api_key),
                    "aws_bedrock": bool(settings.aws_region and settings.bedrock_model_id),
                    "s3_storage": bool(settings.s3_bucket_name),
                    "openai_integration": bool(settings.openai_api_key),
                    "langchain_tracing": settings.langchain_tracing_v2
                }
            },
            "capabilities": [
                "YouTube 자막 추출",
                "포괄적 요약 생성",
                "스마트 시각화 생성",
                "컨텍스트 기반 분석",
                "다양한 시각화 타입 지원"
            ],
            "limits": {
                "max_concurrent_jobs": settings.max_concurrent_jobs,
                "job_timeout": settings.job_timeout
            }
        }

    @app.get("/ping")
    async def ping():
        """간단한 핑 엔드포인트"""
        return {"message": "pong", "timestamp": datetime.now().isoformat()}

    return app


# FastAPI 애플리케이션 인스턴스
app = create_app()

if __name__ == "__main__":
    import uvicorn
    import sys

    # Windows에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 서버 실행
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug and settings.auto_reload,
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    )