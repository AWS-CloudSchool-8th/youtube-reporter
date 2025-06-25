# app/services/langgraph_service.py
from typing import Dict, Any
from ..agents.graph_workflow import YouTubeReporterWorkflow
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LangGraphService:
    """LangGraph 워크플로우 관리 서비스"""
    
    def __init__(self):
        self.workflow = YouTubeReporterWorkflow()
        logger.info("LangGraph 서비스 초기화 완료")
    
    def process_video(self, youtube_url: str) -> Dict[str, Any]:
        """YouTube 영상 처리"""
        try:
            logger.info(f"LangGraph 워크플로우 시작: {youtube_url}")
            result = self.workflow.process(youtube_url)
            logger.info("LangGraph 워크플로우 완료")
            return result
        except Exception as e:
            logger.error(f"LangGraph 워크플로우 실패: {e}")
            raise