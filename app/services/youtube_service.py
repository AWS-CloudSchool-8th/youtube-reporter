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

    async def process_video(self, job_id: str, youtube_url: str, summary_level: str = "detailed"):
        """비동기로 영상 처리"""
        try:
            # 상태 업데이트: 처리 시작
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = "processing"
                    jobs[job_id].progress = 10
                    jobs[job_id].message = "자막 추출 중..."

            logger.info(f"작업 {job_id} 처리 시작")

            # LangGraph 워크플로우 실행
            await asyncio.sleep(1)
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].progress = 50
                    jobs[job_id].message = "AI 분석 중..."

            # 실제 처리
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.workflow.process, youtube_url, summary_level
            )

            # 결과 저장
            with jobs_lock:
                results[job_id] = ReportResult(
                    title=result.get("title", "YouTube 영상 분석"),
                    sections=result.get("sections", []),
                    created_at=datetime.now()
                )

                # 완료 상태 업데이트
                if job_id in jobs:
                    jobs[job_id].status = "completed"
                    jobs[job_id].progress = 100
                    jobs[job_id].message = "분석 완료!"
                    jobs[job_id].completed_at = datetime.now()

            logger.info(f"작업 {job_id} 완료")

        except Exception as e:
            logger.error(f"작업 {job_id} 실패: {e}")

            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = "failed"
                    jobs[job_id].progress = 0
                    jobs[job_id].message = f"처리 실패: {str(e)}"
                    jobs[job_id].error = str(e)
                    jobs[job_id].completed_at = datetime.now()

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
                raise ValueError(f"Job {job_id} is not completed")
            
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