# controllers/report_controller.py
from .base_controller import BaseController
from services.youtube_service import YouTubeService
from services.smart_visualization_service import ClaudeService
from models.report import Report, ReportSection, VisualizationData, VisualizationType
from views.schemas import ProcessVideoRequest, ReportResponse, VisualizationResponse
from typing import Dict, Any, List


class ReportController(BaseController):
    def __init__(self):
        super().__init__()
        self.youtube_service = YouTubeService()
        self.claude_service = ClaudeService()
        # 메모리 저장소 (나중에 DB로 교체)
        self.reports: Dict[str, Report] = {}

    async def process_video(self, request: ProcessVideoRequest) -> Dict[str, Any]:
        """YouTube 영상 처리 메인 로직"""

        # 1. 보고서 객체 생성
        report = Report(
            title="분석 중...",
            youtube_url=str(request.youtube_url),
            status="processing"
        )
        self.reports[report.id] = report

        try:
            # 2. 자막 추출
            self.logger.info(f"Extracting caption for {request.youtube_url}")
            caption = await self.youtube_service.extract_caption(str(request.youtube_url))

            if not caption or caption.startswith("[Error"):
                raise ValueError("자막 추출에 실패했습니다")

            # 3. 보고서 생성
            self.logger.info("Generating report")
            report_text = await self.claude_service.generate_report(caption)

            if not report_text or report_text.startswith("[Error"):
                raise ValueError("보고서 생성에 실패했습니다")

            # 4. 시각화 데이터 추출
            self.logger.info("Extracting visualizations")
            viz_data = await self.claude_service.extract_visualizations(report_text)

            # 5. 보고서 객체 업데이트
            report.title = self._extract_title(report_text)
            report.sections = self._create_sections(viz_data)
            report.status = "completed"

            self.logger.info(f"Report {report.id} completed successfully")
            return {
                "report_id": report.id,
                "status": "completed",
                "sections_count": len(report.sections)
            }

        except Exception as e:
            report.status = "failed"
            report.error_message = str(e)
            self.logger.error(f"Report {report.id} failed: {e}")
            raise

    def get_report(self, report_id: str) -> ReportResponse:
        """보고서 조회"""
        if report_id not in self.reports:
            raise ValueError(f"Report {report_id} not found")

        report = self.reports[report_id]

        # 섹션들을 VisualizationResponse로 변환
        sections = []
        for section in report.sections:
            viz_response = VisualizationResponse(
                id=section.id,
                type=section.type.value,
                title=section.title,
                content=section.content,
                data=section.visualization_data.__dict__ if section.visualization_data else None,
                position=section.position
            )
            sections.append(viz_response)

        return ReportResponse(
            id=report.id,
            title=report.title,
            youtube_url=report.youtube_url,
            status=report.status,
            sections=sections,
            created_at=report.created_at,
            error_message=report.error_message
        )

    def list_reports(self) -> List[ReportResponse]:
        """모든 보고서 목록 조회"""
        reports = []
        for report_id in self.reports:
            try:
                report_response = self.get_report(report_id)
                reports.append(report_response)
            except Exception as e:
                self.logger.error(f"Failed to get report {report_id}: {e}")

        return reports

    def _extract_title(self, report_text: str) -> str:
        """보고서에서 제목 추출"""
        lines = report_text.split('\n')
        for line in lines:
            if line.startswith('제목:'):
                return line.replace('제목:', '').strip()
        return "YouTube 영상 분석 보고서"

    def _create_sections(self, viz_data: List[Dict]) -> List[ReportSection]:
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
                    # 차트 데이터
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
                self.logger.error(f"Failed to create section {i}: {e}")
                # 실패한 경우 기본 paragraph로 추가
                fallback_section = ReportSection(
                    type=VisualizationType.PARAGRAPH,
                    title=item.get("title", f"섹션 {i + 1}"),
                    content=str(item.get("content", item)),
                    position=i
                )
                sections.append(fallback_section)

        return sections