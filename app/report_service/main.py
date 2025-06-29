from fastapi import FastAPI
from routers import report, user_analysis, s3  # report.py, user_analysis.py, s3.py

app = FastAPI(
    title="Report Service",
    description="Handles report upload, listing, metadata, and user analysis tracking.",
    version="1.0.0"
)

# 라우터 등록
app.include_router(report.router)
app.include_router(user_analysis.router)
app.include_router(s3.router)

# 헬스 체크
@app.get("/health")
def health_check():
    return {"status": "ok"}
