from fastapi import FastAPI
from routers import document
import sys
import os

# shared-lib 경로를 PYTHONPATH 외에도 수동으로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared_lib")))

app = FastAPI(
    title="Document Analysis Service",
    description="Supports analysis of document files such as PDF, DOCX, XLSX, CSV, TXT.",
    version="1.0.0"
)

# ? CORS 허용
origins = [
    "http://34.228.65.221:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

for route in app.routes:
    print(f"? {route.path}")
    
# 라우터 등록
app.include_router(document.router)

# 헬스체크 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "ok"}
