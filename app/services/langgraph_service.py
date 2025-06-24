# app/services/langgraph_service.py
import uuid
import time
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph
from ..agents.caption_agent import CaptionAgent
from ..agents.summary_agent import SummaryAgent
from ..agents.visual_agent import VisualAgent
from ..agents.report_agent import ReportAgent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GraphState(TypedDict):
    """LangGraph 워크플로우 상태 정의"""
    job_id: str
    youtube_url: str
    caption: str
    summary: str
    visual_sections: List[Dict[str, Any]]
    report_result: Dict[str, Any]


class LangGraphService:
    """LangGraph 기반 YouTube 분석 파이프라인 서비스"""

    def __init__(self):
        logger.info("🔗 LangGraph 파이프라인 초기화 중...")

        # 에이전트들 초기화
        self.caption_agent = CaptionAgent()
        self.summary_agent = SummaryAgent()
        self.visual_agent = VisualAgent()
        self.report_agent = ReportAgent()

        # 그래프 구성
        self.graph = self._build_graph()

        logger.info("✅ LangGraph 파이프라인 초기화 완료")

    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        builder = StateGraph(state_schema=GraphState)

        # 노드 추가
        builder.add_node("caption_extraction", self._caption_node)
        builder.add_node("summary_generation", self._summary_node)
        builder.add_node("visualization_creation", self._visual_node)
        builder.add_node("report_compilation", self._report_node)

        # 엣지 연결 - 순차적 실행
        builder.set_entry_point("caption_extraction")
        builder.add_edge("caption_extraction", "summary_generation")
        builder.add_edge("summary_generation", "visualization_creation")
        builder.add_edge("visualization_creation", "report_compilation")
        builder.add_edge("report_compilation", "__end__")

        return builder.compile()

    def _caption_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """자막 추출 노드"""
        start_time = time.time()
        logger.info("📝 1단계: 자막 추출 시작")

        try:
            result = self.caption_agent.invoke(state)
            execution_time = round(time.time() - start_time, 2)

            caption = result.get("caption", "")
            if "[오류]" in caption:
                logger.error(f"자막 추출 실패: {caption}")
            else:
                logger.info(f"✅ 자막 추출 완료: {len(caption)}자 ({execution_time}초)")

            return result

        except Exception as e:
            logger.error(f"❌ 자막 추출 중 예외 발생: {e}")
            return {**state, "caption": f"[오류] 자막 추출 중 예외 발생: {str(e)}"}

    def _summary_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """요약 생성 노드"""
        start_time = time.time()
        logger.info("🧠 2단계: 포괄적 요약 생성 시작")

        try:
            result = self.summary_agent.invoke(state)
            execution_time = round(time.time() - start_time, 2)

            summary = result.get("summary", "")
            if "[오류]" in summary:
                logger.error(f"요약 생성 실패: {summary}")
            else:
                logger.info(f"✅ 요약 생성 완료: {len(summary)}자 ({execution_time}초)")

            return result

        except Exception as e:
            logger.error(f"❌ 요약 생성 중 예외 발생: {e}")
            return {**state, "summary": f"[오류] 요약 생성 중 예외 발생: {str(e)}"}

    def _visual_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """시각화 생성 노드"""
        start_time = time.time()
        logger.info("🎨 3단계: 스마트 시각화 생성 시작")

        try:
            result = self.visual_agent.invoke(state)
            execution_time = round(time.time() - start_time, 2)

            visual_sections = result.get("visual_sections", [])
            logger.info(f"✅ 시각화 생성 완료: {len(visual_sections)}개 ({execution_time}초)")

            return result

        except Exception as e:
            logger.error(f"❌ 시각화 생성 중 예외 발생: {e}")
            return {**state, "visual_sections": []}

    def _report_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """리포트 통합 노드"""
        start_time = time.time()
        logger.info("📋 4단계: 최종 리포트 생성 시작")

        try:
            result = self.report_agent.invoke(state)
            execution_time = round(time.time() - start_time, 2)

            report_result = result.get("report_result", {})
            success = report_result.get("success", False)

            if success:
                sections_count = len(report_result.get("sections", []))
                stats = report_result.get("statistics", {})
                logger.info(f"✅ 리포트 생성 완료: {sections_count}개 섹션 "
                            f"(텍스트: {stats.get('text_sections', 0)}, "
                            f"시각화: {stats.get('visualizations', 0)}) ({execution_time}초)")
            else:
                logger.error("❌ 리포트 생성 실패")

            return result

        except Exception as e:
            logger.error(f"❌ 리포트 생성 중 예외 발생: {e}")
            return {**state, "report_result": {"success": False, "error": str(e)}}

    async def analyze_youtube_video(self, youtube_url: str, job_id: str = None) -> Dict[str, Any]:
        """YouTube 영상 분석 실행"""
        start_time = time.time()

        # job_id 생성
        if not job_id:
            job_id = str(uuid.uuid4())

        logger.info(f"\n{'=' * 60}")
        logger.info(f"🚀 YouTube 영상 분석 시작")
        logger.info(f"📝 Job ID: {job_id}")
        logger.info(f"🎬 URL: {youtube_url}")
        logger.info(f"{'=' * 60}\n")

        # 초기 상태 설정
        initial_state = {
            "job_id": job_id,
            "youtube_url": youtube_url,
            "caption": "",
            "summary": "",
            "visual_sections": [],
            "report_result": {}
        }

        try:
            # LangGraph 파이프라인 실행
            result = self.graph.invoke(initial_state)

            # 실행 시간 계산
            total_time = round(time.time() - start_time, 2)

            # 결과 로깅
            report_result = result.get("report_result", {})
            success = report_result.get("success", False)

            if success:
                stats = report_result.get("statistics", {})
                logger.info(f"\n{'=' * 60}")
                logger.info(f"✅ 분석 완료!")
                logger.info(f"⏱️  총 소요 시간: {total_time}초")
                logger.info(f"📊 생성된 섹션: {stats.get('total_sections', 0)}개")
                logger.info(f"📝 텍스트 섹션: {stats.get('text_sections', 0)}개")
                logger.info(f"🎨 시각화: {stats.get('visualizations', 0)}개")
                logger.info(f"{'=' * 60}\n")
            else:
                logger.error(f"\n{'=' * 60}")
                logger.error(f"❌ 분석 실패!")
                logger.error(f"⏱️  소요 시간: {total_time}초")
                logger.error(f"❗ 오류: {report_result.get('error', '알 수 없는 오류')}")
                logger.error(f"{'=' * 60}\n")

            # 최종 결과에 실행 시간 추가
            if "process_info" in report_result:
                report_result["process_info"]["processing_time"] = total_time

            return result

        except Exception as e:
            total_time = round(time.time() - start_time, 2)
            error_msg = f"파이프라인 실행 중 예외 발생: {str(e)}"

            logger.error(f"\n{'=' * 60}")
            logger.error(f"❌ 파이프라인 실행 실패!")
            logger.error(f"⏱️  소요 시간: {total_time}초")
            logger.error(f"❗ 오류: {error_msg}")
            logger.error(f"{'=' * 60}\n")

            # 오류 결과 반환
            return {
                **initial_state,
                "report_result": {
                    "success": False,
                    "title": "분석 실패",
                    "summary": f"영상 분석 중 오류가 발생했습니다: {error_msg}",
                    "sections": [],
                    "statistics": {
                        "total_sections": 0,
                        "text_sections": 0,
                        "visualizations": 0
                    },
                    "process_info": {
                        "youtube_url": youtube_url,
                        "processing_time": total_time,
                        "error": error_msg
                    }
                }
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """파이프라인 상태 정보 반환"""
        return {
            "service": "LangGraph YouTube Analyzer",
            "version": "2.0.0",
            "agents": {
                "caption_agent": "CaptionAgent",
                "summary_agent": "SummaryAgent",
                "visual_agent": "VisualAgent",
                "report_agent": "ReportAgent"
            },
            "pipeline_steps": [
                "caption_extraction",
                "summary_generation",
                "visualization_creation",
                "report_compilation"
            ],
            "features": [
                "포괄적 요약 생성",
                "스마트 시각화 생성",
                "컨텍스트 기반 분석",
                "다양한 시각화 타입 지원"
            ]
        }