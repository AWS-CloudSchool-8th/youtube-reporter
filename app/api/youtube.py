from fastapi import APIRouter, HTTPException
import time
import json
import logging

from ..models.request import RunRequest
from ..models.response import RunResponse
from ..services.langgraph_service import LangGraphService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/run", response_model=RunResponse)
def run_pipeline(request: RunRequest):
    start_time = time.time()
    
    try:
        print(f"\\n{'='*60}")
        print(f"🚀 YouTube 보고서 생성 시작")
        print(f"{'='*60}")
        print(f"📺 URL: {request.youtube_url}")
        print(f"🕐 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        logger.info(f"YouTube 보고서 생성 시작 - URL: {request.youtube_url}")
        
        # 1단계: 자막 추출
        print(f"\\n🎬 1단계: 자막 추출 중...")
        
        # 2단계: 보고서 생성  
        print(f"📝 2단계: 보고서 구조화 중...")
        
        # 3단계: 맥락 분석 및 태깅
        print(f"🏷️ 3단계: 시각화 태그 분석 중...")
        
        # 4단계: 시각화 생성
        print(f"🎨 4단계: 시각화 생성 중...")
        
        # 5단계: 최종 조립
        print(f"🔧 5단계: 최종 보고서 조립 중...")
        
        # 실제 파이프라인 실행
        service = LangGraphService()
        result = service.run_graph(youtube_url=request.youtube_url)
        
        elapsed_time = time.time() - start_time
        
        print(f"\\n{'='*60}")
        print(f"✅ 보고서 생성 완료!")
        print(f"{'='*60}")
        
        # 결과 분석
        final_output = result.get("final_output", {})
        
        total_paragraphs = final_output.get('total_paragraphs', 0)
        total_visuals = final_output.get('total_visuals', 0)
        sections = final_output.get('sections', [])
        assembly_stats = final_output.get('assembly_stats', {})
        
        print(f"📊 생성 통계:")
        print(f"   • 전체 섹션: {len(sections)}개")
        print(f"   • 텍스트 섹션: {total_paragraphs}개")
        print(f"   • 시각화 섹션: {total_visuals}개")
        print(f"   • 처리 시간: {elapsed_time:.1f}초")
        
        if assembly_stats:
            print(f"🔧 조립 통계:")
            print(f"   • 발견된 태그: {assembly_stats.get('total_tags_found', 0)}개")
            print(f"   • 삽입된 시각화: {assembly_stats.get('visualizations_inserted', 0)}개")
            print(f"   • 성공률: {assembly_stats.get('success_rate', 'N/A')}")
        
        # 시각화 상세 분석
        visual_sections = [s for s in sections if s.get('type') == 'visualization']
        print(f"\\n🎨 시각화 상세:")
        if visual_sections:
            for i, vs in enumerate(visual_sections, 1):
                tag_id = vs.get('tag_id', 'N/A')
                viz_type = vs.get('config', {}).get('type', 'unknown')
                title = vs.get('config', {}).get('title', 'N/A')
                print(f"   {i}. [태그 {tag_id}] {viz_type}: {title}")
        else:
            print(f"   시각화가 생성되지 않았습니다.")
        
        print(f"{'='*60}")
        
        logger.info(f"보고서 생성 완료 - 처리시간: {elapsed_time:.1f}초, 섹션: {len(sections)}개")
        
        # JSON 직렬화 가능한지 확인
        try:
            json.dumps(final_output, ensure_ascii=False, indent=2)
            print("✅ JSON 직렬화 성공")
            logger.info("응답 JSON 직렬화 성공")
        except Exception as json_err:
            print(f"❌ JSON 직렬화 실패: {json_err}")
            logger.error(f"JSON 직렬화 실패: {json_err}")
            raise HTTPException(status_code=500, detail=f"JSON 직렬화 실패: {json_err}")
        
        return {"final_output": final_output}
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        
        print(f"\\n{'='*60}")
        print(f"❌ 오류 발생!")
        print(f"{'='*60}")
        print(f"⚠️ 오류 내용: {str(e)}")
        print(f"🕐 실행 시간: {elapsed_time:.1f}초")
        print(f"{'='*60}")
        
        logger.error(f"파이프라인 실행 실패: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-simple")
def test_simple():
    """간단한 테스트용 엔드포인트"""
    print("🧪 테스트 엔드포인트 호출됨")
    return {
        "status": "success",
        "message": "API가 정상적으로 작동하고 있습니다",
        "final_output": {
            "format": "integrated_sequential",
            "sections": [
                {
                    "type": "text",
                    "content": "테스트 문단입니다. 이것은 정상적으로 작동하는 API의 테스트 응답입니다."
                },
                {
                    "type": "visualization",
                    "tag_id": "1",
                    "config": {
                        "type": "chartjs",
                        "title": "테스트 차트",
                        "config": {
                            "type": "bar",
                            "data": {
                                "labels": ["A", "B", "C"],
                                "datasets": [{
                                    "label": "테스트 데이터",
                                    "data": [10, 20, 30],
                                    "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
                                }]
                            },
                            "options": {
                                "responsive": True,
                                "plugins": {
                                    "title": {
                                        "display": True,
                                        "text": "테스트 차트"
                                    }
                                }
                            }
                        },
                        "insight": "이 테스트 차트는 A, B, C 세 항목의 데이터를 비교하여 보여줍니다."
                    },
                    "original_request": {
                        "tag_id": "1",
                        "purpose": "comparison",
                        "why_helpful": "테스트를 위한 시각화"
                    }
                }
            ],
            "total_visuals": 1,
            "total_paragraphs": 1,
            "assembly_stats": {
                "total_tags_found": 1,
                "visualizations_inserted": 1,
                "success_rate": "1/1"
            }
        }
    }