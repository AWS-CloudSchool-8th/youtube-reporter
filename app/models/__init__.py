# app/models/__init__.py
from .request import ProcessVideoRequest
from .response import ProcessVideoResponse, JobStatus, ReportResult, ReportSection

__all__ = ["ProcessVideoRequest", "ProcessVideoResponse", "JobStatus", "ReportResult", "ReportSection"]