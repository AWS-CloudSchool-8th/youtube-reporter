from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.document import router as document_router  # 경로는 실제 위치에 맞게 조정

app = FastAPI()

# CORS 설정 (개발용: * → 운영 시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ["http://localhost:3000"]처럼 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(document_router)

@app.get("/")
async def root():
    return {"message": "Document Service is running"}
