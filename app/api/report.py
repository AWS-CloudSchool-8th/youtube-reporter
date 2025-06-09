from fastapi import APIRouter, Query
from app.services.report_service import generate_report_from_url
from app.models.report import ReportResponse

router = APIRouter()

@router.get("/", response_model=ReportResponse)
def get_report(youtube_url: str = Query(...)):
    return generate_report_from_url(youtube_url)