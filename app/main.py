from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any
import os
import matplotlib.pyplot as plt

from app.pipeline.youtube_graph_pipeline import run_graph

app = FastAPI()

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
        print(f"전체 섹션: {final_output.get('total_sections', 0)}")
        print(f"시각화 개수: {final_output.get('visual_count', 0)}")
        
        # 시각화 디버그 정보
        if 'sections' in final_output:
            visual_sections = [s for s in final_output['sections'] if s.get('type') == 'visual']
            print(f"시각화 섹션: {len(visual_sections)}개")
            for i, vs in enumerate(visual_sections):
                visual_data = vs.get('data', {})
                print(f"  시각화 {i+1}: {visual_data.get('title', 'N/A')} - 성공: {visual_data.get('success', False)}")
                if not visual_data.get('success', False):
                    print(f"    오류: {visual_data.get('error', 'N/A')}")
        
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

@app.post("/test-visual")
def test_visual_generation():
    """시각화 생성 테스트"""
    from app.pipeline.youtube_graph_pipeline import generate_high_quality_visual
    
    # 테스트용 요구사항
    test_requirement = {
        "type": "chart",
        "title": "테스트 차트",
        "purpose": "테스트용 시각화",
        "data_source": "예시 데이터",
        "chart_type": "bar",
        "priority_score": 10,
        "section": "테스트"
    }
    
    try:
        result = generate_high_quality_visual(test_requirement)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}