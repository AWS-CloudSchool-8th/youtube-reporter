# app/api/main.py - 단순화된 버전
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json
import asyncio

# 환경 변수 로드
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않음")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="YouTube Reporter - Simple",
    description="단순화된 YouTube 분석 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 간단한 서비스 클래스들
class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv("VIDCAP_API_KEY")
        self.api_url = "https://vidcap.xyz/api/v1/youtube/caption"

    async def extract_caption(self, youtube_url: str) -> str:
        import requests
        try:
            response = requests.get(
                self.api_url,
                params={"url": youtube_url, "locale": "ko"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            content = response.json().get("data", {}).get("content", "")
            return content if content else "자막을 찾을 수 없습니다."
        except Exception as e:
            return f"자막 추출 실패: {str(e)}"


class SimpleVisualizationService:
    def __init__(self):
        from langchain_aws import ChatBedrock
        import boto3

        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION")),
            model_id=os.getenv("AWS_BEDROCK_MODEL_ID"),
            model_kwargs={"temperature": 0.7, "max_tokens": 4096}
        )

    async def analyze_and_create_visualizations(self, caption: str) -> Dict:
        """자막을 분석해서 시각화 JSON 생성"""

        prompt = f"""
YouTube 영상 자막을 분석하여 시각적 보고서를 생성하세요.

자막:
{caption[:2000]}

다음 JSON 형식으로 응답하세요:
{{
  "title": "영상 제목",
  "sections": [
    {{
      "type": "heading",
      "title": "요약",
      "content": "영상의 핵심 내용을 2-3문장으로 요약"
    }},
    {{
      "type": "paragraph", 
      "title": "주요 내용",
      "content": "영상의 주요 내용을 상세히 설명"
    }},
    {{
      "type": "bar_chart",
      "title": "데이터 차트",
      "data": {{
        "labels": ["항목1", "항목2", "항목3"],
        "datasets": [{{
          "label": "데이터",
          "data": [10, 20, 15],
          "backgroundColor": "#6366f1"
        }}]
      }}
    }},
    {{
      "type": "mindmap",
      "title": "핵심 개념",
      "data": {{
        "center": "중심 주제",
        "branches": [
          {{
            "label": "주요 개념 1",
            "children": ["세부사항1", "세부사항2"]
          }},
          {{
            "label": "주요 개념 2", 
            "children": ["세부사항3", "세부사항4"]
          }}
        ]
      }}
    }}
  ]
}}

실제 영상 내용을 반영하여 의미있는 데이터와 시각화를 생성하세요.
"""

        try:
            from langchain_core.prompts import ChatPromptTemplate

            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 YouTube 영상을 분석하여 시각적 보고서를 생성하는 전문가입니다."),
                ("human", prompt)
            ])

            response = self.llm.invoke(chat_prompt.format_messages())

            # JSON 파싱
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()

            result = json.loads(content)
            return result

        except Exception as e:
            print(f"❌ 시각화 생성 실패: {e}")
            return self._create_fallback_result(caption)

    def _create_fallback_result(self, caption: str) -> Dict:
        """실패시 기본 결과"""
        return {
            "title": "YouTube 영상 분석",
            "sections": [
                {
                    "type": "heading",
                    "title": "분석 결과",
                    "content": "YouTube 영상 분석 결과"
                },
                {
                    "type": "paragraph",
                    "title": "영상 내용",
                    "content": caption[:500] + "..." if len(caption) > 500 else caption
                },
                {
                    "type": "bar_chart",
                    "title": "샘플 차트",
                    "data": {
                        "labels": ["항목 A", "항목 B", "항목 C"],
                        "datasets": [{
                            "label": "샘플 데이터",
                            "data": [30, 45, 25],
                            "backgroundColor": "#6366f1"
                        }]
                    }
                }
            ]
        }


# 서비스 인스턴스
youtube_service = YouTubeService()
viz_service = SimpleVisualizationService()

# 메모리 저장소
jobs: Dict[str, Dict[str, Any]] = {}
results: Dict[str, Dict[str, Any]] = {}


# API 모델
class ProcessRequest(BaseModel):
    youtube_url: HttpUrl


# 백그라운드 작업 함수
async def process_video_task(job_id: str, youtube_url: str):
    """비동기 영상 처리"""
    try:
        print(f"🎬 작업 {job_id} 시작: {youtube_url}")

        # 1. 자막 추출
        jobs[job_id].update({
            "status": "processing",
            "progress": 20,
            "message": "자막 추출 중..."
        })

        caption = await youtube_service.extract_caption(youtube_url)
        print(f"📝 자막 추출 완료: {len(caption)} 글자")

        # 2. 시각화 생성
        jobs[job_id].update({
            "progress": 60,
            "message": "시각화 생성 중..."
        })

        result = await viz_service.analyze_and_create_visualizations(caption)
        print(f"📊 시각화 생성 완료: {len(result.get('sections', []))} 섹션")

        # 3. 결과 저장
        results[job_id] = result
        jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석 완료!",
            "completed_at": datetime.now().isoformat()
        })

        print(f"✅ 작업 {job_id} 완료")

    except Exception as e:
        print(f"❌ 작업 {job_id} 실패: {e}")
        jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"처리 실패: {str(e)}",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })


# API 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "YouTube Reporter - Simple API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/v1/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """영상 처리 시작"""
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "message": "분석 대기 중...",
        "created_at": datetime.now().isoformat(),
        "youtube_url": str(request.youtube_url)
    }

    background_tasks.add_task(process_video_task, job_id, str(request.youtube_url))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "분석이 시작되었습니다."
    }


@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/v1/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """작업 결과 조회"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job is still processing")

    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job.get("error", "Job failed"))

    if job_id not in results:
        raise HTTPException(status_code=404, detail="Result not found")

    return results[job_id]


@app.get("/api/v1/jobs")
async def list_jobs():
    """모든 작업 목록"""
    return {"jobs": list(jobs.values())}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Simple YouTube Reporter API 시작")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)