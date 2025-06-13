# main.py

import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional

from app.fsm.fsm_graph import run_graph

# ----------- CLI 실행용 코드 -----------
def cli_runner():
    test_url = input("▶️ YouTube URL을 입력하세요: ").strip()
    state = {"youtube_url": test_url}
    result = run_graph(state)
    print("\n📝 최종 결과:")
    print(result["final_output"])


# ----------- FastAPI 서버 정의 -----------
app = FastAPI(title="Agentic AI FSM API", description="LangGraph 기반 FSM 실행 API")

class YouTubeRequest(BaseModel):
    youtube_url: str

@app.post("/run")
def run_fsm(request: YouTubeRequest):
    state = {"youtube_url": request.youtube_url}
    result = run_graph(state)
    return {"output": result.get("final_output", "No result")}


# ----------- entry point 선택 -----------
if __name__ == "__main__":
    import sys
    if "--api" in sys.argv:
        print("🚀 FastAPI 서버를 실행합니다...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("🧪 CLI 테스트 모드 실행")
        cli_runner()