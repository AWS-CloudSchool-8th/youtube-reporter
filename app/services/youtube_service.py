# app/services/youtube_service.py
import uuid
import asyncio
from datetime import datetime
from typing import Dict
from threading import Lock
from ..agents.graph_workflow import YouTubeReporterWorkflow
from ..models.response_models import JobStatus, ReportResult
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Thread-safe 전역 상태 저장소
jobs: Dict[str, JobStatus] = {}
results: Dict[str, ReportResult] = {}
jobs_lock = Lock()


class YouTubeService:
    """YouTube 영상 처리 서비스"""

    def __init__(self):
        self.workflow = YouTubeReporterWorkflow()

    def create_job(self, youtube_url: str) -> str:
        """새 작업 생성"""
        job_id = str(uuid.uuid4())

        with jobs_lock:
            jobs[job_id] = JobStatus(
                job_id=job_id,
                status="queued",
                progress=0,
                message="분석 대기 중...",
                created_at=datetime.now()
            )

        logger.info(f"새 작업 생성: {job_id} - {youtube_url}")
        return job_id

    async def process_video(self, job_id: str, youtube_url: str):
        """비동기로 영상 처리"""
        try:
            # 상태 업데이트: 처리 시작
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = "processing"
                    jobs[job_id].progress = 10
                    jobs[job_id].message = "🎬 자막 추출 중..."

            logger.info(f"작업 {job_id} 처리 시작")

            # 프로그레스 업데이트 함수
            async def update_progress(progress: int, message: str):
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id].progress = progress
                        jobs[job_id].message = message
                await asyncio.sleep(0.1)  # UI 업데이트를 위한 짧은 대기

            # 단계별 진행 상황 업데이트
            await update_progress(20, "📝 자막 추출 중...")
            await asyncio.sleep(1)  # 실제 처리 시뮬레이션

            await update_progress(40, "🧠 영상 내용 분석 중...")
            await asyncio.sleep(1)

            await update_progress(60, "🎯 시각화 기회 탐지 중...")
            await asyncio.sleep(1)

            await update_progress(80, "🎨 스마트 시각화 생성 중...")

            # LangGraph 워크플로우 실행
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.workflow.process, youtube_url
            )

            await update_progress(95, "📊 최종 리포트 생성 중...")
            await asyncio.sleep(0.5)

            # 결과를 ReportResult 모델로 변환
            report_result = ReportResult(
                success=result.get("success", False),
                title=result.get("title", "YouTube 영상 분석"),
                summary=result.get("summary", ""),
                sections=result.get("sections", []),
                statistics=result.get("statistics", {
                    "total_sections": 0,
                    "text_sections": 0,
                    "visualizations": 0
                }),
                process_info=result.get("process_info", {}),
                created_at=datetime.now()
            )

            # 결과 저장
            with jobs_lock:
                results[job_id] = report_result

                # 완료 상태 업데이트
                if job_id in jobs:
                    jobs[job_id].status = "completed"
                    jobs[job_id].progress = 100
                    jobs[job_id].message = "✅ 분석 완료!"
                    jobs[job_id].completed_at = datetime.now()

            logger.info(f"작업 {job_id} 완료")
            logger.info(f"  - 전체 섹션: {report_result.statistics.get('total_sections', 0)}개")
            logger.info(f"  - 시각화: {report_result.statistics.get('visualizations', 0)}개")

        except Exception as e:
            logger.error(f"작업 {job_id} 실패: {e}")

            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = "failed"
                    jobs[job_id].progress = 0
                    jobs[job_id].message = f"처리 실패: {str(e)}"
                    jobs[job_id].error = str(e)
                    jobs[job_id].completed_at = datetime.now()

                # 실패 시에도 기본 결과 저장
                results[job_id] = ReportResult(
                    success=False,
                    title="분석 실패",
                    summary=f"영상 분석 중 오류가 발생했습니다: {str(e)}",
                    sections=[],
                    statistics={
                        "total_sections": 0,
                        "text_sections": 0,
                        "visualizations": 0
                    },
                    process_info={
                        "youtube_url": youtube_url,
                        "error": str(e)
                    },
                    created_at=datetime.now()
                )

    def get_job_status(self, job_id: str) -> JobStatus:
        """작업 상태 조회"""
        with jobs_lock:
            if job_id not in jobs:
                raise ValueError(f"Job {job_id} not found")
            return jobs[job_id]

    def get_job_result(self, job_id: str) -> ReportResult:
        """작업 결과 조회"""
        with jobs_lock:
            if job_id not in jobs:
                raise ValueError(f"Job {job_id} not found")

            job = jobs[job_id]
            if job.status != "completed":
                raise ValueError(f"Job {job_id} is not completed (status: {job.status})")

            if job_id not in results:
                raise ValueError(f"Result for job {job_id} not found")

            return results[job_id]

    def list_jobs(self) -> list:
        """모든 작업 목록"""
        with jobs_lock:
            return list(jobs.values())

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """오래된 작업 정리"""
        current_time = datetime.now()
        with jobs_lock:
            jobs_to_remove = [
                job_id for job_id, job in jobs.items()
                if (current_time - job.created_at).total_seconds() / 3600 > max_age_hours
            ]

            for job_id in jobs_to_remove:
                jobs.pop(job_id, None)
                results.pop(job_id, None)
                logger.info(f"오래된 작업 정리: {job_id}")