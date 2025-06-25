from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import matplotlib.pyplot as plt

from app.api.youtube import router as youtube_router
from app.utils.logger import setup_logger

# 로깅 설정
setup_logger()

app = FastAPI(title="YouTube Reporter", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 라우터 등록
app.include_router(youtube_router)

@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

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

if __name__ == "__main__":
    import uvicorn
    print("YouTube 보고서 생성기를 시작합니다...")
    print("브라우저에서 http://localhost:8001 으로 접속하세요")
    print("종료하려면 Ctrl+C를 누르세요")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )