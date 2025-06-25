from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.s3_service import s3_service
from app.core.config import settings
import json

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/list")
async def list_reports() -> List[Dict[str, Any]]:
    """
    저장된 보고서 목록 조회
    """
    try:
        # S3에서 보고서 목록 가져오기
        objects = s3_service.list_objects(prefix="reports/", max_keys=100)
        
        reports = []
        for obj in objects:
            if not obj.get("Key", "").endswith(".json"):
                continue
                
            key = obj.get("Key", "")
            last_modified = obj.get("LastModified")
            size = obj.get("Size", 0)
            
            # S3 URL 생성
            url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            # 메타데이터 가져오기 시도
            metadata = {}
            try:
                metadata_key = key.replace("reports/", "metadata/").replace("_report.json", "_metadata.json")
                metadata_objects = s3_service.list_objects(prefix=metadata_key, max_keys=1)
                
                if metadata_objects:
                    # 메타데이터 파일이 존재하면 내용 가져오기
                    metadata_url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{metadata_key}"
                    # 여기서는 메타데이터 URL만 제공
                    metadata = {"url": metadata_url}
            except Exception as e:
                print(f"메타데이터 조회 실패: {e}")
            
            # 보고서 정보 추가
            reports.append({
                "key": key,
                "title": extract_title_from_key(key),
                "last_modified": last_modified.isoformat() if hasattr(last_modified, "isoformat") else str(last_modified),
                "size": size,
                "url": url,
                "metadata": metadata,
                "type": "YouTube"
            })
        
        # 최신순 정렬
        reports.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 목록 조회 실패: {str(e)}")

@router.get("/{report_id}")
async def get_report(report_id: str) -> Dict[str, Any]:
    """
    특정 보고서 조회
    
    - **report_id**: 보고서 ID
    """
    try:
        # S3에서 보고서 가져오기
        key = f"reports/{report_id}_report.json"
        
        # 객체 존재 여부 확인
        objects = s3_service.list_objects(prefix=key, max_keys=1)
        if not objects:
            raise HTTPException(status_code=404, detail=f"보고서를 찾을 수 없음: {report_id}")
        
        # S3 URL 생성
        url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        
        # 메타데이터 가져오기 시도
        metadata = {}
        try:
            metadata_key = f"metadata/{report_id}_metadata.json"
            metadata_objects = s3_service.list_objects(prefix=metadata_key, max_keys=1)
            
            if metadata_objects:
                # 메타데이터 URL 생성
                metadata_url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{metadata_key}"
                metadata = {"url": metadata_url}
        except Exception as e:
            print(f"메타데이터 조회 실패: {e}")
        
        return {
            "report_id": report_id,
            "url": url,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 조회 실패: {str(e)}")

def extract_title_from_key(key: str) -> str:
    """파일 키에서 제목 추출"""
    if not key:
        return "제목 없음"
    
    # 파일 이름 추출
    file_name = key.split("/")[-1]
    
    # 확장자 제거
    name_without_ext = file_name.replace(".json", "")
    
    # job_id나 UUID 제거
    clean_name = name_without_ext\
        .replace("_report", "")\
        .replace("report_", "")\
        .replace("_metadata", "")
    
    # UUID 패턴 제거 시도
    import re
    uuid_pattern = r"[0-9a-f]{8}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{12}"
    clean_name = re.sub(uuid_pattern, "", clean_name, flags=re.IGNORECASE)
    
    # 언더스코어를 공백으로 변환
    result = clean_name.replace("_", " ").strip()
    
    return result if result else "분석 보고서"
