from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import os
import matplotlib.pyplot as plt
import json

from app.pipeline.youtube_graph_pipeline import run_graph

app = FastAPI()

# CORS 설정 추가 (프론트엔드 연결을 위해 필수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 실제 배포시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (프론트엔드)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

class RunRequest(BaseModel):
    youtube_url: str

class RunResponse(BaseModel):
    final_output: Any

@app.post("/run", response_model=RunResponse)
def run_pipeline(request: RunRequest):
    try:
        print(f"\n=== YouTube 보고서 생성 시작 ===")
        print(f"URL: {request.youtube_url}")
        
        result = run_graph(youtube_url=request.youtube_url)
        
        print(f"\n=== 결과 요약 ===")
        final_output = result.get("final_output", {})
        
        # 수정된 디버그 정보 (파이프라인 출력에 맞춤)
        total_paragraphs = final_output.get('total_paragraphs', 0)
        total_visuals = final_output.get('total_visuals', 0)
        sections = final_output.get('sections', [])
        
        print(f"전체 섹션: {len(sections)}")
        print(f"문단 개수: {total_paragraphs}")
        print(f"시각화 개수: {total_visuals}")
        
        # 시각화 디버그 정보 (새로운 구조에 맞춤)
        visual_sections = [s for s in sections if s.get('type') in ['chart', 'diagram', 'table', 'mindmap']]
        print(f"시각화 섹션: {len(visual_sections)}개")
        
        for i, vs in enumerate(visual_sections):
            section_name = vs.get('section', 'N/A')
            success = vs.get('success', False)
            viz_type = vs.get('type', 'unknown')
            print(f"  시각화 {i+1}: [{viz_type}] {section_name} - 성공: {success}")
            if not success:
                print(f"    오류: {vs.get('error', 'N/A')}")
        
        # JSON 직렬화 가능한지 확인
        try:
            json.dumps(final_output, ensure_ascii=False, indent=2)
            print("✅ JSON 직렬화 성공")
        except Exception as json_err:
            print(f"❌ JSON 직렬화 실패: {json_err}")
        
        return {"final_output": final_output}
        
    except Exception as e:
        print(f"\n=== 오류 발생 ===")
        print(f"오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug")
def debug_info():
    """디버그 정보 확인용 엔드포인트"""
    import sys
    return {
        "python_version": sys.version,
        "environment_variables": {
            "VIDCAP_API_KEY": "설정됨" if os.getenv("VIDCAP_API_KEY") else "없음",
            "AWS_REGION": os.getenv("AWS_REGION", "없음"),
            "S3_BUCKET_NAME": "설정됨" if os.getenv("S3_BUCKET_NAME") else "없음",
            "BEDROCK_MODEL_ID": os.getenv("BEDROCK_MODEL_ID", "없음")
        },
        "current_directory": os.getcwd(),
        "font_info": plt.rcParams.get('font.family', 'Unknown')
    }

@app.post("/test-simple")
def test_simple():
    """간단한 테스트용 엔드포인트"""
    return {
        "status": "success",
        "message": "API가 정상적으로 작동하고 있습니다",
        "final_output": {
            "format": "client_rendering",
            "sections": [
                {
                    "type": "paragraph",
                    "content": "테스트 문단입니다."
                },
                {
                    "type": "chart",
                    "library": "chartjs",
                    "section": "테스트 차트",
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
                    "success": True
                }
            ],
            "total_visuals": 1,
            "total_paragraphs": 1
        }
    }

@app.post("/test-youtube")
def test_youtube_pipeline():
    """YouTube 파이프라인 간단 테스트"""
    test_url = "https://www.youtube.com/watch?v=LXJhA3VWXFA"
    
    try:
        # 자막 추출만 테스트
        from app.pipeline.youtube_graph_pipeline import extract_youtube_caption_tool
        caption = extract_youtube_caption_tool(test_url)
        
        if caption.startswith("[자막 추출 실패"):
            return {"error": "자막 추출 실패", "details": caption}
        
        return {
            "status": "success",
            "caption_length": len(caption),
            "caption_preview": caption[:200] + "..." if len(caption) > 200 else caption
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/test-visual")
def test_visual_generation():
    """시각화 생성 테스트"""
    try:
        from app.pipeline.youtube_graph_pipeline import generate_visualization_data
        
        # 테스트용 요구사항
        test_requirement = {
            "section": "테스트 섹션",
            "content": "김치 300g, 돼지고기 200g, 두부 1모를 사용합니다",
            "visualization_type": "chart",
            "library": "chartjs",
            "necessity_score": 8,
            "reasoning": "재료 비교를 위한 차트"
        }
        
        result = generate_visualization_data(test_requirement)
        return {"result": result}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}