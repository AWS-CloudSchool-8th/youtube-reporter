from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

# ✅ 함수(run_graph)만 정확히 import해야 합니다
from app.pipeline.youtube_graph_pipeline import run_graph

app = FastAPI()

class RunRequest(BaseModel):
    youtube_url: str

class RunResponse(BaseModel):
    final_output: Any

@app.post("/run", response_model=RunResponse)
def run_pipeline(request: RunRequest):
    try:
        # ✅ 함수 호출로 수정!!
        result = run_graph(youtube_url=request.youtube_url)
        return {"final_output": result.get("final_output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        # test tag hihi
       
    