# app/services/youtube_service.py
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any
from ..agents.graph_workflow import YouTubeReporterWorkflow
from ..models.response_models import JobStatus, ReportResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeService:
    def __init__(self):
        self.workflow = YouTubeReporterWorkflow()
        self.jobs: Dict[str, JobStatus] = {}
        self.results: Dict[str, ReportResult] = {}

    def create_job(self, youtube_url: str) -> str:
        """새 작업 생성"""
        job_id = str(uuid.uuid4())

        self.jobs[job_id] = JobStatus(
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
            self.jobs[job_id].status = "processing"
            self.jobs[job_id].progress = 10
            self.jobs[job_id].message = "자막 추출 중..."

            logger.info(f"작업 {job_id} 처리 시작")

            # LangGraph 워크플로우 실행
            await asyncio.sleep(1)  # 상태 업데이트 시간
            self.jobs[job_id].progress = 50
            self.jobs[job_id].message = "AI 분석 중..."

            # 실제 처리 (별도 스레드에서 실행)
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.workflow.process, youtube_url
            )

            # 결과 저장
            self.results[job_id] = ReportResult(
                title=result.get("title", "YouTube 영상 분석"),
                sections=result.get("sections", []),
                created_at=datetime.now()
            )

            # 완료 상태 업데이트
            self.jobs[job_id].status = "completed"
            self.jobs[job_id].progress = 100
            self.jobs[job_id].message = "분석 완료!"
            self.jobs[job_id].completed_at = datetime.now()

            logger.info(f"작업 {job_id} 완료")

        except Exception as e:
            logger.error(f"작업 {job_id} 실패: {e}")

            self.jobs[job_id].status = "failed"
            self.jobs[job_id].progress = 0
            self.jobs[job_id].message = f"처리 실패: {str(e)}"
            self.jobs[job_id].error = str(e)
            self.jobs[job_id].completed_at = datetime.now()

    def get_job_status(self, job_id: str) -> JobStatus:
        """작업 상태 조회"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        return self.jobs[job_id]

    def get_job_result(self, job_id: str) -> ReportResult:
        """작업 결과 조회"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        if job.status != "completed":
            raise ValueError(f"Job {job_id} is not completed")

        if job_id not in self.results:
            raise ValueError(f"Result for job {job_id} not found")

        return self.results[job_id]

    def list_jobs(self) -> list:
        """모든 작업 목록"""
        return list(self.jobs.values())


