# app/api/main.py (PyCharm 디버그 친화적 버전)
"""Pure MVC API - PyCharm 최적화"""

import os
import sys
from pathlib import Path

# PyCharm에서 실행시 경로 자동 설정
if __name__ == "__main__":
    # 현재 파일의 부모의 부모 폴더를 Python 경로에 추가
    app_root = Path(__file__).parent.parent
    if str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))
    print(f"🐍 Python 경로 추가됨: {app_root}")

# 환경 변수 로드
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드됨: {env_path}")
    else:
        print(f"⚠️  .env 파일 없음: {env_path}")
        print("💡 PyCharm Run Configuration에서 환경 변수를 직접 설정하세요")
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않음. pip install python-dotenv")

# 필수 환경 변수 확인
required_vars = ['VIDCAP_API_KEY', 'OPENAI_API_KEY', 'AWS_REGION', 'S3_BUCKET_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ 누락된 환경 변수: {missing_vars}")
    print("\n💡 PyCharm에서 환경 변수 설정 방법:")
    print("1. Run Configuration 편집")
    print("2. Environment variables 섹션에 추가:")
    for var in missing_vars:
        print(f"   {var}=your_value_here")
    print("\n또는 .env 파일을 app/.env 경로에 생성하세요")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import json

# MVC 컴포넌트들 import
try:
    from services.youtube_service import YouTubeService
    from services.claude_service import ClaudeService
    from models.report import Report, ReportSection, VisualizationType, VisualizationData
    from views.schemas import ProcessVideoRequest, ReportResponse, VisualizationResponse

    print("✅ MVC 컴포넌트 import 성공")
except ImportError as e:
    print(f"❌ MVC 컴포넌트 import 실패: {e}")
    print("💡 PyCharm에서 app 폴더를 소스 루트로 설정해보세요:")
    print("   app 폴더 우클릭 → Mark Directory as → Sources Root")
    sys.exit(1)

app = FastAPI(
    title="YouTube Reporter - Pure MVC (PyCharm)",
    description="PyCharm 환경에 최적화된 Pure MVC API",
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

# 서비스 인스턴스
try:
    youtube_service = YouTubeService()
    claude_service = ClaudeService()
    print("✅ 서비스 인스턴스 생성 성공")
except Exception as e:
    print(f"❌ 서비스 인스턴스 생성 실패: {e}")

# 작업 및 보고서 저장소 (메모리)
jobs: Dict[str, Dict[str, Any]] = {}
reports: Dict[str, Report] = {}


async def process_video_background_mvc(job_id: str, request: ProcessVideoRequest):
    """MVC 패턴으로 영상 처리 - PyCharm 디버그 포인트 설정 가능"""
    try:
        print(f"🎬 [PyCharm Debug] MVC 작업 {job_id} 시작")

        # 디버그 포인트 설정하기 좋은 위치 1
        report = Report(
            title="분석 중...",
            youtube_url=str(request.youtube_url),
            status="processing"
        )
        reports[report.id] = report

        jobs[job_id].update({
            "status": "processing",
            "progress": 20,
            "message": "자막 추출 중...",
            "report_id": report.id
        })

        # 디버그 포인트 설정하기 좋은 위치 2
        print(f"📝 [PyCharm Debug] 자막 추출 시작")
        caption = await youtube_service.extract_caption(str(request.youtube_url))

        if not caption or caption.startswith("[Error"):
            raise ValueError("자막 추출 실패")

        print(f"✅ [PyCharm Debug] 자막 추출 완료: {len(caption)} 글자")

        jobs[job_id].update({
            "progress": 50,
            "message": "보고서 생성 중..."
        })

        # 디버그 포인트 설정하기 좋은 위치 3
        print(f"📄 [PyCharm Debug] 보고서 생성 시작")
        report_text = await claude_service.generate_report(caption)

        if not report_text or report_text.startswith("[Error"):
            raise ValueError("보고서 생성 실패")

        print(f"✅ [PyCharm Debug] 보고서 생성 완료: {len(report_text)} 글자")

        jobs[job_id].update({
            "progress": 80,
            "message": "시각화 데이터 생성 중..."
        })

        # 디버그 포인트 설정하기 좋은 위치 4
        print(f"📊 [PyCharm Debug] 시각화 데이터 추출 시작")
        viz_data = await claude_service.extract_visualizations(report_text)

        print(f"✅ [PyCharm Debug] 시각화 데이터 추출 완료: {len(viz_data)}개 섹션")

        # 디버그 포인트 설정하기 좋은 위치 5
        report.title = extract_title_from_text(report_text)
        report.sections = create_sections_from_viz_data(viz_data)
        report.status = "completed"

        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석 완료!",
            "completed_at": datetime.now().isoformat(),
            "report_id": report.id
        })

        print(f"🎉 [PyCharm Debug] MVC 작업 {job_id} 완료")

    except Exception as e:
        print(f"❌ [PyCharm Debug] MVC 작업 {job_id} 실패: {e}")
        # PyCharm에서 예외 상세 정보 확인 가능

        if 'report' in locals():
            report.status = "failed"
            report.error_message = str(e)

        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"처리 실패: {str(e)}",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


def extract_title_from_text(report_text: str) -> str:
    """보고서 텍스트에서 제목 추출"""
    lines = report_text.split('\n')
    for line in lines:
        if line.startswith('제목:'):
            return line.replace('제목:', '').strip()
        elif line.startswith('#'):
            return line.replace('#', '').strip()
    return "YouTube 영상 분석 보고서"


def create_sections_from_viz_data(viz_data: List[Dict]) -> List[ReportSection]:
    """시각화 데이터를 ReportSection으로 변환"""
    sections = []

    for i, item in enumerate(viz_data):
        try:
            section_type = VisualizationType(item.get("type", "paragraph"))

            if section_type == VisualizationType.PARAGRAPH:
                section = ReportSection(
                    type=section_type,
                    title=item.get("title"),
                    content=item.get("content"),
                    position=item.get("position", i)
                )
            else:
                # 차트 데이터만 저장
                data_dict = item.get("data", {})
                viz_data_obj = VisualizationData(
                    labels=data_dict.get("labels", []),
                    datasets=data_dict.get("datasets", []),
                    options=data_dict.get("options", {})
                )
                section = ReportSection(
                    type=section_type,
                    title=item.get("title"),
                    visualization_data=viz_data_obj,
                    position=item.get("position", i)
                )

            sections.append(section)

        except Exception as e:
            print(f"⚠️ [PyCharm Debug] 섹션 {i} 생성 실패: {e}")
            fallback_section = ReportSection(
                type=VisualizationType.PARAGRAPH,
                title=item.get("title", f"섹션 {i + 1}"),
                content=str(item.get("content", item)),
                position=i
            )
            sections.append(fallback_section)

    return sections


# API 엔드포인트들
@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "YouTube Reporter - Pure MVC (PyCharm Optimized)",
        "version": "2.0.0",
        "status": "running",
        "environment": "PyCharm",
        "python_path": sys.path[:3],  # 처음 3개 경로만 표시
        "endpoints": {
            "docs": "/docs",
            "process": "/api/v1/process",
            "reports": "/api/v1/reports",
            "jobs": "/api/v1/jobs"
        }
    }


@app.post("/api/v1/process")
async def process_youtube_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """YouTube 영상 처리 시작"""
    try:
        job_id = str(uuid.uuid4())
        print(f"📋 [PyCharm Debug] 새 작업 생성: {job_id}")

        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "작업 대기 중...",
            "created_at": datetime.now().isoformat(),
            "youtube_url": str(request.youtube_url),
            "options": request.options,
            "report_id": None
        }

        background_tasks.add_task(process_video_background_mvc, job_id, request)

        return {
            "job_id": job_id,
            "report_id": "",
            "status": "queued",
            "message": "PyCharm MVC 패턴으로 작업이 시작되었습니다."
        }

    except Exception as e:
        print(f"❌ [PyCharm Debug] 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

    # 보고서 반환
    if job_data.get("report_id") and job_data["report_id"] in reports:
        report = reports[job_data["report_id"]]
        return convert_report_to_response(report)

    return {"message": "Job completed but no report available"}


@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    """보고서 상세 조회"""
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports[report_id]
    return convert_report_to_response(report)


@app.get("/api/v1/jobs")
async def list_jobs():
    """모든 작업 목록 조회"""
    return {"jobs": list(jobs.values()), "total": len(jobs)}


def convert_report_to_response(report: Report) -> Dict:
    """Report 모델을 응답 형식으로 변환"""
    sections = []
    for section in report.sections:
        section_dict = {
            "id": section.id,
            "type": section.type.value,
            "title": section.title,
            "content": section.content,
            "position": section.position
        }

        if section.visualization_data:
            section_dict["data"] = {
                "labels": section.visualization_data.labels,
                "datasets": section.visualization_data.datasets,
                "options": section.visualization_data.options
            }

        sections.append(section_dict)

    return {
        "id": report.id,
        "title": report.title,
        "youtube_url": report.youtube_url,
        "status": report.status,
        "sections": sections,
        "created_at": report.created_at.isoformat(),
        "error_message": report.error_message
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 [PyCharm] YouTube Reporter API 서버 시작")
    print("🐍 [PyCharm] 디버그 모드로 실행하면 중단점 설정 가능")
    print("📖 API 문서: http://localhost:8000/docs")

    # PyCharm에서 실행할 때는 reload=True로 설정하면 편함
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )