import re
import logging
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable, RunnableLambda
from langsmith.run_helpers import traceable

from ..models.state_models import ImprovedGraphState
from .caption_agent import CaptionAgent
from .report_agent import ReportAgent
from .visual_agent import VisualAgent

logger = logging.getLogger(__name__)

class ToolAgent(Runnable):
    """단순 도구를 LangGraph 노드로 변환"""
    def __init__(self, tool_func, input_key: str, output_key: str):
        self.tool_func = tool_func
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.tool_func(input_value)
        return {**state, self.output_key: result}

class LangGraphAgentNode(Runnable):
    """LangChain Runnable을 LangGraph 노드로 변환"""
    def __init__(self, runnable, input_key: str, output_key: str):
        self.runnable = runnable
        self.input_key = input_key
        self.output_key = output_key

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        input_value = state.get(self.input_key, "")
        result = self.runnable.invoke(input_value)
        return {**state, self.output_key: result}

class ContextAndTaggingAgent(Runnable):
    """맥락 분석 및 태깅 에이전트"""
    def __init__(self):
        self.visual_agent = VisualAgent()

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        
        logger.info("맥락 분석 및 태깅 시작...")
        
        result = self.visual_agent.analyze_and_tag(report_text)
        
        return {
            **state,
            "tagged_report": result.get("tagged_report", report_text),
            "visualization_requests": result.get("visualization_requests", [])
        }

class VisualizationAgent(Runnable):
    """시각화 생성 에이전트"""
    def __init__(self):
        self.visual_agent = VisualAgent()

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        visualization_requests = state.get("visualization_requests", [])
        caption_context = state.get("caption", "")
        
        generated_visualizations = self.visual_agent.generate_visualizations(
            visualization_requests, caption_context
        )
        
        return {**state, "generated_visualizations": generated_visualizations}

class FinalAssemblyAgent(Runnable):
    """최종 조립 에이전트"""
    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        tagged_report = state.get("tagged_report", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("최종 보고서 조립 시작...")
        
        # 시각화를 태그 ID별로 매핑
        viz_by_tag = {viz["tag_id"]: viz["visualization"] for viz in generated_visualizations}
        
        # 최종 섹션 생성
        final_sections = []
        current_text = ""
        
        # 태그를 찾아서 교체하면서 섹션 생성
        tag_pattern = r'\[VIZ_(\d+)\]'
        
        last_end = 0
        for match in re.finditer(tag_pattern, tagged_report):
            tag_id = match.group(1)
            
            # 태그 이전의 텍스트 추가
            text_before = tagged_report[last_end:match.start()].strip()
            if text_before:
                current_text += text_before
            
            # 누적된 텍스트가 있으면 섹션으로 추가
            if current_text.strip():
                final_sections.append({
                    "type": "text",
                    "content": current_text.strip()
                })
                current_text = ""
            
            # 해당 태그의 시각화 추가 (있다면)
            if tag_id in viz_by_tag:
                # 원본 요청에서 관련 텍스트 추출
                original_request = next(
                    (viz["original_request"] for viz in generated_visualizations if viz["tag_id"] == tag_id), 
                    {}
                )
                
                # related_content만 사용
                related_content = original_request.get("related_content", "").strip()
                
                final_sections.append({
                    "type": "visualization",
                    "tag_id": tag_id,
                    "config": viz_by_tag[tag_id],
                    "original_request": original_request,
                    "original_text": related_content
                })
                logger.info(f"태그 {tag_id} 시각화 삽입 완료 (관련 텍스트: {len(related_content)}자)")
            else:
                logger.warning(f"태그 {tag_id}에 대한 시각화를 찾을 수 없음")
            
            last_end = match.end()
        
        # 마지막 남은 텍스트 추가
        remaining_text = tagged_report[last_end:].strip()
        if remaining_text:
            current_text += remaining_text
            if current_text.strip():
                final_sections.append({
                    "type": "text",
                    "content": current_text.strip()
                })
        
        # 통계 계산
        text_count = len([s for s in final_sections if s["type"] == "text"])
        viz_count = len([s for s in final_sections if s["type"] == "visualization"])
        
        final_output = {
            "format": "integrated_sequential",
            "sections": final_sections,
            "total_paragraphs": text_count,
            "total_visuals": viz_count,
            "assembly_stats": {
                "total_tags_found": len(re.findall(tag_pattern, tagged_report)),
                "visualizations_inserted": viz_count,
                "success_rate": f"{viz_count}/{len(re.findall(tag_pattern, tagged_report))}"
            }
        }
        
        logger.info("조립 완료!")
        logger.info(f"결과: 텍스트 {text_count}개, 시각화 {viz_count}개")
        
        return {**state, "final_output": final_output}

class GraphWorkflow:
    def __init__(self):
        self.caption_agent = CaptionAgent()
        self.report_agent = ReportAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """그래프 구성"""
        builder = StateGraph(state_schema=ImprovedGraphState)
        
        # 노드 추가
        builder.add_node("caption_node", ToolAgent(
            self.caption_agent.extract_caption, "youtube_url", "caption"
        ))
        builder.add_node("report_node", LangGraphAgentNode(
            RunnableLambda(self.report_agent.generate_report), "caption", "report_text"
        ))
        builder.add_node("tagging_node", ContextAndTaggingAgent())
        builder.add_node("visualization_node", VisualizationAgent())
        builder.add_node("assembly_node", FinalAssemblyAgent())
        
        # 엣지 설정
        builder.set_entry_point("caption_node")
        builder.add_edge("caption_node", "report_node")
        builder.add_edge("report_node", "tagging_node")
        builder.add_edge("tagging_node", "visualization_node")
        builder.add_edge("visualization_node", "assembly_node")
        builder.add_edge("assembly_node", "__end__")
        
        return builder.compile()
    
    @traceable(name="improved-sequential-youtube-report")
    def run(self, youtube_url: str) -> Dict[str, Any]:
        """그래프 실행"""
        logger.info("[Improved Sequential Graph] 실행 시작")
        logger.info(f"입력 URL: {youtube_url}")
        
        try:
            result = self.graph.invoke({"youtube_url": youtube_url})
            logger.info("[Improved Sequential Graph] 실행 완료")
            
            stats = result['final_output'].get('assembly_stats', {})
            logger.info(f"최종 결과: 텍스트 {result['final_output']['total_paragraphs']}개, 시각화 {result['final_output']['total_visuals']}개")
            logger.info(f"조립 성공률: {stats.get('success_rate', 'N/A')}")
            
            return result
        except Exception as e:
            logger.error(f"[Improved Sequential Graph] 실행 실패: {e}")
            return {
                "youtube_url": youtube_url,
                "final_output": {
                    "format": "error",
                    "error": str(e),
                    "sections": [],
                    "total_paragraphs": 0,
                    "total_visuals": 0
                }
            }