from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.report import ReportListResponse
from app.services.report_service import report_service

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/list", response_model=ReportListResponse)
async def list_reports(
    prefix: str = Query("reports/", description="리포트 경로 접두사"),
    max_keys: int = Query(100, description="최대 리포트 수"),
    continuation_token: Optional[str] = Query(None, description="다음 페이지 토큰")
) -> ReportListResponse:
    """
    S3에 저장된 리포트 목록을 조회합니다.
    
    - **prefix**: 리포트 경로 접두사 (기본값: reports/)
    - **max_keys**: 최대 리포트 수 (기본값: 100)
    - **continuation_token**: 다음 페이지 토큰
    """
    try:
        return await report_service.list_reports(
            prefix=prefix,
            max_keys=max_keys,
            continuation_token=continuation_token
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}")
async def get_report(report_id: str):
    """
    리포트 다운로드 URL을 생성합니다.
    
    - **report_id**: 리포트 ID
    """
    try:
        return await report_service.get_report(report_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 