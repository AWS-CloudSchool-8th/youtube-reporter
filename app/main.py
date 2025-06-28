from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analysis, audio, document, youtube, report, auth, user_analysis, s3
from app.core.database import engine
from app.models.database_models import Base


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="YouTube, 문서 파일, 검색을 통한 통합 AI 분석 및 보고서 생성",
    version=settings.VERSION
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(auth.router)
app.include_router(user_analysis.router)
app.include_router(analysis.router)
app.include_router(audio.router)
app.include_router(document.router)
app.include_router(youtube.router)
app.include_router(report.router)
app.include_router(s3.router)

@app.get("/")
async def root():
    return {
        "message": "통합 콘텐츠 분석 API Server with YouTube Reporter",
        "version": settings.VERSION,
        "new_features": [
            "S3 자동 보고서 저장",
            "Polly 음성 변환",
            "오디오 스트리밍 재생",
            "YouTube Reporter - 스마트 시각화",
            "LangGraph 기반 에이전트 워크플로우",
            "컨텍스트 기반 시각화 자동 생성"
        ],
        "supported_inputs": [
            "YouTube URLs (단일/다중)",
            "문서 파일 (PDF, DOCX, XLSX, CSV, TXT)",
            "YouTube 검색 키워드",
            "YouTube Reporter - 포괄적 분석"
        ],
        "pipeline": [
            "1. 콘텐츠 추출",
            "2. AI 분석 및 구조화",
            "3. 스마트 시각화 생성",
            "4. S3 보고서 저장",
            "5. Polly 음성 변환",
            "6. 통합 결과 반환"
        ],
        "endpoints": {
            "youtube_search": "/youtube/search",
            "youtube_analysis": "/youtube/analyze",
            "document_analysis": "/analysis/document",
            "search_analysis": "/analysis/search",
            "youtube_status": "/youtube/jobs/{job_id}/status",
            "youtube_result": "/youtube/jobs/{job_id}/result",
            "analysis_status": "/analysis/{job_id}",
            "report_download": "/reports/{report_id}",
            "audio_generation": "/audio/generate",
            "audio_streaming": "/audio/stream/{audio_id}",
            "s3_reports": "/reports/list",
            "s3_list": "/s3/list",
            "health": "/health"
        }
    }