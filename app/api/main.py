# app/api/main.py (수정된 버전)
import os
import sys
from pathlib import Path

# PyCharm에서 실행시 경로 자동 설정
if __name__ == "__main__":
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
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않음")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import json

# 올바른 서비스들 import
try:
    from services.youtube_service import YouTubeService
    from services.claude_service import ClaudeService  # 기존 서비스 사용
    from services.smart_visualization_service import SmartVisualizationService
    from models.report import Report, ReportSection, VisualizationType, VisualizationData
    from views.schemas import ProcessVideoRequest, ReportResponse, VisualizationResponse

    print("✅ 스마트 시각화 컴포넌트 import 성공")
except ImportError as e:
    print(f"❌ 컴포넌트 import 실패: {e}")
    sys.exit(1)

app = FastAPI(
    title="YouTube Reporter - Smart Visualization",
    description="영상 내용 맞춤형 스마트 시각화 API",
    version="3.0.0"
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
    claude_service = ClaudeService()  # 기존 보고서 생성용
    smart_viz_service = SmartVisualizationService()  # 스마트 시각화용
    print("✅ 스마트 시각화 서비스 인스턴스 생성 성공")
except Exception as e:
    print(f"❌ 서비스 인스턴스 생성 실패: {e}")

# 메모리 저장소
jobs: Dict[str, Dict[str, Any]] = {}
reports: Dict[str, Report] = {}


async def process_video_with_smart_visualization(job_id: str, request: ProcessVideoRequest):
    """스마트 시각화를 포함한 영상 처리"""
    try:
        print(f"🎬 [Smart Viz] 작업 {job_id} 시작")

        # 보고서 객체 생성
        report = Report(
            title="분석 중...",
            youtube_url=str(request.youtube_url),
            status="processing"
        )
        reports[report.id] = report

        jobs[job_id].update({
            "status": "processing",
            "progress": 10,
            "message": "자막 추출 중...",
            "report_id": report.id
        })

        # 1단계: 자막 추출
        print(f"📝 자막 추출 시작")
        caption = await youtube_service.extract_caption(str(request.youtube_url))

        if not caption or caption.startswith("[Error"):
            raise ValueError("자막 추출 실패")

        print(f"✅ 자막 추출 완료: {len(caption)} 글자")

        jobs[job_id].update({
            "progress": 30,
            "message": "기본 보고서 생성 중..."
        })

        # 2단계: 기본 보고서 생성 (ClaudeService 사용)
        print(f"📄 기본 보고서 생성 시작")
        basic_report = await claude_service.generate_report(caption)

        if not basic_report or basic_report.startswith("[Error"):
            raise ValueError("보고서 생성 실패")

        print(f"✅ 기본 보고서 생성 완료: {len(basic_report)} 글자")

        jobs[job_id].update({
            "progress": 60,
            "message": "스마트 시각화 분석 중..."
        })

        # 3단계: 스마트 시각화 생성
        print(f"🧠 스마트 시각화 분석 시작")
        smart_visualizations = await smart_viz_service.analyze_and_generate_visualizations(
            caption, basic_report
        )

        print(f"✅ 스마트 시각화 생성 완료: {len(smart_visualizations)}개 섹션")

        # 시각화 타입별 통계
        viz_stats = analyze_visualization_types(smart_visualizations)
        print(f"📊 시각화 통계: {viz_stats}")

        jobs[job_id].update({
            "progress": 90,
            "message": "최종 보고서 구성 중..."
        })

        # 4단계: 보고서 완성
        report.title = extract_title_from_text(basic_report)
        report.sections = create_smart_sections(smart_visualizations)
        report.status = "completed"

        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "스마트 분석 완료!",
            "completed_at": datetime.now().isoformat(),
            "report_id": report.id,
            "visualization_stats": viz_stats
        })

        print(f"🎉 스마트 시각화 작업 {job_id} 완료")

    except Exception as e:
        print(f"❌ 스마트 시각화 작업 {job_id} 실패: {e}")
        import traceback
        traceback.print_exc()  # 상세 에러 로그

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


def analyze_visualization_types(visualizations: List[Dict]) -> Dict[str, Any]:
    """생성된 시각화 타입 분석"""
    stats = {
        "total_sections": len(visualizations),
        "text_sections": 0,
        "chart_sections": 0,
        "advanced_viz": 0,
        "types": {},
        "unique_types": []
    }

    for viz in visualizations:
        viz_type = viz.get("type", "unknown")

        # 타입별 카운트
        stats["types"][viz_type] = stats["types"].get(viz_type, 0) + 1

        # 카테고리별 분류
        if viz_type in ["paragraph", "heading"]:
            stats["text_sections"] += 1
        elif viz_type in ["bar_chart", "line_chart", "pie_chart"]:
            stats["chart_sections"] += 1
        else:
            stats["advanced_viz"] += 1

    stats["unique_types"] = list(stats["types"].keys())
    return stats


def extract_title_from_text(report_text: str) -> str:
    """보고서 텍스트에서 제목 추출"""
    lines = report_text.split('\n')
    for line in lines:
        if line.startswith('제목:'):
            return line.replace('제목:', '').strip()
        elif line.startswith('#'):
            return line.replace('#', '').strip()
    return "YouTube 영상 분석 보고서"


def create_smart_sections(viz_data: List[Dict]) -> List[ReportSection]:
    """스마트 시각화 데이터를 ReportSection으로 변환"""
    sections = []

    for i, item in enumerate(viz_data):
        try:
            viz_type_str = item.get("type", "paragraph")

            # 확장된 VisualizationType enum 처리
            try:
                section_type = VisualizationType(viz_type_str)
            except ValueError:
                # 새로운 타입이면 paragraph로 처리하되, 원본 타입 정보 보존
                section_type = VisualizationType.PARAGRAPH
                print(f"⚠️ 새로운 시각화 타입: {viz_type_str}, paragraph로 처리")

            # 텍스트 섹션
            if section_type == VisualizationType.PARAGRAPH or viz_type_str in ["heading", "paragraph"]:
                section = ReportSection(
                    type=section_type,
                    title=item.get("title"),
                    content=item.get("content"),
                    position=item.get("position", i)
                )
            # 기본 차트 섹션
            elif section_type in [VisualizationType.BAR_CHART, VisualizationType.LINE_CHART,
                                  VisualizationType.PIE_CHART]:
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
            # 고급 시각화 (임시로 paragraph로 처리하되 원본 데이터 보존)
            else:
                section = ReportSection(
                    type=VisualizationType.PARAGRAPH,
                    title=item.get("title", f"고급 시각화: {viz_type_str}"),
                    content=json.dumps(item, ensure_ascii=False, indent=2),
                    position=item.get("position", i)
                )
                # 원본 시각화 타입과 데이터를 메타데이터로 저장
                section._original_type = viz_type_str
                section._original_data = item.get("data")

            sections.append(section)

        except Exception as e:
            print(f"⚠️ 섹션 {i} 생성 실패: {e}")
            # 실패한 섹션은 원본 데이터를 그대로 표시
            fallback_section = ReportSection(
                type=VisualizationType.PARAGRAPH,
                title=item.get("title", f"섹션 {i + 1}"),
                content=f"원본 데이터:\n{json.dumps(item, ensure_ascii=False, indent=2)}",
                position=i
            )
            sections.append(fallback_section)

    return sections


# API 엔드포인트들
@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "YouTube Reporter - Smart Visualization",
        "version": "3.0.0",
        "status": "running",
        "features": [
            "영상 내용 분석",
            "맞춤형 시각화 생성",
            "마인드맵, 플로우차트, 타임라인 지원",
            "실시간 처리 상태 확인"
        ],
        "services": {
            "youtube_service": "✅ 준비됨",
            "claude_service": "✅ 준비됨",
            "smart_viz_service": "✅ 준비됨"
        },
        "endpoints": {
            "docs": "/docs",
            "process": "/api/v1/process",
            "reports": "/api/v1/reports",
            "jobs": "/api/v1/jobs"
        }
    }


@app.post("/api/v1/process")
async def process_youtube_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """YouTube 영상 스마트 시각화 처리 시작"""
    try:
        job_id = str(uuid.uuid4())
        print(f"📋 새 스마트 시각화 작업 생성: {job_id}")

        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "스마트 분석 대기 중...",
            "created_at": datetime.now().isoformat(),
            "youtube_url": str(request.youtube_url),
            "options": request.options,
            "report_id": None,
            "visualization_stats": None
        }

        background_tasks.add_task(process_video_with_smart_visualization, job_id, request)

        return {
            "job_id": job_id,
            "report_id": "",
            "status": "queued",
            "message": "스마트 시각화 분석이 시작되었습니다.",
            "estimated_time": "2-3분"
        }

    except Exception as e:
        print(f"❌ 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/v1/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """작업 결과 조회 (스마트 시각화 포함)"""
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
        result = convert_report_to_response(report)

        # 시각화 통계 추가
        if job_data.get("visualization_stats"):
            result["visualization_stats"] = job_data["visualization_stats"]

        return result

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
    """Report 모델을 응답 형식으로 변환 (고급 시각화 지원)"""
    sections = []

    for section in report.sections:
        section_dict = {
            "id": section.id,
            "type": section.type.value,
            "title": section.title,
            "content": section.content,
            "position": section.position
        }

        # 기본 차트 데이터
        if section.visualization_data:
            section_dict["data"] = {
                "labels": section.visualization_data.labels,
                "datasets": section.visualization_data.datasets,
                "options": section.visualization_data.options
            }

        # 고급 시각화 메타데이터 복원
        if hasattr(section, '_original_type'):
            section_dict["type"] = section._original_type
            if hasattr(section, '_original_data'):
                section_dict["data"] = section._original_data

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

    print("🚀 YouTube Reporter - Smart Visualization API 서버 시작")
    print("🧠 지원하는 시각화 타입:")
    print("   📊 기본 차트: bar_chart, line_chart, pie_chart")
    print("   🧩 고급 시각화: mindmap, flowchart, timeline, comparison, tree, network")
    print("📖 API 문서: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )