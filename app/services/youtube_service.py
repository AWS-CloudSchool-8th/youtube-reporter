# app/services/youtube_service.py
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from threading import Lock
from ..models.response import JobStatusResponse, ReportResult, JobStatus
from ..services.langgraph_service import LangGraphService
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 메모리 기반 작업 상태 저장소 (프로덕션에서는 Redis 등 사용 권장)
jobs: Dict[str, JobStatusResponse] = {}
results: Dict[str, ReportResult] = {}
jobs_lock = Lock()


class YouTubeService:
    """YouTube 영상 처리 서비스"""

    def __init__(self):
        self.langgraph_service = LangGraphService()

    def create_job(self, youtube_url: str) -> str:
        """새 작업 생성"""
        job_id = str(uuid.uuid4())

        with jobs_lock:
            jobs[job_id] = JobStatusResponse(
                job_id=job_id,
                status=JobStatus.QUEUED,
                progress=0,
                message="분석 대기 중...",
                created_at=datetime.now()
            )

        logger.info(f"📝 새 작업 생성: {job_id} - {youtube_url}")
        return job_id

    async def process_video(self, job_id: str, youtube_url: str):
        """비동기로 영상 처리"""
        try:
            # 상태 업데이트: 처리 시작
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = JobStatus.PROCESSING
                    jobs[job_id].progress = 5
                    jobs[job_id].message = "🎬 영상 분석을 시작합니다..."

            logger.info(f"🚀 작업 {job_id} 처리 시작")

            # 진행률 업데이트 함수
            async def update_progress(progress: int, message: str):
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id].progress = progress
                        jobs[job_id].message = message
                await asyncio.sleep(0.1)  # UI 업데이트를 위한 짧은 대기

            # 단계별 진행 상황 업데이트
            await update_progress(10, "📝 자막 추출 중...")
            await asyncio.sleep(1)

            await update_progress(25, "🧠 영상 내용 분석 중...")
            await asyncio.sleep(1)

            await update_progress(50, "📊 포괄적 요약 생성 중...")
            await asyncio.sleep(1)

            await update_progress(70, "🎯 시각화 기회 탐지 중...")
            await asyncio.sleep(1)

            await update_progress(85, "🎨 스마트 시각화 생성 중...")

            # LangGraph 파이프라인 실행
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.langgraph_service.analyze_youtube_video,
                youtube_url,
                job_id
            )

            await update_progress(95, "📋 최종 리포트 조합 중...")
            await asyncio.sleep(0.5)

            # 결과를 ReportResult 모델로 변환
            report_data = result.get("report_result", {})

            if report_data.get("success", False):
                # 성공적인 결과 변환
                report_result = ReportResult(
                    success=True,
                    title=report_data.get("title", "YouTube 영상 분석"),
                    summary=report_data.get("summary", ""),
                    sections=report_data.get("sections", []),
                    statistics=report_data.get("statistics", {
                        "total_sections": 0,
                        "text_sections": 0,
                        "visualizations": 0
                    }),
                    process_info=report_data.get("process_info", {
                        "youtube_url": youtube_url,
                        "caption_length": 0,
                        "summary_length": 0
                    }),
                    created_at=datetime.now()
                )

                success_message = "✅ 분석 완료!"

                # 통계 로깅
                stats = report_result.statistics
                logger.info(f"📊 작업 {job_id} 완료 - "
                            f"섹션: {stats.total_sections}개, "
                            f"텍스트: {stats.text_sections}개, "
                            f"시각화: {stats.visualizations}개")

            else:
                # 실패한 결과 처리
                error_msg = report_data.get("error", "알 수 없는 오류")
                report_result = ReportResult(
                    success=False,
                    title="분석 실패",
                    summary=f"영상 분석 중 오류가 발생했습니다: {error_msg}",
                    sections=[],
                    statistics={
                        "total_sections": 0,
                        "text_sections": 0,
                        "visualizations": 0
                    },
                    process_info={
                        "youtube_url": youtube_url,
                        "error": error_msg
                    },
                    created_at=datetime.now()
                )

                success_message = f"❌ 분석 실패: {error_msg}"

            # 결과 저장
            with jobs_lock:
                results[job_id] = report_result

                # 완료 상태 업데이트
                if job_id in jobs:
                    jobs[job_id].status = JobStatus.COMPLETED
                    jobs[job_id].progress = 100
                    jobs[job_id].message = success_message
                    jobs[job_id].completed_at = datetime.now()

            logger.info(f"✅ 작업 {job_id} 완료")

        except Exception as e:
            error_msg = f"처리 중 오류 발생: {str(e)}"
            logger.error(f"❌ 작업 {job_id} 실패: {e}")

            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].status = JobStatus.FAILED
                    jobs[job_id].progress = 0
                    jobs[job_id].message = f"❌ {error_msg}"
                    jobs[job_id].error = str(e)
                    jobs[job_id].completed_at = datetime.now()

                # 실패 시에도 기본 결과 저장
                results[job_id] = ReportResult(
                    success=False,
                    title="분석 실패",
                    summary=error_msg,
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

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        """작업 상태 조회"""
        with jobs_lock:
            if job_id not in jobs:
                raise ValueError(f"작업 {job_id}를 찾을 수 없습니다.")
            return jobs[job_id]

    def get_job_result(self, job_id: str) -> ReportResult:
        """작업 결과 조회"""
        with jobs_lock:
            if job_id not in jobs:
                raise ValueError(f"작업 {job_id}를 찾을 수 없습니다.")

            job = jobs[job_id]
            if job.status != JobStatus.COMPLETED:
                raise ValueError(f"작업 {job_id}가 완료되지 않았습니다. (상태: {job.status})")

            if job_id not in results:
                raise ValueError(f"작업 {job_id}의 결과를 찾을 수 없습니다.")

            return results[job_id]

    def list_jobs(self, limit: int = 20) -> List[JobStatusResponse]:
        """작업 목록 조회"""
        with jobs_lock:
            # 최신 작업부터 정렬
            job_list = list(jobs.values())
            job_list.sort(key=lambda x: x.created_at, reverse=True)
            return job_list[:limit]

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """오래된 작업 정리"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with jobs_lock:
            jobs_to_remove = [
                job_id for job_id, job in jobs.items()
                if job.created_at < cutoff_time
            ]

            for job_id in jobs_to_remove:
                jobs.pop(job_id, None)
                results.pop(job_id, None)
                logger.info(f"🧹 오래된 작업 정리: {job_id}")

            if jobs_to_remove:
                logger.info(f"🧹 총 {len(jobs_to_remove)}개의 오래된 작업 정리 완료")

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계 정보"""
        with jobs_lock:
            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs.values() if j.status == JobStatus.COMPLETED])
            failed_jobs = len([j for j in jobs.values() if j.status == JobStatus.FAILED])
            processing_jobs = len([j for j in jobs.values() if j.status == JobStatus.PROCESSING])

            # 성공률 계산
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "processing_jobs": processing_jobs,
                "success_rate": round(success_rate, 2),
                "pipeline_info": self.langgraph_service.get_pipeline_status()
            }