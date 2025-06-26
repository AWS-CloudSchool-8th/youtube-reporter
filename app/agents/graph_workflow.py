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


SMART_FINAL_ASSEMBLY_PROMPT = """
당신은 보고서와 시각화를 자연스럽게 조합하는 전문가입니다.

## 임무:
원본 보고서를 적절한 섹션으로 나누고, 각 시각화를 가장 어울리는 위치에 배치하세요.

## 원본 보고서:
{report_text}

## 생성된 시각화 목록:
{visualizations_summary}

## 배치 원칙:
1. **텍스트 유사성**: 시각화의 related_content와 가장 유사한 텍스트 부분 찾기
2. **논리적 흐름**: 독자가 자연스럽게 이해할 수 있는 순서
3. **섹션 완결성**: 각 섹션이 독립적으로도 이해 가능하도록

## 작업 방법:
1. 원본 보고서를 논리적 섹션으로 분할 (제목, 소제목, 주요 문단 기준)
2. 각 시각화의 related_content와 매칭되는 섹션 식별
3. 해당 섹션 직후에 시각화 배치
4. 전체적인 읽기 흐름 최적화

## 출력 형식:
```json
{{
  "sections": [
    {{
      "type": "text",
      "content": "첫 번째 섹션의 완전한 텍스트 내용",
      "section_info": "섹션 설명 (선택사항)"
    }},
    {{
      "type": "visualization",
      "viz_index": 0,
      "placement_reason": "이 위치에 배치한 이유",
      "content_match_score": "높음|중간|낮음"
    }},
    {{
      "type": "text", 
      "content": "두 번째 섹션의 완전한 텍스트 내용"
    }}
  ],
  "assembly_summary": {{
    "total_text_sections": 숫자,
    "total_visualizations": 숫자,
    "matching_method": "어떤 방식으로 매칭했는지"
  }}
}}
```

## 중요사항:
- **원본 보고서의 모든 텍스트를 반드시 포함**하세요
- 텍스트를 요약하거나 생략하지 마세요
- 각 시각화는 정확히 한 번만 배치하세요

JSON만 출력하세요.
"""


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
    def __init__(self):
        # 🔧 수정 2: LLM 초기화 추가 (최신 브랜치와 동일하게)
        from .report_agent import ReportAgent
        self.report_agent = ReportAgent()
        self.llm = self.report_agent.llm  # ReportAgent의 LLM 재사용

    def invoke(self, state: Dict[str, Any], config: Optional[Any] = None) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("최종 보고서 조립 시작...")
        
        if not generated_visualizations:
            logger.info("⚠️ 시각화가 없어서 텍스트만 반환")
            return {
                **state,
                "final_output": {
                    "format": "text_only",
                    "sections": [{"type": "text", "content": report_text}],
                    "total_paragraphs": 1,
                    "total_visuals": 0
                }
            }
        
        # 시각화 요약 정보 생성
        viz_summary = []
        for i, viz in enumerate(generated_visualizations):
            original_req = viz.get("original_request", {})
            viz_config = viz.get("visualization", {})
            
            summary = {
                "index": i,
                "title": viz_config.get("title", f"시각화 {i+1}"),
                "purpose": original_req.get("purpose", ""),
                "description": original_req.get("content_description", ""),
                "related_content_preview": original_req.get("related_content", "")[:150] + "..."
            }
            viz_summary.append(summary)
        
        try:
            prompt = SMART_FINAL_ASSEMBLY_PROMPT.format(
                report_text=report_text,
                visualizations_summary=json.dumps(viz_summary, indent=2, ensure_ascii=False)
            )
            
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = content[start_idx:end_idx+1]
                result = json.loads(json_part)
                
                sections = result.get("sections", [])
                assembly_summary = result.get("assembly_summary", {})
                
                # 시각화 정보 보강
                enhanced_sections = []
                for section in sections:
                    if section.get("type") == "visualization":
                        viz_index = section.get("viz_index", 0)
                        if 0 <= viz_index < len(generated_visualizations):
                            viz_data = generated_visualizations[viz_index]
                            enhanced_sections.append({
                                **section,
                                "tag_id": f"viz_{viz_index + 1}",
                                "config": viz_data["visualization"],
                                "original_request": viz_data["original_request"]
                            })
                        else:
                            logger.warning(f"⚠️ 잘못된 시각화 인덱스: {viz_index}")
                    else:
                        enhanced_sections.append(section)
                
                # 통계 계산
                text_count = len([s for s in enhanced_sections if s["type"] == "text"])
                viz_count = len([s for s in enhanced_sections if s["type"] == "visualization"])
                
                final_output = {
                    "format": "smart_assembly",
                    "sections": enhanced_sections,
                    "total_paragraphs": text_count,
                    "total_visuals": viz_count,
                    "assembly_stats": assembly_summary,
                    "assembly_method": "content_similarity_matching"
                }
                
                logger.info(f"🔧 스마트 조립 완료!")
                logger.info(f"📊 결과: 텍스트 {text_count}개, 시각화 {viz_count}개")
                
                return {**state, "final_output": final_output}
            else:
                logger.error("JSON 파싱 실패, 폴백 모드로 전환")
                return self._fallback_simple_assembly(state)
                
        except Exception as e:
            logger.error(f"스마트 조립 실패: {e}, 폴백 모드로 전환")
            return self._fallback_simple_assembly(state)
    
    def _fallback_simple_assembly(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """폴백: 기존 방식과 유사한 단순 조립"""
        report_text = state.get("report_text", "")
        generated_visualizations = state.get("generated_visualizations", [])
        
        logger.info("🔄 폴백: 단순 조립 모드")
        
        # 텍스트를 문단별로 분할
        paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]
        
        sections = []
        
        # 첫 번째 절반의 텍스트
        mid_point = len(paragraphs) // 2
        if mid_point > 0:
            first_half = '\n\n'.join(paragraphs[:mid_point])
            sections.append({"type": "text", "content": first_half})
        
        # 시각화들 삽입
        for i, viz in enumerate(generated_visualizations):
            sections.append({
                "type": "visualization",
                "tag_id": f"viz_{i + 1}",
                "viz_index": i,
                "config": viz["visualization"],
                "original_request": viz["original_request"],
                "placement_reason": "폴백 모드 - 중간 위치 배치"
            })
        
        # 나머지 텍스트
        if mid_point < len(paragraphs):
            second_half = '\n\n'.join(paragraphs[mid_point:])
            sections.append({"type": "text", "content": second_half})
        
        return {
            **state,
            "final_output": {
                "format": "fallback_simple",
                "sections": sections,
                "total_paragraphs": 2 if len(paragraphs) > 1 else 1,
                "total_visuals": len(generated_visualizations),
                "assembly_method": "fallback_paragraph_split"
            }
        }

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
            logger.info(f"조립 성공률: {stats.get('assembly_method', 'N/A')}")
            
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